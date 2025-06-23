#!/usr/bin/env python3
"""
スキーマ推論精度の検証テスト
"""

import requests
import json
import io
import pandas as pd

BASE_URL = "http://localhost:8000"

# 様々なテストケース
TEST_CASES = [
    {
        "name": "標準的な経費精算フォーマット",
        "data": {
            "申請日": ["2024/01/15", "2024/01/16", "2024/01/17"],
            "支払金額": [12500, 3500, 8000],
            "申請者氏名": ["田中太郎", "佐藤花子", "山田次郎"],
            "経費種別": ["交通費", "食事代", "宿泊費"],
            "備考": ["新幹線代", "会議弁当", "ホテル代"]
        },
        "expected": {
            "date_column": "申請日",
            "amount_column": "支払金額", 
            "person_column": "申請者氏名",
            "category_column": "経費種別"
        }
    },
    {
        "name": "英語ヘッダー",
        "data": {
            "Date": ["2024-01-15", "2024-01-16", "2024-01-17"],
            "Amount": [12500, 3500, 8000],
            "Employee": ["Tanaka Taro", "Sato Hanako", "Yamada Jiro"],
            "Category": ["Transportation", "Meal", "Accommodation"],
            "Note": ["Train fare", "Meeting lunch", "Hotel"]
        },
        "expected": {
            "date_column": "Date",
            "amount_column": "Amount",
            "person_column": "Employee", 
            "category_column": "Category"
        }
    },
    {
        "name": "曖昧なヘッダー（推論が困難）",
        "data": {
            "項目A": ["2024/01/15", "2024/01/16", "2024/01/17"],
            "項目B": [12500, 3500, 8000],
            "項目C": ["田中", "佐藤", "山田"],
            "項目D": ["A", "B", "C"],
            "項目E": ["備考1", "備考2", "備考3"]
        },
        "expected": {
            "date_column": "項目A",  # 日付データから推論可能
            "amount_column": "項目B",  # 数値データから推論可能
            "person_column": "項目C",  # 人名データから推論可能
            "category_column": "項目D"  # 困難だが選択肢から推論
        }
    },
    {
        "name": "部分的に欠損したパターン",
        "data": {
            "日付": ["2024/01/15", "2024/01/16", "2024/01/17"],
            "金額": [12500, 3500, 8000],
            "その他": ["情報1", "情報2", "情報3"],
            "補足": ["メモ1", "メモ2", "メモ3"]
        },
        "expected": {
            "date_column": "日付",
            "amount_column": "金額",
            "person_column": None,  # 該当なし
            "category_column": None  # 該当なし
        }
    }
]

def create_excel_from_data(data_dict):
    """辞書データからExcelファイルを作成"""
    df = pd.DataFrame(data_dict)
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    return excel_buffer.getvalue()

def run_full_flow(excel_data, case_name):
    """完全なフローを実行してスキーマ推論結果を取得"""
    
    # 1. Excel解析
    files = {
        'file': (f'{case_name}.xlsx', excel_data, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    
    response = requests.post(f"{BASE_URL}/api/parse-excel-sheets", files=files, timeout=30)
    if response.status_code != 200:
        return None, f"Excel解析失敗: {response.status_code}"
    
    parse_result = response.json()
    session_id = parse_result["session_id"]
    sheet_name = parse_result["data"]["sheets"][0]["name"]
    
    # 2. 表検出
    response = requests.post(f"{BASE_URL}/api/excel-sheet-tables/{session_id}/{sheet_name}", timeout=30)
    if response.status_code != 200:
        return None, f"表検出失敗: {response.status_code}"
    
    table_result = response.json()
    table_id = table_result["data"]["tables"][0]["table_id"]
    
    # 3. 表選択
    response = requests.post(f"{BASE_URL}/api/select-table/{session_id}/{table_id}", timeout=30)
    if response.status_code != 200:
        return None, f"表選択失敗: {response.status_code}"
    
    select_result = response.json()
    headers = select_result["data"]["headers"]
    sample_records = select_result["data"]["sample_records"][:3]
    
    # 4. スキーマ推論
    sample_data = []
    for record in sample_records:
        row = [record.get(header, "") for header in headers]
        sample_data.append(row)
    
    inference_request = {
        "session_id": session_id,
        "headers": headers,
        "sample_data": sample_data
    }
    
    response = requests.post(f"{BASE_URL}/api/infer-schema", json=inference_request, 
                           headers={"Content-Type": "application/json"}, timeout=30)
    
    if response.status_code != 200:
        return None, f"スキーマ推論失敗: {response.status_code}"
    
    return response.json(), None

def evaluate_inference_result(result, expected):
    """推論結果を評価"""
    mappings = result["data"]["inference_result"]["mappings"]
    score = 0
    total = 0
    details = {}
    
    for column_type, expected_column in expected.items():
        total += 1
        mapping = mappings.get(column_type)
        
        if expected_column is None:
            # 該当なしが期待される場合
            if mapping is None:
                score += 1
                details[column_type] = "✓ 正しく「該当なし」と判定"
            else:
                details[column_type] = f"✗ 期待: なし, 実際: {mapping.get('column_name')}"
        else:
            # 特定の列が期待される場合
            if mapping and mapping.get('column_name') == expected_column:
                score += 1
                confidence = mapping.get('confidence', 0)
                details[column_type] = f"✓ 正解 (信頼度: {confidence}%)"
            else:
                actual = mapping.get('column_name') if mapping else None
                details[column_type] = f"✗ 期待: {expected_column}, 実際: {actual}"
    
    accuracy = (score / total) * 100 if total > 0 else 0
    overall_confidence = result["data"]["inference_result"].get("overall_confidence", 0)
    
    return accuracy, overall_confidence, details

def test_inference_accuracy():
    """推論精度テストを実行"""
    
    print("=== スキーマ推論精度検証テスト ===\n")
    
    total_accuracy = 0
    total_confidence = 0
    test_count = 0
    
    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"テストケース {i}: {test_case['name']}")
        print("-" * 50)
        
        # Excelファイル作成
        excel_data = create_excel_from_data(test_case['data'])
        
        # フロー実行
        result, error = run_full_flow(excel_data, test_case['name'])
        
        if error:
            print(f"✗ エラー: {error}")
            continue
        
        # 評価
        accuracy, confidence, details = evaluate_inference_result(result, test_case['expected'])
        
        print(f"推論精度: {accuracy:.1f}%")
        print(f"全体信頼度: {confidence}%")
        print("\n詳細結果:")
        for column_type, detail in details.items():
            print(f"  {column_type}: {detail}")
        
        print()
        
        total_accuracy += accuracy
        total_confidence += confidence
        test_count += 1
    
    if test_count > 0:
        avg_accuracy = total_accuracy / test_count
        avg_confidence = total_confidence / test_count
        
        print("=" * 60)
        print("🎯 総合評価")
        print(f"平均推論精度: {avg_accuracy:.1f}%")
        print(f"平均信頼度: {avg_confidence:.1f}%")
        print(f"テスト実行数: {test_count}/{len(TEST_CASES)}")
        
        if avg_accuracy >= 90:
            print("✅ 優秀: 推論精度が非常に高いです")
        elif avg_accuracy >= 75:
            print("✅ 良好: 推論精度が良好です")
        elif avg_accuracy >= 50:
            print("⚠️  改善余地: 推論精度の向上が必要です")
        else:
            print("❌ 要改善: 推論精度が低すぎます")

if __name__ == "__main__":
    test_inference_accuracy()