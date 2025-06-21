from fastapi import APIRouter, UploadFile, File, HTTPException, Path
from typing import Dict, Any, Optional, List
import pandas as pd
import openpyxl
import uuid
import os
import logging
from io import BytesIO
from datetime import datetime, timedelta
import re
import numpy as np
from collections import Counter

# ログ設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/api", tags=["Excel Parser"])

# セッション管理用のグローバル変数
session_data: Dict[str, Dict[str, Any]] = {}
session_timestamps: Dict[str, datetime] = {}

# セッション有効期限（30分）
SESSION_TIMEOUT = timedelta(minutes=30)

class SessionData:
    """セッションデータを管理するクラス"""
    def __init__(self):
        self.raw_data: Optional[pd.DataFrame] = None
        self.processed_data: Optional[pd.DataFrame] = None
        self.analysis_result: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.file_info: Dict[str, Any] = {}

def cleanup_expired_sessions():
    """期限切れのセッションをクリーンアップ"""
    current_time = datetime.now()
    expired_sessions = []
    
    for session_id, timestamp in session_timestamps.items():
        if current_time - timestamp > SESSION_TIMEOUT:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        if session_id in session_data:
            del session_data[session_id]
        if session_id in session_timestamps:
            del session_timestamps[session_id]
        logger.info(f"Expired session cleaned up: {session_id}")
    
    return len(expired_sessions)

def get_session_data(session_id: str) -> Optional[Dict[str, Any]]:
    """セッションデータを取得"""
    cleanup_expired_sessions()
    
    if session_id not in session_data:
        return None
    
    # アクセス時刻を更新
    session_timestamps[session_id] = datetime.now()
    return session_data[session_id]

def create_session(session_id: str) -> Dict[str, Any]:
    """新しいセッションを作成"""
    cleanup_expired_sessions()
    
    session_data[session_id] = {
        'raw_data': None,
        'processed_data': None,
        'analysis_result': {},
        'metadata': {},
        'file_info': {}
    }
    session_timestamps[session_id] = datetime.now()
    return session_data[session_id]

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

def detect_header_row(df: pd.DataFrame) -> int:
    """CSVファイルのヘッダー行を検出する"""
    try:
        # 最初の10行を分析（ファイルが小さい場合は全行）
        max_rows_to_check = min(10, len(df))
        
        header_candidates = []
        
        for i in range(max_rows_to_check):
            row = df.iloc[i]
            
            # 空行をスキップ
            if row.isna().all() or (row == '').all():
                continue
            
            # 文字列データの割合を計算
            string_count = 0
            numeric_count = 0
            
            for value in row:
                if pd.isna(value) or value == '':
                    continue
                
                # 数値かどうかをチェック
                try:
                    float(str(value).replace(',', ''))
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
                header_candidates.append({
                    'row_index': i,
                    'string_ratio': string_ratio,
                    'total_values': total_values
                })
        
        # 最も文字列の割合が高い行をヘッダーとして選択
        if header_candidates:
            best_candidate = max(header_candidates, key=lambda x: x['string_ratio'])
            return best_candidate['row_index']
        
        # ヘッダー候補が見つからない場合は0行目を返す
        return 0
        
    except Exception as e:
        logger.warning(f"Header detection failed: {e}, using row 0 as default")
        return 0

def analyze_data_types(df: pd.DataFrame) -> Dict[str, str]:
    """データ型を詳細に分析する"""
    data_types = {}
    
    for col in df.columns:
        col_data = df[col].dropna()  # 欠損値を除外
        
        if len(col_data) == 0:
            data_types[col] = 'empty'
            continue
        
        # 数値型の判定
        numeric_count = 0
        date_count = 0
        boolean_count = 0
        
        for value in col_data:
            str_value = str(value).strip()
            
            # Boolean型チェック
            if str_value.lower() in ['true', 'false', 'yes', 'no', 'y', 'n', '1', '0']:
                boolean_count += 1
                continue
            
            # 数値型チェック（カンマ区切りの数値も考慮）
            try:
                float(str_value.replace(',', ''))
                numeric_count += 1
                continue
            except (ValueError, TypeError):
                pass
            
            # 日付型チェック
            date_patterns = [
                r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
                r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
                r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            ]
            
            for pattern in date_patterns:
                if re.match(pattern, str_value):
                    date_count += 1
                    break
        
        total_values = len(col_data)
        
        # データ型を決定（閾値: 80%）
        if boolean_count / total_values >= 0.8:
            data_types[col] = 'boolean'
        elif date_count / total_values >= 0.8:
            data_types[col] = 'date'
        elif numeric_count / total_values >= 0.8:
            # 整数か小数点数かを判定
            integer_count = 0
            for value in col_data:
                str_value = str(value).strip().replace(',', '')
                try:
                    float_val = float(str_value)
                    if float_val.is_integer():
                        integer_count += 1
                except (ValueError, TypeError):
                    pass
            
            if integer_count / numeric_count >= 0.9:
                data_types[col] = 'integer'
            else:
                data_types[col] = 'number'
        else:
            # カテゴリ型かどうかを判定
            unique_ratio = len(col_data.unique()) / total_values
            if unique_ratio <= 0.1 and len(col_data.unique()) <= 20:  # 重複が多くユニーク値が少ない
                data_types[col] = 'category'
            else:
                data_types[col] = 'string'
    
    return data_types

def get_excel_sheets_info(file_content: bytes) -> List[Dict[str, Any]]:
    """Excelファイルからシート情報を取得"""
    try:
        workbook = openpyxl.load_workbook(BytesIO(file_content), read_only=True)
        sheets_info = []
        
        for sheet_name in workbook.sheetnames:
            sheet = workbook[sheet_name]
            
            # シートの最大行・列を取得
            max_row = sheet.max_row
            max_col = sheet.max_column
            
            # データの有無を確認（最初の100行をサンプリング）
            has_data = False
            data_cells = 0
            sample_rows = min(100, max_row) if max_row else 0
            sample_cols = min(20, max_col) if max_col else 0
            
            if sample_rows > 0 and sample_cols > 0:
                for row in range(1, sample_rows + 1):
                    for col in range(1, sample_cols + 1):
                        cell_value = sheet.cell(row, col).value
                        if cell_value is not None and str(cell_value).strip() != '':
                            data_cells += 1
                            has_data = True
                
                # データ密度を計算
                total_sample_cells = sample_rows * sample_cols
                data_density = data_cells / total_sample_cells if total_sample_cells > 0 else 0
            else:
                data_density = 0
            
            # データ範囲を推定
            data_range = None
            if has_data and max_row > 0 and max_col > 0:
                end_col_letter = openpyxl.utils.get_column_letter(max_col)
                data_range = f"A1:{end_col_letter}{max_row}"
            
            sheet_info = {
                "name": sheet_name,
                "row_count": max_row if max_row else 0,
                "col_count": max_col if max_col else 0,
                "has_data": has_data,
                "data_range": data_range,
                "data_density": round(data_density, 3),
                "estimated_data_cells": data_cells
            }
            sheets_info.append(sheet_info)
        
        workbook.close()
        return sheets_info
        
    except Exception as e:
        logger.error(f"Error reading Excel sheets: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Excelファイルのシート情報取得中にエラーが発生しました: {str(e)}"
        )

def validate_excel_file(file: UploadFile) -> bool:
    """Excelファイルの妥当性をチェック"""
    if not file.filename:
        return False
    
    # ファイル拡張子チェック
    file_extension = os.path.splitext(file.filename.lower())[1]
    if file_extension not in ['.xlsx', '.xls']:
        return False
    
    # MIMEタイプチェック
    excel_mime_types = {
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.ms-excel',  # .xls
    }
    if file.content_type not in excel_mime_types:
        return False
    
    return True

def process_excel_sheets(file_content: bytes, filename: str, session_id: str) -> Dict[str, Any]:
    """Excelファイルのシート情報を処理してセッションに保存"""
    try:
        logger.info(f"Processing Excel sheets for file: {filename} (session: {session_id})")
        
        # セッションデータを作成
        session = create_session(session_id)
        
        # シート情報を取得
        sheets_info = get_excel_sheets_info(file_content)
        
        # ワークブックを保存（後でシート選択時に使用）
        workbook = openpyxl.load_workbook(BytesIO(file_content))
        
        # セッションにデータを保存
        session['file_info'] = {
            'filename': filename,
            'file_type': 'excel',
            'total_sheets': len(sheets_info),
            'sheets_info': sheets_info
        }
        
        # ワークブックデータも保存（バイト形式で保存）
        session['raw_workbook_data'] = file_content
        
        return {
            "filename": filename,
            "sheets": sheets_info,
            "total_sheets": len(sheets_info)
        }
        
    except Exception as e:
        logger.error(f"Error processing Excel file {filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Excelファイルの処理中にエラーが発生しました: {str(e)}"
        )

def analyze_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """データ品質を分析する"""
    quality_report = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'missing_data': {},
        'data_consistency': {},
        'statistics': {}
    }
    
    for col in df.columns:
        col_data = df[col]
        
        # 欠損値分析
        missing_count = col_data.isna().sum()
        missing_ratio = missing_count / len(col_data) if len(col_data) > 0 else 0
        
        quality_report['missing_data'][col] = {
            'count': int(missing_count),
            'ratio': float(missing_ratio)
        }
        
        # データ一貫性分析
        non_missing_data = col_data.dropna()
        if len(non_missing_data) > 0:
            unique_count = len(non_missing_data.unique())
            unique_ratio = unique_count / len(non_missing_data)
            
            quality_report['data_consistency'][col] = {
                'unique_values': int(unique_count),
                'unique_ratio': float(unique_ratio),
                'duplicates': int(len(non_missing_data) - unique_count)
            }
            
            # 数値列の統計情報
            try:
                numeric_data = pd.to_numeric(non_missing_data, errors='coerce').dropna()
                if len(numeric_data) > 0:
                    quality_report['statistics'][col] = {
                        'mean': float(numeric_data.mean()),
                        'median': float(numeric_data.median()),
                        'std': float(numeric_data.std()),
                        'min': float(numeric_data.min()),
                        'max': float(numeric_data.max())
                    }
            except Exception:
                pass  # 数値変換できない場合はスキップ
    
    return quality_report

async def process_csv_advanced(file_content: bytes, filename: str, session_id: str) -> Dict[str, Any]:
    """CSV ファイルを高度に解析する"""
    try:
        logger.info(f"Advanced processing CSV file: {filename} (session: {session_id})")
        
        # セッションデータを作成
        session = create_session(session_id)
        
        # CSVファイルを読み込み（ヘッダーなしで読み込んで後で判定）
        df_raw = pd.read_csv(BytesIO(file_content), header=None)
        
        # ヘッダー行を検出
        header_row = detect_header_row(df_raw)
        
        # ヘッダー行を使用してデータフレームを再構成
        if header_row > 0:
            # ヘッダー行より前の行を削除
            df_raw = df_raw.iloc[header_row:].reset_index(drop=True)
        
        # 1行目を列名として使用
        df = pd.read_csv(BytesIO(file_content), skiprows=header_row)
        
        # セッションにデータを保存
        session['raw_data'] = df_raw
        session['processed_data'] = df
        session['file_info'] = {
            'filename': filename,
            'file_type': 'csv',
            'detected_header_row': header_row,
            'total_rows': len(df),
            'total_columns': len(df.columns)
        }
        
        # 詳細なデータ型分析
        data_types = analyze_data_types(df)
        
        # データ品質分析
        quality_report = analyze_data_quality(df)
        
        # 分析結果をセッションに保存
        session['analysis_result'] = {
            'data_types': data_types,
            'quality_report': quality_report
        }
        
        # 基本情報を取得
        columns = df.columns.tolist()
        total_rows = len(df)
        
        # サンプルデータを取得（最初の5行）
        sample_data = df.head(5).fillna('').to_dict('records')
        
        return {
            "file_type": "csv",
            "detected_header_row": header_row,
            "columns": columns,
            "data_types": data_types,
            "sample_data": sample_data,
            "total_rows": total_rows,
            "quality_summary": {
                "missing_data_columns": len([col for col, info in quality_report['missing_data'].items() if info['ratio'] > 0]),
                "numeric_columns": len([col for col, dtype in data_types.items() if dtype in ['integer', 'number']]),
                "date_columns": len([col for col, dtype in data_types.items() if dtype == 'date']),
                "category_columns": len([col for col, dtype in data_types.items() if dtype == 'category'])
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing CSV file {filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"CSVファイルの処理中にエラーが発生しました: {str(e)}"
        )

# 後方互換性のため古い関数も残しておく
async def process_csv(file_content: bytes, filename: str) -> Dict[str, Any]:
    """CSV ファイルを処理する（シンプル版）"""
    session_id = str(uuid.uuid4())
    result = await process_csv_advanced(file_content, filename, session_id)
    return result

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
            result = await process_csv_advanced(file_content, file.filename, session_id)
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

@router.get("/session/{session_id}/data")
async def get_session_data_detail(session_id: str = Path(...)):
    """セッションの詳細データを取得"""
    session = get_session_data(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つからないか期限切れです")
    
    try:
        # DataFrameをJSON形式に変換
        processed_data = session.get('processed_data')
        if processed_data is not None:
            # 全データを返す（大きなファイルの場合は制限をかけることも可能）
            data_dict = processed_data.fillna('').to_dict('records')
            return {
                "status": "success",
                "session_id": session_id,
                "file_info": session.get('file_info', {}),
                "data": data_dict,
                "total_rows": len(data_dict)
            }
        else:
            raise HTTPException(status_code=404, detail="処理済みデータが見つかりません")
    
    except Exception as e:
        logger.error(f"Error retrieving session data {session_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"セッションデータの取得中にエラーが発生しました: {str(e)}"
        )

@router.get("/session/{session_id}/analysis")
async def get_session_analysis(session_id: str = Path(...)):
    """セッションの分析結果を取得"""
    session = get_session_data(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="セッションが見つからないか期限切れです")
    
    try:
        analysis_result = session.get('analysis_result', {})
        file_info = session.get('file_info', {})
        
        return {
            "status": "success",
            "session_id": session_id,
            "file_info": file_info,
            "analysis": analysis_result
        }
    
    except Exception as e:
        logger.error(f"Error retrieving session analysis {session_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"分析結果の取得中にエラーが発生しました: {str(e)}"
        )

@router.delete("/session/{session_id}")
async def delete_session(session_id: str = Path(...)):
    """セッションを削除"""
    if session_id in session_data:
        del session_data[session_id]
    if session_id in session_timestamps:
        del session_timestamps[session_id]
    
    logger.info(f"Session deleted: {session_id}")
    return {
        "status": "success",
        "message": f"セッション {session_id} が削除されました"
    }

@router.post("/parse-excel-sheets")
async def parse_excel_sheets(file: UploadFile = File(...)):
    """Excelファイルのシート一覧を取得するエンドポイント"""
    try:
        # Excelファイルの妥当性をチェック
        if not validate_excel_file(file):
            raise HTTPException(
                status_code=400,
                detail="サポートされていないファイル形式です。Excel形式（.xlsx, .xls）のファイルをアップロードしてください。"
            )
        
        # ファイル内容を読み取り
        file_content = await file.read()
        
        # ファイルサイズを検証
        validate_file_size(file_content)
        
        # セッションIDを生成
        session_id = str(uuid.uuid4())
        
        logger.info(f"Processing Excel sheets for: {file.filename}, session: {session_id}")
        
        # Excelシート情報を処理
        result = process_excel_sheets(file_content, file.filename, session_id)
        
        return {
            "status": "success",
            "message": "Excelファイルのシート一覧を取得しました",
            "session_id": session_id,
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing Excel file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Excelファイル処理中に予期しないエラーが発生しました: {str(e)}"
        )

@router.get("/sessions")
async def list_active_sessions():
    """アクティブなセッション一覧を取得"""
    cleanup_expired_sessions()
    
    sessions_info = []
    for session_id, timestamp in session_timestamps.items():
        session = session_data.get(session_id, {})
        file_info = session.get('file_info', {})
        
        sessions_info.append({
            "session_id": session_id,
            "created_at": timestamp.isoformat(),
            "filename": file_info.get('filename', 'Unknown'),
            "file_type": file_info.get('file_type', 'Unknown'),
            "total_rows": file_info.get('total_rows', 0),
            "total_columns": file_info.get('total_columns', 0),
            "total_sheets": file_info.get('total_sheets', 0)
        })
    
    return {
        "status": "success",
        "active_sessions": sessions_info,
        "total_count": len(sessions_info)
    }