#!/usr/bin/env python3
"""
Pinecone journal-entriesインデックスの全データを削除するスクリプト
"""

import os
from pinecone import Pinecone
from dotenv import load_dotenv

# 環境変数を読み込み
load_dotenv()


def delete_all_journal_entries():
    """journal-entriesインデックスの全データを削除"""

    # Pineconeクライアントを初期化
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    if not PINECONE_API_KEY:
        print("❌ PINECONE_API_KEYが設定されていません")
        return False

    try:
        pc = Pinecone(api_key=PINECONE_API_KEY)

        # インデックスに接続
        index_name = "journal-entries"
        index = pc.Index(index_name)

        # 削除前の統計情報を表示
        stats_before = index.describe_index_stats()
        total_count_before = stats_before.get("total_vector_count", 0)
        print(f"📊 削除前: {total_count_before}件のベクトルデータ")

        if total_count_before == 0:
            print("✅ 削除対象のデータがありません")
            return True

        # 確認プロンプト
        confirm = input(
            f"⚠️  {total_count_before}件の全データを削除しますか？ (yes/no): "
        )
        if confirm.lower() != "yes":
            print("❌ 削除がキャンセルされました")
            return False

        # 全データを削除
        print("🗑️  全データを削除中...")
        index.delete(delete_all=True)

        # 削除後の統計情報を確認
        print("⏳ 削除完了を確認中...")
        stats_after = index.describe_index_stats()
        total_count_after = stats_after.get("total_vector_count", 0)

        print(f"📊 削除後: {total_count_after}件のベクトルデータ")

        if total_count_after == 0:
            print("✅ 全データの削除が完了しました！")
            return True
        else:
            print(f"⚠️  {total_count_after}件のデータが残っています")
            return False

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        return False


if __name__ == "__main__":
    print("🧹 Pinecone journal-entries データ削除スクリプト")
    print("=" * 50)

    success = delete_all_journal_entries()

    if success:
        print("\n🎉 削除処理が正常に完了しました")
    else:
        print("\n💥 削除処理中にエラーが発生しました")
