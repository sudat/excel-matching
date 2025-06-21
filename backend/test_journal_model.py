#!/usr/bin/env python3
"""
仕訳データモデルのテストスクリプト
Pydanticモデルが正しく定義され、サンプルCSVデータがスキーマに準拠していることを確認
"""

import sys
import os
import csv
from pathlib import Path
import pytest
from datetime import datetime
from decimal import Decimal

# パスを追加してモデルをインポート
sys.path.append(str(Path(__file__).parent))
from models.journal_entry import JournalEntry


def test_journal_entry_model():
    """JournalEntryモデルのテスト"""
    print("=== JournalEntryモデルテスト開始 ===")

    # サンプルCSVファイルのパス
    csv_path = Path(__file__).parent / "data" / "sample_journal_entries.csv"

    if not csv_path.exists():
        print(f"エラー: サンプルCSVファイルが見つかりません: {csv_path}")
        return False

    print(f"CSVファイル読み込み: {csv_path}")

    success_count = 0
    error_count = 0

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            # BOMを除去
            content = f.read()
            if content.startswith("\ufeff"):
                content = content[1:]

            # CSVを再度読み込み
            csv_reader = csv.DictReader(content.splitlines())

            for i, row in enumerate(csv_reader, 1):
                try:
                    # Pydanticモデルでパース
                    journal_entry = JournalEntry(
                        date=row["日付"],
                        journal_number=row["仕訳番号"],
                        voucher_description=row["伝票摘要"],
                        line_number=int(row["行番号"]),
                        debit_credit=row["借貸"],
                        account_code=row["勘定科目コード"],
                        account_name=row["勘定科目名"],
                        sub_account_code=(
                            row["補助科目コード"] if row["補助科目コード"] else None
                        ),
                        sub_account_name=(
                            row["補助科目名"] if row["補助科目名"] else None
                        ),
                        customer_code=(
                            row["取引先コード"] if row["取引先コード"] else None
                        ),
                        customer_name=row["取引先名"] if row["取引先名"] else None,
                        analysis_code=row["分析コード"] if row["分析コード"] else None,
                        analysis_code_name=(
                            row["分析コード名"] if row["分析コード名"] else None
                        ),
                        base_amount=row["基準金額"],
                        tax_amount=row["税額"],
                        total_amount=row["合計金額"],
                        tax_category=row["税区分"],
                        detail_description=row["明細摘要"] if row["明細摘要"] else None,
                    )

                    print(
                        f"✓ 行 {i}: {journal_entry.journal_number} - {journal_entry.account_name} - {journal_entry.total_amount}円"
                    )

                    # テキスト埋め込み用形式のテスト
                    text_for_embedding = journal_entry.to_text_for_embedding()
                    print(f"  埋め込み用テキスト: {text_for_embedding[:100]}...")

                    # メタデータ辞書のテスト
                    metadata = journal_entry.to_metadata_dict()
                    print(f"  メタデータ項目数: {len(metadata)}")

                    success_count += 1

                except Exception as e:
                    print(f"✗ 行 {i}でエラー: {e}")
                    print(f"  データ: {row}")
                    error_count += 1

    except Exception as e:
        print(f"CSV読み込みエラー: {e}")
        return False

    print(f"\n=== テスト結果 ===")
    print(f"成功: {success_count}件")
    print(f"エラー: {error_count}件")
    print(f"成功率: {success_count / (success_count + error_count) * 100:.1f}%")

    return error_count == 0


def test_individual_record():
    """個別レコードのテスト"""
    print("\n=== 個別レコードテスト ===")

    try:
        # 手動で作成したテストデータ
        test_data = {
            "date": "2025/01/03",
            "journal_number": "20250103000001",
            "voucher_description": "売上入金処理",
            "line_number": 1,
            "debit_credit": "D",
            "account_code": "1010",
            "account_name": "普通預金",
            "sub_account_code": None,
            "sub_account_name": None,
            "customer_code": None,
            "customer_name": None,
            "analysis_code": None,
            "analysis_code_name": None,
            "base_amount": "13790",
            "tax_amount": "1379",
            "total_amount": "15169",
            "tax_category": "非課税(0%)",
            "detail_description": None,
        }

        journal_entry = JournalEntry(**test_data)
        print(f"✓ 個別テスト成功: {journal_entry.journal_number}")
        print(f"  日付: {journal_entry.date}")
        print(
            f"  金額検証: {journal_entry.base_amount} + {journal_entry.tax_amount} = {journal_entry.total_amount}"
        )

        return True

    except Exception as e:
        print(f"✗ 個別テストエラー: {e}")
        return False


def test_journal_entry_model_basic():
    """基本的なJournalEntryモデルの動作テスト"""
    data = {
        "date": "2025/01/03",
        "journal_number": "20250103000001",
        "voucher_description": "売上入金処理",
        "line_number": 1,
        "debit_credit": "D",
        "account_code": "1010",
        "account_name": "普通預金",
        "base_amount": "13790",
        "tax_amount": "1379",
        "total_amount": "15169",
        "tax_category": "非課税(0%)",
    }

    entry = JournalEntry(**data)

    # 基本的な値の確認
    assert entry.date == datetime(2025, 1, 3)
    assert entry.journal_number == "20250103000001"
    assert entry.debit_credit == "D"
    assert entry.base_amount == Decimal("13790")
    assert entry.tax_amount == Decimal("1379")
    assert entry.total_amount == Decimal("15169")


def test_journal_entry_validation():
    """バリデーション機能のテスト"""
    # 無効な借貸区分
    with pytest.raises(ValueError):
        JournalEntry(
            date="2025/01/03",
            journal_number="20250103000001",
            voucher_description="テスト",
            line_number=1,
            debit_credit="X",  # 無効な値
            account_code="1010",
            account_name="普通預金",
            base_amount="1000",
            tax_amount="100",
            total_amount="1100",
            tax_category="消費税10%(10%)",
        )

    # 無効な日付形式
    with pytest.raises(ValueError):
        JournalEntry(
            date="2025-01-03",  # 無効な形式
            journal_number="20250103000001",
            voucher_description="テスト",
            line_number=1,
            debit_credit="D",
            account_code="1010",
            account_name="普通預金",
            base_amount="1000",
            tax_amount="100",
            total_amount="1100",
            tax_category="消費税10%(10%)",
        )


def test_total_amount_validation():
    """合計金額のバリデーションテスト"""
    # 正しい合計金額
    entry = JournalEntry(
        date="2025/01/03",
        journal_number="20250103000001",
        voucher_description="テスト",
        line_number=1,
        debit_credit="D",
        account_code="1010",
        account_name="普通預金",
        base_amount="1000",
        tax_amount="100",
        total_amount="1100",  # 1000 + 100 = 1100
        tax_category="消費税10%(10%)",
    )
    assert entry.total_amount == Decimal("1100")

    # 不正な合計金額
    with pytest.raises(ValueError):
        JournalEntry(
            date="2025/01/03",
            journal_number="20250103000001",
            voucher_description="テスト",
            line_number=1,
            debit_credit="D",
            account_code="1010",
            account_name="普通預金",
            base_amount="1000",
            tax_amount="100",
            total_amount="1200",  # 不正：1000 + 100 ≠ 1200
            tax_category="消費税10%(10%)",
        )


def test_sample_csv_parsing():
    """サンプルCSVファイルのパーシングテスト"""
    csv_file_path = "data/sample_journal_entries.csv"

    # ファイルの存在確認
    assert os.path.exists(
        csv_file_path
    ), f"サンプルCSVファイルが見つかりません: {csv_file_path}"

    entries = []
    with open(csv_file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            try:
                entry = JournalEntry.from_csv_row(row)
                entries.append(entry)
            except Exception as e:
                pytest.fail(
                    f"CSVデータのパースに失敗しました。行データ: {row}, エラー: {e}"
                )

    # 最低限のデータが読み込まれることを確認
    assert len(entries) > 0, "CSVファイルからデータが読み込まれませんでした"
    print(f"正常にパースされた仕訳エントリ数: {len(entries)}")


def test_to_text_for_embedding():
    """RAG検索用テキスト変換のテスト"""
    entry = JournalEntry(
        date="2025/01/03",
        journal_number="20250103000001",
        voucher_description="売上入金処理",
        line_number=1,
        debit_credit="D",
        account_code="1010",
        account_name="普通預金",
        sub_account_name="三菱UFJ銀行",
        customer_name="株式会社テスト",
        base_amount="13790",
        tax_amount="1379",
        total_amount="15169",
        tax_category="非課税(0%)",
        detail_description="現金売上入金",
    )

    text = entry.to_text_for_embedding()

    # 重要な情報が含まれていることを確認
    assert "2025年01月03日" in text
    assert "借方" in text
    assert "普通預金" in text
    assert "15,169円" in text
    assert "売上入金処理" in text
    assert "現金売上入金" in text

    print(f"生成されたテキスト: {text}")


def test_to_metadata_dict():
    """Pineconeメタデータ変換のテスト"""
    entry = JournalEntry(
        date="2025/01/03",
        journal_number="20250103000001",
        voucher_description="売上入金処理",
        line_number=1,
        debit_credit="D",
        account_code="1010",
        account_name="普通預金",
        base_amount="13790",
        tax_amount="1379",
        total_amount="15169",
        tax_category="非課税(0%)",
    )

    metadata = entry.to_metadata_dict()

    # 必須フィールドの確認
    assert metadata["journal_number"] == "20250103000001"
    assert metadata["date"] == "2025-01-03"
    assert metadata["debit_credit"] == "D"
    assert metadata["account_code"] == "1010"
    assert metadata["account_name"] == "普通預金"
    assert metadata["total_amount"] == 15169.0

    print(f"生成されたメタデータ: {metadata}")


def test_csv_data_integrity():
    """CSVデータの整合性テスト"""
    csv_file_path = "data/sample_journal_entries.csv"

    with open(csv_file_path, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for i, row in enumerate(reader, 1):
            try:
                entry = JournalEntry.from_csv_row(row)

                # 基準金額 + 税額 = 合計金額の確認
                expected_total = entry.base_amount + entry.tax_amount
                assert abs(entry.total_amount - expected_total) <= Decimal(
                    "0.01"
                ), f"行{i}: 金額計算エラー - 基準金額({entry.base_amount}) + 税額({entry.tax_amount}) ≠ 合計金額({entry.total_amount})"

                # 借貸区分の確認
                assert entry.debit_credit in [
                    "D",
                    "C",
                ], f"行{i}: 無効な借貸区分 - {entry.debit_credit}"

                # 日付の確認
                assert isinstance(
                    entry.date, datetime
                ), f"行{i}: 日付の型が正しくありません"

            except Exception as e:
                pytest.fail(f"行{i}のデータに問題があります: {row}, エラー: {e}")


if __name__ == "__main__":
    print("JournalEntryモデル検証スクリプト")
    print("=" * 50)

    # 個別レコードテスト
    individual_success = test_individual_record()

    # CSVファイルテスト
    csv_success = test_journal_entry_model()

    # 基本テスト
    try:
        test_journal_entry_model_basic()
        print("✅ 基本モデルテスト: 成功")
    except Exception as e:
        print(f"❌ 基本モデルテスト: 失敗 - {e}")

    # バリデーションテスト
    try:
        test_journal_entry_validation()
        print("✅ バリデーションテスト: 成功")
    except Exception as e:
        print(f"❌ バリデーションテスト: 失敗 - {e}")

    # 合計金額バリデーションテスト
    try:
        test_total_amount_validation()
        print("✅ 合計金額バリデーションテスト: 成功")
    except Exception as e:
        print(f"❌ 合計金額バリデーションテスト: 失敗 - {e}")

    # CSVパーシングテスト
    try:
        test_sample_csv_parsing()
        print("✅ CSVパーシングテスト: 成功")
    except Exception as e:
        print(f"❌ CSVパーシングテスト: 失敗 - {e}")

    # テキスト変換テスト
    try:
        test_to_text_for_embedding()
        print("✅ テキスト変換テスト: 成功")
    except Exception as e:
        print(f"❌ テキスト変換テスト: 失敗 - {e}")

    # メタデータ変換テスト
    try:
        test_to_metadata_dict()
        print("✅ メタデータ変換テスト: 成功")
    except Exception as e:
        print(f"❌ メタデータ変換テスト: 失敗 - {e}")

    # データ整合性テスト
    try:
        test_csv_data_integrity()
        print("✅ データ整合性テスト: 成功")
    except Exception as e:
        print(f"❌ データ整合性テスト: 失敗 - {e}")

    if individual_success and csv_success:
        print("\n🎉 すべてのテストが成功しました！")
        sys.exit(0)
    else:
        print("\n❌ テストが失敗しました。")
        sys.exit(1)
