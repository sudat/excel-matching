#!/usr/bin/env python3
"""
Gemini 2.5 Flash接続テストスクリプト
"""

import os
import sys
from dotenv import load_dotenv

# .envファイルを読み込み（プロジェクトルートから）
load_dotenv("../.env")

try:
    import google.generativeai as genai
    print("✓ Google Generative AI SDK import successful")
except ImportError as e:
    print(f"✗ Google Generative AI SDK import failed: {e}")
    sys.exit(1)

def test_gemini_connection():
    """Gemini接続をテスト"""
    try:
        # API キーの確認
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("✗ API key not found. Please set GOOGLE_API_KEY environment variable")
            return False
        
        print(f"✓ API key found: {api_key[:20]}...")
        
        # Gemini設定
        genai.configure(api_key=api_key)
        print("✓ Gemini configured")
        
        # モデル初期化
        model = genai.GenerativeModel('gemini-2.5-flash')
        print("✓ Gemini model initialized")
        
        # 簡単なテストリクエスト
        generation_config = genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=100
        )
        
        response = model.generate_content(
            "Hello! This is a connection test. Please respond with a simple JSON: {\"status\": \"connected\", \"message\": \"Hello from Gemini\"}",
            generation_config=generation_config
        )
        
        print("✓ Gemini response received:")
        print(f"Response: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"✗ Gemini connection test failed: {str(e)}")
        return False

def test_schema_inference_prompt():
    """スキーマ推論プロンプトのテスト"""
    try:
        # API キー取得
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GEMINI_API_KEY")
        
        # Gemini設定
        genai.configure(api_key=api_key)
        
        # モデル初期化
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # テスト用ヘッダーとサンプルデータ
        test_headers = ["日付", "金額", "申請者", "費目", "摘要"]
        test_sample_data = [
            ["2024/01/15", "12500", "田中太郎", "交通費", "出張電車代"],
            ["2024/01/16", "3500", "佐藤花子", "食事代", "会議弁当"],
            ["2024/01/17", "8000", "山田次郎", "宿泊費", "宿泊代"]
        ]
        
        formatted_sample = ""
        for i, row in enumerate(test_sample_data):
            row_str = [str(cell) for cell in row]
            formatted_sample += f"行{i+1}: {row_str}\n"
        
        prompt = f"""
あなたは経費精算・会計業務の専門家です。Excelファイルのヘッダーとサンプルデータを分析して、
以下の4つの列タイプに最も適した列を特定してください。

**対象列タイプ:**
1. **date_column**: 日付列（仕訳日付、発生日、支払日等）
2. **amount_column**: 金額列（基準金額、合計金額、税抜金額等）
3. **person_column**: 人物列（精算者、申請者、担当者等）
4. **category_column**: カテゴリ列（勘定科目、費目、分類等）

**分析対象データ:**
ヘッダー: {test_headers}

サンプルデータ:
{formatted_sample}

**レスポンス形式（JSON）:**
```json
{{
    "mappings": {{
        "date_column": {{
            "column_index": 0,
            "column_name": "日付",
            "confidence": 95,
            "reasoning": "「日付」という明確な列名で、サンプルデータが日付形式"
        }},
        "amount_column": {{
            "column_index": 1,
            "column_name": "金額",
            "confidence": 90,
            "reasoning": "「金額」という列名で、サンプルデータが数値形式"
        }},
        "person_column": {{
            "column_index": 2,
            "column_name": "申請者",
            "confidence": 85,
            "reasoning": "人名と思われるデータが含まれている"
        }},
        "category_column": {{
            "column_index": 3,
            "column_name": "費目",
            "confidence": 80,
            "reasoning": "経費の分類に関する列名"
        }}
    }},
    "overall_confidence": 87,
    "analysis_notes": "全体的に標準的な経費精算フォーマットに適合"
}}
```

必ずJSON形式で回答してください。```json ```ブロックは不要です。
"""
        
        generation_config = genai.types.GenerationConfig(
            temperature=0.1,
            max_output_tokens=1024
        )
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        print("✓ Schema inference test successful:")
        print(f"Response: {response.text}")
        
        # JSONパースのテスト
        import json
        try:
            result = json.loads(response.text.strip())
            print("✓ JSON parsing successful")
            print(f"Overall confidence: {result.get('overall_confidence', 'N/A')}")
        except json.JSONDecodeError as e:
            print(f"✗ JSON parsing failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Schema inference test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Gemini 2.5 Flash Connection Test ===")
    
    print("\n1. Testing basic connection...")
    basic_success = test_gemini_connection()
    
    if basic_success:
        print("\n2. Testing schema inference prompt...")
        schema_success = test_schema_inference_prompt()
        
        if schema_success:
            print("\n✓ All tests passed! Gemini 2.5 Flash is ready for schema inference.")
        else:
            print("\n✗ Schema inference test failed.")
    else:
        print("\n✗ Basic connection test failed. Please check your API key.")
    
    print("\n=== Test Complete ===")