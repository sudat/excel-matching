"""
ファイル処理機能
"""

import uuid
import logging
from typing import Dict, Any
from io import BytesIO
import pandas as pd
from fastapi import UploadFile, HTTPException

from utils.excel_utils import get_excel_sheets_info
from services.data_analyzer import DataAnalyzer
from services.session_manager import SessionManager

logger = logging.getLogger(__name__)


class FileProcessor:
    """ファイル処理機能を提供するクラス"""

    def __init__(self):
        self.data_analyzer = DataAnalyzer()

    async def process_csv_advanced(
        self,
        file_content: bytes,
        filename: str,
        session_id: str,
        session_manager: SessionManager,
    ) -> Dict[str, Any]:
        """CSV ファイルを高度に解析する"""
        try:
            logger.info(
                f"Advanced processing CSV file: {filename} (session: {session_id})"
            )

            # セッションデータを作成
            session = session_manager.create_session(session_id)

            # CSVファイルを読み込み（ヘッダーなしで読み込んで後で判定）
            df_raw = pd.read_csv(BytesIO(file_content), header=None)

            # ヘッダー行を検出
            header_row = self.data_analyzer.detect_header_row(df_raw)

            # ヘッダー行を使用してデータフレームを再構成
            if header_row > 0:
                # ヘッダー行より前の行を削除
                df_raw = df_raw.iloc[header_row:].reset_index(drop=True)

            # 1行目を列名として使用
            df = pd.read_csv(BytesIO(file_content), skiprows=header_row)

            # セッションにデータを保存
            session["raw_data"] = df_raw
            session["processed_data"] = df
            session["file_info"] = {
                "filename": filename,
                "file_type": "csv",
                "detected_header_row": header_row,
                "total_rows": len(df),
                "total_columns": len(df.columns),
            }

            # 詳細なデータ型分析
            data_types = self.data_analyzer.analyze_data_types(df)

            # データ品質分析
            quality_report = self.data_analyzer.analyze_data_quality(df)

            # 分析結果をセッションに保存
            session["analysis_result"] = {
                "data_types": data_types,
                "quality_report": quality_report,
            }

            # 基本情報を取得
            columns = df.columns.tolist()
            total_rows = len(df)

            # サンプルデータを取得（最初の5行）
            sample_data = df.head(5).fillna("").to_dict("records")

            return {
                "file_type": "csv",
                "detected_header_row": header_row,
                "columns": columns,
                "data_types": data_types,
                "sample_data": sample_data,
                "total_rows": total_rows,
                "quality_summary": {
                    "missing_data_columns": len(
                        [
                            col
                            for col, info in quality_report["missing_data"].items()
                            if info["ratio"] > 0
                        ]
                    ),
                    "numeric_columns": len(
                        [
                            col
                            for col, dtype in data_types.items()
                            if dtype in ["integer", "number"]
                        ]
                    ),
                    "date_columns": len(
                        [col for col, dtype in data_types.items() if dtype == "date"]
                    ),
                    "category_columns": len(
                        [
                            col
                            for col, dtype in data_types.items()
                            if dtype == "category"
                        ]
                    ),
                },
            }

        except Exception as e:
            logger.error(f"Error processing CSV file {filename}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"CSVファイルの処理中にエラーが発生しました: {str(e)}",
            )

    async def process_excel(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Excel ファイルを処理する（基本版）"""
        try:
            logger.info(f"Processing Excel file: {filename}")

            # 現段階では基本的な読み込みのみ実装
            df = pd.read_excel(BytesIO(file_content))

            # 基本情報を取得
            columns = df.columns.tolist()
            total_rows = len(df)

            # データ型を推論
            data_types = {}
            for col in columns:
                dtype = str(df[col].dtype)
                # pandasのデータ型を簡潔な形式に変換
                if dtype.startswith("int"):
                    data_types[col] = "integer"
                elif dtype.startswith("float"):
                    data_types[col] = "number"
                elif dtype.startswith("bool"):
                    data_types[col] = "boolean"
                elif dtype.startswith("datetime"):
                    data_types[col] = "date"
                else:
                    data_types[col] = "string"

            # サンプルデータを取得（最初の5行）
            sample_data = df.head(5).to_dict("records")

            return {
                "file_type": "excel",
                "detected_header_row": 0,  # 暫定的に0行目を設定
                "columns": columns,
                "data_types": data_types,
                "sample_data": sample_data,
                "total_rows": total_rows,
                "note": "Excel表走査機能は次段階で実装予定",
            }

        except Exception as e:
            logger.error(f"Error processing Excel file {filename}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Excelファイルの処理中にエラーが発生しました: {str(e)}",
            )

    def process_excel_sheets(
        self,
        file_content: bytes,
        filename: str,
        session_id: str,
        session_manager: SessionManager,
    ) -> Dict[str, Any]:
        """Excelファイルのシート情報を処理してセッションに保存"""
        try:
            logger.info(
                f"Processing Excel sheets for file: {filename} (session: {session_id})"
            )

            # セッションデータを作成
            session = session_manager.create_session(session_id)

            # シート情報を取得
            sheets_info = get_excel_sheets_info(file_content)

            # セッションにデータを保存
            session["file_info"] = {
                "filename": filename,
                "file_type": "excel",
                "total_sheets": len(sheets_info),
                "sheets_info": sheets_info,
            }

            # ワークブックデータも保存（バイト形式で保存）
            session["raw_workbook_data"] = file_content

            return {
                "filename": filename,
                "sheets": sheets_info,
                "total_sheets": len(sheets_info),
            }

        except Exception as e:
            logger.error(f"Error processing Excel file {filename}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Excelファイルの処理中にエラーが発生しました: {str(e)}",
            )
