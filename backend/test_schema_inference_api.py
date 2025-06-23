#!/usr/bin/env python3
"""
スキーマ推論APIのテストスクリプト
"""

import requests
import json
import uuid

BASE_URL = "http://localhost:8000"

def test_schema_inference_api():
    """スキーマ推論APIをテスト"""
    
    print("=== スキーマ推論API テスト ===")
    
    # テスト用データ
    test_session_id = str(uuid.uuid4())
    test_headers = ["日付", "金額", "申請者", "費目", "摘要", "部署"]
    test_sample_data = [
        ["2024/01/15", "12500", "田中太郎", "交通費", "出張電車代", "営業部"],
        ["2024/01/16", "3500", "佐藤花子", "食事代", "会議弁当", "総務部"],
        ["2024/01/17", "8000", "山田次郎", "宿泊費", "宿泊代", "開発部"]
    ]
    
    # 1. セッションデータをモックで作成（通常は既存の表選択フローで作成済み）
    print("1. 模擬セッションデータを作成...")
    
    # セッション作成の代わりにテスト用データを直接送信
    # （実際にはparse-excel-sheets -> select-table のフローを経て作成される）
    
    # 2. スキーマ推論APIを呼び出し
    print("2. スキーマ推論APIを呼び出し...")
    
    inference_request = {
        "session_id": test_session_id,
        "headers": test_headers,
        "sample_data": test_sample_data
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/infer-schema",
            json=inference_request,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ API呼び出し成功!")
            print(f"レスポンス: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 結果検証
            data = result.get("data", {})
            inference_result = data.get("inference_result", {})
            mappings = inference_result.get("mappings", {})
            
            print("\n=== 推論結果の検証 ===")
            for column_type, mapping in mappings.items():
                if mapping:
                    print(f"{column_type}: {mapping.get('column_name')} (信頼度: {mapping.get('confidence')}%)")
                    print(f"  理由: {mapping.get('reasoning')}")
                else:
                    print(f"{column_type}: 検出されませんでした")
            
            overall_confidence = inference_result.get("overall_confidence", 0)
            print(f"\n全体信頼度: {overall_confidence}%")
            
            return True
            
        else:
            print(f"✗ API呼び出し失敗: {response.status_code}")
            print(f"エラー内容: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("✗ サーバーに接続できませんでした。サーバーが起動していることを確認してください。")
        return False
    except requests.exceptions.Timeout:
        print("✗ リクエストがタイムアウトしました。")
        return False
    except Exception as e:
        print(f"✗ 予期しないエラー: {str(e)}")
        return False

def test_edge_cases():
    """エッジケースのテスト"""
    
    print("\n=== エッジケースのテスト ===")
    
    # 1. 空のヘッダーでテスト
    print("1. 空のヘッダーでテスト...")
    response = requests.post(
        f"{BASE_URL}/api/infer-schema",
        json={
            "session_id": str(uuid.uuid4()),
            "headers": [],
            "sample_data": []
        },
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    if response.status_code == 400:
        print("✓ 空のヘッダーを正しく拒否")
    else:
        print(f"✗ 予期しないレスポンス: {response.status_code}")
    
    # 2. 無効なセッションIDでテスト
    print("2. 無効なセッションIDでテスト...")
    response = requests.post(
        f"{BASE_URL}/api/infer-schema",
        json={
            "session_id": "invalid-session-id",
            "headers": ["日付", "金額"],
            "sample_data": [["2024/01/01", "1000"]]
        },
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    if response.status_code == 404:
        print("✓ 無効なセッションIDを正しく拒否")
    else:
        print(f"✗ 予期しないレスポンス: {response.status_code}")

if __name__ == "__main__":
    success = test_schema_inference_api()
    
    if success:
        test_edge_cases()
        print("\n✓ 全てのテストが完了しました。")
    else:
        print("\n✗ メインテストが失敗しました。")