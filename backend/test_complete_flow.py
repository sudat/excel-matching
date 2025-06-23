#!/usr/bin/env python3
"""
完全なExcel解析フローのテスト（セッション作成から推論まで）
"""

import requests
import json
import io
import pandas as pd

BASE_URL = "http://localhost:8000"

def create_test_excel():
    """テスト用のExcelファイルを作成"""
    
    # テストデータ
    data = {
        "日付": ["2024/01/15", "2024/01/16", "2024/01/17", "2024/01/18"],
        "金額": [12500, 3500, 8000, 2500],
        "申請者": ["田中太郎", "佐藤花子", "山田次郎", "鈴木一郎"],
        "費目": ["交通費", "食事代", "宿泊費", "文具代"],
        "摘要": ["出張電車代", "会議弁当", "宿泊代", "ボールペン"]
    }
    
    df = pd.DataFrame(data)
    
    # BytesIOを使ってExcelファイルをメモリ上に作成
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False, engine='openpyxl')
    excel_buffer.seek(0)
    
    return excel_buffer.getvalue()

def test_complete_excel_flow():
    """完全なExcel解析フローをテスト"""
    
    print("=== 完全なExcel解析フローテスト ===")
    
    # 1. Excelファイル作成
    print("1. テスト用Excelファイルを作成...")
    excel_data = create_test_excel()
    
    # 2. Excel解析（parse-excel-sheets）
    print("2. Excel解析を実行...")
    
    files = {
        'file': ('test_data.xlsx', excel_data, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    
    response = requests.post(
        f"{BASE_URL}/api/parse-excel-sheets",
        files=files,
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"✗ Excel解析失敗: {response.status_code}")
        print(f"エラー: {response.text}")
        return False
    
    parse_result = response.json()
    session_id = parse_result["session_id"]
    sheets = parse_result["data"]["sheets"]
    
    print(f"✓ Excel解析成功、セッションID: {session_id}")
    print(f"  シート数: {len(sheets)}")
    
    # 3. 表検出（最初のシートを使用）
    sheet_name = sheets[0]["name"]
    print(f"3. シート'{sheet_name}'の表検出を実行...")
    
    response = requests.post(
        f"{BASE_URL}/api/excel-sheet-tables/{session_id}/{sheet_name}",
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"✗ 表検出失敗: {response.status_code}")
        print(f"エラー: {response.text}")
        return False
    
    table_result = response.json()
    tables = table_result["data"]["tables"]
    
    print(f"✓ 表検出成功、検出表数: {len(tables)}")
    
    # 4. 表選択（最初の表を使用）
    table_id = tables[0]["table_id"]
    print(f"4. 表'{table_id}'を選択...")
    
    response = requests.post(
        f"{BASE_URL}/api/select-table/{session_id}/{table_id}",
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"✗ 表選択失敗: {response.status_code}")
        print(f"エラー: {response.text}")
        return False
    
    select_result = response.json()
    headers = select_result["data"]["headers"]
    sample_records = select_result["data"]["sample_records"][:3]  # 最初の3行
    
    print(f"✓ 表選択成功")
    print(f"  ヘッダー: {headers}")
    print(f"  サンプル行数: {len(sample_records)}")
    
    # 5. スキーマ推論
    print("5. スキーマ推論を実行...")
    
    # サンプルレコードを配列形式に変換
    sample_data = []
    for record in sample_records:
        row = [record.get(header, "") for header in headers]
        sample_data.append(row)
    
    inference_request = {
        "session_id": session_id,
        "headers": headers,
        "sample_data": sample_data
    }
    
    response = requests.post(
        f"{BASE_URL}/api/infer-schema",
        json=inference_request,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"✗ スキーマ推論失敗: {response.status_code}")
        print(f"エラー: {response.text}")
        return False
    
    inference_result = response.json()
    
    print("✓ スキーマ推論成功!")
    print(f"レスポンス: {json.dumps(inference_result, indent=2, ensure_ascii=False)}")
    
    # 結果詳細表示
    data = inference_result.get("data", {})
    mappings = data.get("inference_result", {}).get("mappings", {})
    
    print("\n=== 推論結果詳細 ===")
    for column_type, mapping in mappings.items():
        if mapping:
            column_index = mapping.get('column_index')
            column_name = mapping.get('column_name')
            confidence = mapping.get('confidence')
            reasoning = mapping.get('reasoning')
            
            print(f"{column_type}:")
            print(f"  列インデックス: {column_index}")
            print(f"  列名: {column_name}")
            print(f"  信頼度: {confidence}%")
            print(f"  推論理由: {reasoning}")
            print()
        else:
            print(f"{column_type}: 検出されませんでした")
    
    overall_confidence = data.get("inference_result", {}).get("overall_confidence", 0)
    print(f"全体信頼度: {overall_confidence}%")
    
    return True

if __name__ == "__main__":
    success = test_complete_excel_flow()
    
    if success:
        print("\n✓ 完全なフローテストが成功しました！")
    else:
        print("\n✗ フローテストが失敗しました。")