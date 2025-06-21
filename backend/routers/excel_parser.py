from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any, Optional
import pandas as pd
import openpyxl
import uuid
import os
import logging
from io import BytesIO

# ログ設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/api", tags=["Excel Parser"])

# 許可されるファイルタイプ
ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}
ALLOWED_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
    'application/vnd.ms-excel',  # .xls
    'text/csv',  # .csv
    'application/csv'  # .csv
}

# ファイルサイズ制限（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

def detect_file_type(file: UploadFile) -> str:
    """ファイルの形式を判定する"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="ファイル名が指定されていません")
    
    # ファイル拡張子チェック
    file_extension = os.path.splitext(file.filename.lower())[1]
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"サポートされていないファイル形式です: {file_extension}"
        )
    
    # MIMEタイプチェック
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"サポートされていないMIMEタイプです: {file.content_type}"
        )
    
    # ファイルタイプを返す
    if file_extension == '.csv':
        return "csv"
    elif file_extension in ['.xlsx', '.xls']:
        return "excel"
    else:
        raise HTTPException(status_code=400, detail="未知のファイル形式です")

def validate_file_size(content: bytes) -> None:
    """ファイルサイズを検証する"""
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"ファイルサイズが大きすぎます（最大10MB）: {len(content)} bytes"
        )

async def process_csv(file_content: bytes, filename: str) -> Dict[str, Any]:
    """CSV ファイルを処理する（正規化されたファイルを想定）"""
    try:
        logger.info(f"Processing CSV file: {filename}")
        
        # CSVファイルを読み込み（1行目をヘッダーとして扱う）
        df = pd.read_csv(BytesIO(file_content))
        
        # 基本情報を取得
        columns = df.columns.tolist()
        total_rows = len(df)
        
        # データ型を推論
        data_types = {}
        for col in columns:
            dtype = str(df[col].dtype)
            # pandasのデータ型を簡潔な形式に変換
            if dtype.startswith('int'):
                data_types[col] = 'integer'
            elif dtype.startswith('float'):
                data_types[col] = 'number'
            elif dtype.startswith('bool'):
                data_types[col] = 'boolean'
            elif dtype.startswith('datetime'):
                data_types[col] = 'date'
            else:
                data_types[col] = 'string'
        
        # サンプルデータを取得（最初の5行）
        sample_data = df.head(5).to_dict('records')
        
        return {
            "file_type": "csv",
            "detected_header_row": 0,  # CSVは1行目（インデックス0）がヘッダー
            "columns": columns,
            "data_types": data_types,
            "sample_data": sample_data,
            "total_rows": total_rows
        }
        
    except Exception as e:
        logger.error(f"Error processing CSV file {filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"CSVファイルの処理中にエラーが発生しました: {str(e)}"
        )

async def process_excel(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Excel ファイルを処理する（非正規化ファイルを想定）"""
    try:
        logger.info(f"Processing Excel file: {filename}")
        
        # 現段階では基本的な読み込みのみ実装
        # 後でテーブル走査機能を追加予定
        df = pd.read_excel(BytesIO(file_content))
        
        # 基本情報を取得
        columns = df.columns.tolist()
        total_rows = len(df)
        
        # データ型を推論
        data_types = {}
        for col in columns:
            dtype = str(df[col].dtype)
            # pandasのデータ型を簡潔な形式に変換
            if dtype.startswith('int'):
                data_types[col] = 'integer'
            elif dtype.startswith('float'):
                data_types[col] = 'number'
            elif dtype.startswith('bool'):
                data_types[col] = 'boolean'
            elif dtype.startswith('datetime'):
                data_types[col] = 'date'
            else:
                data_types[col] = 'string'
        
        # サンプルデータを取得（最初の5行）
        sample_data = df.head(5).to_dict('records')
        
        return {
            "file_type": "excel",
            "detected_header_row": 0,  # 暫定的に0行目を設定（後で改善予定）
            "columns": columns,
            "data_types": data_types,
            "sample_data": sample_data,
            "total_rows": total_rows,
            "note": "Excel表走査機能は次段階で実装予定"
        }
        
    except Exception as e:
        logger.error(f"Error processing Excel file {filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Excelファイルの処理中にエラーが発生しました: {str(e)}"
        )

@router.post("/parse-excel")
async def parse_excel(file: UploadFile = File(...)):
    """Excel/CSVファイルを解析するエンドポイント"""
    try:
        # ファイル内容を読み取り
        file_content = await file.read()
        
        # ファイルサイズを検証
        validate_file_size(file_content)
        
        # ファイル形式を判定
        file_type = detect_file_type(file)
        
        # セッションIDを生成
        session_id = str(uuid.uuid4())
        
        logger.info(f"Processing file: {file.filename}, type: {file_type}, session: {session_id}")
        
        # ファイル形式に応じて処理を分岐
        if file_type == "csv":
            result = await process_csv(file_content, file.filename)
        elif file_type == "excel":
            result = await process_excel(file_content, file.filename)
        else:
            raise HTTPException(status_code=400, detail="サポートされていないファイル形式です")
        
        # セッションIDを結果に追加
        result["session_id"] = session_id
        result["filename"] = file.filename
        
        return {
            "status": "success",
            "message": "ファイルの解析が完了しました",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"ファイル処理中に予期しないエラーが発生しました: {str(e)}"
        )