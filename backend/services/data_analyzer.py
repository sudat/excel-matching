"""
データ型分析と品質分析
"""

import re
import logging
from typing import Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """データ分析機能を提供するクラス"""

    @staticmethod
    def detect_header_row(df: pd.DataFrame) -> int:
        """CSVファイルのヘッダー行を検出する"""
        try:
            # 最初の10行を分析（ファイルが小さい場合は全行）
            max_rows_to_check = min(10, len(df))

            header_candidates = []

            for i in range(max_rows_to_check):
                row = df.iloc[i]

                # 空行をスキップ
                if row.isna().all() or (row == "").all():
                    continue

                # 文字列データの割合を計算
                string_count = 0
                numeric_count = 0

                for value in row:
                    if pd.isna(value) or value == "":
                        continue

                    # 数値かどうかをチェック
                    try:
                        float(str(value).replace(",", ""))
                        numeric_count += 1
                    except (ValueError, TypeError):
                        string_count += 1

                total_values = string_count + numeric_count
                if total_values == 0:
                    continue

                string_ratio = string_count / total_values

                # ヘッダー行の候補として評価
                # - 文字列の割合が高い（70%以上）
                # - 少なくとも2つ以上の値がある
                if string_ratio >= 0.7 and total_values >= 2:
                    header_candidates.append(
                        {
                            "row_index": i,
                            "string_ratio": string_ratio,
                            "total_values": total_values,
                        }
                    )

            # 最も文字列の割合が高い行をヘッダーとして選択
            if header_candidates:
                best_candidate = max(header_candidates, key=lambda x: x["string_ratio"])
                return best_candidate["row_index"]

            # ヘッダー候補が見つからない場合は0行目を返す
            return 0

        except Exception as e:
            logger.warning(f"Header detection failed: {e}, using row 0 as default")
            return 0

    @staticmethod
    def analyze_data_types(df: pd.DataFrame) -> Dict[str, str]:
        """データ型を詳細に分析する"""
        data_types = {}

        for col in df.columns:
            col_data = df[col].dropna()  # 欠損値を除外

            if len(col_data) == 0:
                data_types[col] = "empty"
                continue

            # 数値型の判定
            numeric_count = 0
            date_count = 0
            boolean_count = 0

            for value in col_data:
                str_value = str(value).strip()

                # Boolean型チェック
                if str_value.lower() in [
                    "true",
                    "false",
                    "yes",
                    "no",
                    "y",
                    "n",
                    "1",
                    "0",
                ]:
                    boolean_count += 1
                    continue

                # 数値型チェック（カンマ区切りの数値も考慮）
                try:
                    float(str_value.replace(",", ""))
                    numeric_count += 1
                    continue
                except (ValueError, TypeError):
                    pass

                # 日付型チェック
                date_patterns = [
                    r"\d{4}-\d{2}-\d{2}",  # YYYY-MM-DD
                    r"\d{4}/\d{2}/\d{2}",  # YYYY/MM/DD
                    r"\d{2}/\d{2}/\d{4}",  # MM/DD/YYYY
                    r"\d{2}-\d{2}-\d{4}",  # MM-DD-YYYY
                ]

                for pattern in date_patterns:
                    if re.match(pattern, str_value):
                        date_count += 1
                        break

            total_values = len(col_data)

            # データ型を決定（閾値: 80%）
            if boolean_count / total_values >= 0.8:
                data_types[col] = "boolean"
            elif date_count / total_values >= 0.8:
                data_types[col] = "date"
            elif numeric_count / total_values >= 0.8:
                # 整数か小数点数かを判定
                integer_count = 0
                for value in col_data:
                    str_value = str(value).strip().replace(",", "")
                    try:
                        float_val = float(str_value)
                        if float_val.is_integer():
                            integer_count += 1
                    except (ValueError, TypeError):
                        pass

                if integer_count / numeric_count >= 0.9:
                    data_types[col] = "integer"
                else:
                    data_types[col] = "number"
            else:
                # カテゴリ型かどうかを判定
                unique_ratio = len(col_data.unique()) / total_values
                if (
                    unique_ratio <= 0.1 and len(col_data.unique()) <= 20
                ):  # 重複が多くユニーク値が少ない
                    data_types[col] = "category"
                else:
                    data_types[col] = "string"

        return data_types

    @staticmethod
    def analyze_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
        """データ品質を分析する"""
        quality_report = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "missing_data": {},
            "data_consistency": {},
            "statistics": {},
        }

        for col in df.columns:
            col_data = df[col]

            # 欠損値分析
            missing_count = col_data.isna().sum()
            missing_ratio = missing_count / len(col_data) if len(col_data) > 0 else 0

            quality_report["missing_data"][col] = {
                "count": int(missing_count),
                "ratio": float(missing_ratio),
            }

            # データ一貫性分析
            non_missing_data = col_data.dropna()
            if len(non_missing_data) > 0:
                unique_count = len(non_missing_data.unique())
                unique_ratio = unique_count / len(non_missing_data)

                quality_report["data_consistency"][col] = {
                    "unique_values": int(unique_count),
                    "unique_ratio": float(unique_ratio),
                    "duplicates": int(len(non_missing_data) - unique_count),
                }

                # 数値列の統計情報
                try:
                    numeric_data = pd.to_numeric(
                        non_missing_data, errors="coerce"
                    ).dropna()
                    if len(numeric_data) > 0:
                        quality_report["statistics"][col] = {
                            "mean": float(numeric_data.mean()),
                            "median": float(numeric_data.median()),
                            "std": float(numeric_data.std()),
                            "min": float(numeric_data.min()),
                            "max": float(numeric_data.max()),
                        }
                except Exception:
                    pass  # 数値変換できない場合はスキップ

        return quality_report
