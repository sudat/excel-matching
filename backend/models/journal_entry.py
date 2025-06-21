from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, ClassVar, Dict
from decimal import Decimal


class JournalEntry(BaseModel):
    """
    会計仕訳データモデル
    実際のCSVファイルの18項目レイアウトに基づいて定義
    """

    # CSVカラム名から英語フィールド名へのマッピング
    CSV_FIELD_MAPPING: ClassVar[Dict[str, str]] = {
        "日付": "date",
        "仕訳番号": "journal_number",
        "伝票摘要": "voucher_description",
        "行番号": "line_number",
        "借貸": "debit_credit",
        "勘定科目コード": "account_code",
        "勘定科目名": "account_name",
        "補助科目コード": "sub_account_code",
        "補助科目名": "sub_account_name",
        "取引先コード": "customer_code",
        "取引先名": "customer_name",
        "分析コード": "analysis_code",
        "分析コード名": "analysis_code_name",
        "基準金額": "base_amount",
        "税額": "tax_amount",
        "合計金額": "total_amount",
        "税区分": "tax_category",
        "明細摘要": "detail_description",
    }

    # 1. 日付 - 必須項目
    date: datetime = Field(..., description="仕訳日付 (YYYY/MM/DD形式)")

    # 2. 仕訳番号 - 必須項目
    journal_number: str = Field(..., description="仕訳番号 (例: 20250103000001)")

    # 3. 伝票摘要 - 必須項目
    voucher_description: str = Field(..., description="伝票摘要")

    # 4. 行番号 - 必須項目
    line_number: int = Field(..., description="行番号", ge=1)

    # 5. 借貸 - 必須項目 (D: 借方, C: 貸方)
    debit_credit: str = Field(
        ..., description="借貸区分 (D: 借方, C: 貸方)", pattern="^[DC]$"
    )

    # 6. 勘定科目コード - 必須項目
    account_code: str = Field(..., description="勘定科目コード (例: 1010)")

    # 7. 勘定科目名 - 必須項目
    account_name: str = Field(..., description="勘定科目名 (例: 普通預金)")

    # 8. 補助科目コード - オプション項目
    sub_account_code: Optional[str] = Field(None, description="補助科目コード")

    # 9. 補助科目名 - オプション項目
    sub_account_name: Optional[str] = Field(None, description="補助科目名")

    # 10. 取引先コード - オプション項目
    customer_code: Optional[str] = Field(None, description="取引先コード")

    # 11. 取引先名 - オプション項目
    customer_name: Optional[str] = Field(None, description="取引先名")

    # 12. 分析コード - オプション項目
    analysis_code: Optional[str] = Field(None, description="分析コード")

    # 13. 分析コード名 - オプション項目
    analysis_code_name: Optional[str] = Field(None, description="分析コード名")

    # 14. 基準金額 - 必須項目（税抜金額）
    base_amount: Decimal = Field(..., description="基準金額（税抜）", ge=0)

    # 15. 税額 - 必須項目
    tax_amount: Decimal = Field(..., description="税額", ge=0)

    # 16. 合計金額 - 必須項目（税込金額）
    total_amount: Decimal = Field(..., description="合計金額（税込）", ge=0)

    # 17. 税区分 - 必須項目
    tax_category: str = Field(
        ..., description="税区分 (例: 消費税10%(10%), 非課税(0%))"
    )

    # 18. 明細摘要 - オプション項目
    detail_description: Optional[str] = Field(None, description="明細摘要")

    @validator("date", pre=True)
    def parse_date(cls, v):
        """日付文字列をdatetimeオブジェクトに変換"""
        if isinstance(v, str):
            try:
                return datetime.strptime(v, "%Y/%m/%d")
            except ValueError:
                raise ValueError(
                    f"日付形式が正しくありません: {v}. YYYY/MM/DD形式で入力してください。"
                )
        return v

    @validator("base_amount", "tax_amount", "total_amount", pre=True)
    def parse_decimal(cls, v):
        """数値文字列をDecimalに変換"""
        if isinstance(v, str):
            # カンマを除去して数値に変換
            v = v.replace(",", "")
            return Decimal(v)
        return Decimal(str(v))

    @validator("total_amount")
    def validate_total_amount(cls, v, values):
        """合計金額が基準金額+税額と一致することを確認"""
        if "base_amount" in values and "tax_amount" in values:
            expected_total = values["base_amount"] + values["tax_amount"]
            if abs(v - expected_total) > Decimal("0.01"):  # 1円の誤差まで許容
                raise ValueError(
                    f"合計金額が不正です。基準金額({values['base_amount']}) + 税額({values['tax_amount']}) = {expected_total} ≠ {v}"
                )
        return v

    @classmethod
    def from_csv_row(cls, csv_row: dict) -> "JournalEntry":
        """
        CSVの日本語カラム名から英語フィールド名に変換してインスタンスを作成
        """
        mapped_data = {}
        for japanese_key, english_key in cls.CSV_FIELD_MAPPING.items():
            if japanese_key in csv_row:
                value = csv_row[japanese_key]
                # 空文字列をNoneに変換（オプションフィールド用）
                if value == "" and english_key in [
                    "sub_account_code",
                    "sub_account_name",
                    "customer_code",
                    "customer_name",
                    "analysis_code",
                    "analysis_code_name",
                    "detail_description",
                ]:
                    mapped_data[english_key] = None
                else:
                    mapped_data[english_key] = value

        return cls(**mapped_data)

    def to_text_for_embedding(self) -> str:
        """
        RAG検索用のテキスト形式に変換
        各フィールドを検索可能な自然言語形式で結合
        """
        parts = [
            f"日付: {self.date.strftime('%Y年%m月%d日')}",
            f"仕訳番号: {self.journal_number}",
            f"{"借方" if self.debit_credit == "D" else "貸方"}",
            f"勘定科目: {self.account_name}({self.account_code})",
        ]

        if self.sub_account_name:
            parts.append(f"補助科目: {self.sub_account_name}")

        if self.customer_name:
            parts.append(f"取引先: {self.customer_name}")

        parts.extend(
            [
                f"金額: {self.total_amount:,}円",
                f"基準金額: {self.base_amount:,}円",
                f"税額: {self.tax_amount:,}円",
                f"税区分: {self.tax_category}",
            ]
        )

        if self.voucher_description:
            parts.append(f"摘要: {self.voucher_description}")

        if self.detail_description:
            parts.append(f"明細: {self.detail_description}")

        return ", ".join(parts)

    def to_metadata_dict(self) -> dict:
        """
        Pinecone保存用のメタデータ辞書を生成
        """
        return {
            "journal_number": self.journal_number,
            "date": self.date.strftime("%Y-%m-%d"),
            "debit_credit": self.debit_credit,
            "account_code": self.account_code,
            "account_name": self.account_name,
            "sub_account_code": self.sub_account_code or "",
            "sub_account_name": self.sub_account_name or "",
            "customer_code": self.customer_code or "",
            "customer_name": self.customer_name or "",
            "base_amount": float(self.base_amount),
            "tax_amount": float(self.tax_amount),
            "total_amount": float(self.total_amount),
            "tax_category": self.tax_category,
            "voucher_description": self.voucher_description,
            "detail_description": self.detail_description or "",
        }

    class Config:
        # JSON エンコーディング時の設定
        json_encoders = {
            datetime: lambda v: v.strftime("%Y/%m/%d"),
            Decimal: lambda v: float(v),
        }
