#!/usr/bin/env python3
"""
Geminiエンベディング機能のテストスクリプト
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# 環境変数を読み込み
load_dotenv(Path(__file__).parent.parent / ".env")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
    print(f"Gemini API設定完了: キー末尾{GOOGLE_API_KEY[-4:]}")
else:
    print("GOOGLE_API_KEYが設定されていません")
    exit(1)

async def test_embedding():
    try:
        # テスト用のテキスト
        test_text = "日付: 2025年01月03日, 仕訳番号: 20250103000001, 借方, 勘定科目: 普通預金(1010), 金額: 15,169円, 基準金額: 13,790円, 税額: 1,379円, 税区分: 非課税(0%), 摘要: 売上入金処理"
        
        print(f"テストテキスト: {test_text}")
        print("\nGeminiエンベディング生成中...")
        
        # Geminiでエンベディング生成
        embedding_result = genai.embed_content(
            model="models/text-embedding-004",
            content=test_text
        )
        
        print(f"成功！エンベディング次元数: {len(embedding_result['embedding'])}")
        print(f"エンベディングベクトル（最初の5要素）: {embedding_result['embedding'][:5]}")
        
        return True
        
    except Exception as e:
        print(f"エラー: {str(e)}")
        print(f"エラータイプ: {type(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_embedding())
    if result:
        print("\n✅ Geminiエンベディングテスト成功")
    else:
        print("\n❌ Geminiエンベディングテスト失敗")