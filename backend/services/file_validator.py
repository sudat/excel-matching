"""
ファイル検証機能
"""

import os
from typing import Set
from fastapi import UploadFile, HTTPException

# 許可されるファイルタイプ
ALLOWED_EXTENSIONS: Set[str] = {".xlsx", ".xls", ".csv"}

ALLOWED_MIME_TYPES: Set[str] = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-excel",  # .xls
    "text/csv",  # .csv
    "application/csv",  # .csv
}

# ファイルサイズ制限（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes


class FileValidator:
    """ファイル検証機能を提供するクラス"""

    @staticmethod
    def detect_file_type(file: UploadFile) -> str:
        """ファイルの形式を判定する"""
        if not file.filename:
            raise HTTPException(
                status_code=400, detail="ファイル名が指定されていません"
            )

        # ファイル拡張子チェック
        file_extension = os.path.splitext(file.filename.lower())[1]
        if file_extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"サポートされていないファイル形式です: {file_extension}",
            )

        # MIMEタイプチェック
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"サポートされていないMIMEタイプです: {file.content_type}",
            )

        # ファイルタイプを返す
        if file_extension == ".csv":
            return "csv"
        elif file_extension in [".xlsx", ".xls"]:
            return "excel"
        else:
            raise HTTPException(status_code=400, detail="未知のファイル形式です")

    @staticmethod
    def validate_file_size(content: bytes) -> None:
        """ファイルサイズを検証する"""
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"ファイルサイズが大きすぎます（最大10MB）: {len(content)} bytes",
            )

    @staticmethod
    def validate_excel_file(file: UploadFile) -> bool:
        """Excelファイルの妥当性をチェック"""
        if not file.filename:
            return False

        # ファイル拡張子チェック
        file_extension = os.path.splitext(file.filename.lower())[1]
        if file_extension not in [".xlsx", ".xls"]:
            return False

        # MIMEタイプチェック
        excel_mime_types = {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
            "application/vnd.ms-excel",  # .xls
        }
        if file.content_type not in excel_mime_types:
            return False

        return True
