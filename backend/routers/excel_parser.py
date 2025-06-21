from fastapi import APIRouter, UploadFile, File, HTTPException, Path
from typing import Dict, Any, Optional
import uuid
import logging
import urllib.parse
import pandas as pd

# 新しいモジュールからインポート
from models.table_models import TableCandidate
from services.table_detector import TableDetector, StatisticalTableDetector
from services.session_manager import SessionManager
from services.file_processor import FileProcessor
from services.file_validator import FileValidator
from services.data_analyzer import DataAnalyzer
from utils.excel_utils import extract_table_data

# ログ設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

router = APIRouter(prefix="/api", tags=["Excel Parser"])

# グローバルインスタンス
default_table_detector = StatisticalTableDetector()
session_manager = SessionManager()
file_processor = FileProcessor()
file_validator = FileValidator()
data_analyzer = DataAnalyzer()


@router.post("/parse-excel")
async def parse_excel(file: UploadFile = File(...)):
    """Excel/CSVファイルを解析するエンドポイント"""
    try:
        # ファイル内容を読み取り
        file_content = await file.read()

        # ファイルサイズを検証
        file_validator.validate_file_size(file_content)

        # ファイル形式を判定
        file_type = file_validator.detect_file_type(file)

        # セッションIDを生成
        session_id = str(uuid.uuid4())

        logger.info(
            f"Processing file: {file.filename}, type: {file_type}, session: {session_id}"
        )

        # ファイル形式に応じて処理を分岐
        filename = file.filename or "unknown_file"
        if file_type == "csv":
            result = await file_processor.process_csv_advanced(
                file_content, filename, session_id, session_manager
            )
        elif file_type == "excel":
            result = await file_processor.process_excel(file_content, filename)
        else:
            raise HTTPException(
                status_code=400, detail="サポートされていないファイル形式です"
            )

        # セッションIDを結果に追加
        result["session_id"] = session_id
        result["filename"] = file.filename

        return {
            "status": "success",
            "message": "ファイルの解析が完了しました",
            "data": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"ファイル処理中に予期しないエラーが発生しました: {str(e)}",
        )


@router.get("/session/{session_id}/data")
async def get_session_data_detail(session_id: str = Path(...)):
    """セッションの詳細データを取得"""
    session = session_manager.get_session_data(session_id)
    if not session:
        raise HTTPException(
            status_code=404, detail="セッションが見つからないか期限切れです"
        )

    try:
        # DataFrameをJSON形式に変換
        processed_data = session.get("processed_data")
        if processed_data is not None:
            # 全データを返す（大きなファイルの場合は制限をかけることも可能）
            data_dict = processed_data.fillna("").to_dict("records")
            return {
                "status": "success",
                "session_id": session_id,
                "file_info": session.get("file_info", {}),
                "data": data_dict,
                "total_rows": len(data_dict),
            }
        else:
            raise HTTPException(
                status_code=404, detail="処理済みデータが見つかりません"
            )

    except Exception as e:
        logger.error(f"Error retrieving session data {session_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"セッションデータの取得中にエラーが発生しました: {str(e)}",
        )


@router.get("/session/{session_id}/analysis")
async def get_session_analysis(session_id: str = Path(...)):
    """セッションの分析結果を取得"""
    session = session_manager.get_session_data(session_id)
    if not session:
        raise HTTPException(
            status_code=404, detail="セッションが見つからないか期限切れです"
        )

    try:
        analysis_result = session.get("analysis_result", {})
        file_info = session.get("file_info", {})

        return {
            "status": "success",
            "session_id": session_id,
            "file_info": file_info,
            "analysis": analysis_result,
        }

    except Exception as e:
        logger.error(f"Error retrieving session analysis {session_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"分析結果の取得中にエラーが発生しました: {str(e)}"
        )


@router.delete("/session/{session_id}")
async def delete_session(session_id: str = Path(...)):
    """セッションを削除"""
    session_manager.delete_session(session_id)

    logger.info(f"Session deleted: {session_id}")
    return {"status": "success", "message": f"セッション {session_id} が削除されました"}


@router.post("/parse-excel-sheets")
async def parse_excel_sheets(file: UploadFile = File(...)):
    """Excelファイルのシート一覧を取得するエンドポイント"""
    try:
        # Excelファイルの妥当性をチェック
        if not file_validator.validate_excel_file(file):
            raise HTTPException(
                status_code=400,
                detail="サポートされていないファイル形式です。Excel形式（.xlsx, .xls）のファイルをアップロードしてください。",
            )

        # ファイル内容を読み取り
        file_content = await file.read()

        # ファイルサイズを検証
        file_validator.validate_file_size(file_content)

        # セッションIDを生成
        session_id = str(uuid.uuid4())

        logger.info(
            f"Processing Excel sheets for: {file.filename}, session: {session_id}"
        )

        # Excelシート情報を処理
        filename = file.filename or "unknown_file.xlsx"
        result = file_processor.process_excel_sheets(
            file_content, filename, session_id, session_manager
        )

        return {
            "status": "success",
            "message": "Excelファイルのシート一覧を取得しました",
            "session_id": session_id,
            "data": result,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error processing Excel file {file.filename}: {str(e)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Excelファイル処理中に予期しないエラーが発生しました: {str(e)}",
        )


@router.get("/sessions")
async def list_active_sessions():
    """アクティブなセッション一覧を取得"""
    sessions_info = session_manager.list_active_sessions()

    return {
        "status": "success",
        "active_sessions": sessions_info,
        "total_count": len(sessions_info),
    }


@router.post("/excel-sheet-tables/{session_id}/{sheet_name}")
async def detect_tables_in_sheet(
    session_id: str = Path(...),
    sheet_name: str = Path(...),
    min_rows: int = 3,
    min_cols: int = 2,
    max_tables: int = 10,
):
    """指定されたシート内の表を検出するエンドポイント"""
    try:
        # セッションを取得
        session = session_manager.get_session_data(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail="セッションが見つからないか期限切れです"
            )

        # ワークブックデータを取得
        workbook_data = session.get("raw_workbook_data")
        if not workbook_data:
            raise HTTPException(
                status_code=404, detail="Excelワークブックデータが見つかりません"
            )

        # シート名をデコード（URLエンコードされている可能性があるため）
        decoded_sheet_name = urllib.parse.unquote(sheet_name)

        logger.info(
            f"Detecting tables in sheet '{decoded_sheet_name}' (session: {session_id})"
        )

        # 表検出を実行
        table_candidates = default_table_detector.detect_tables(
            workbook_data=workbook_data,
            sheet_name=decoded_sheet_name,
            min_rows=min_rows,
            min_cols=min_cols,
            max_tables=max_tables,
        )

        # 検出された表をセッションに保存
        session["detected_tables"] = {
            "sheet_name": decoded_sheet_name,
            "tables": [table.to_dict() for table in table_candidates],
            "detection_info": default_table_detector.get_detector_info(),
            "detection_time": session_manager.get_current_time().isoformat(),
        }

        # レスポンスデータを構築
        response_data = {
            "sheet_name": decoded_sheet_name,
            "total_tables": len(table_candidates),
            "tables": [table.to_dict() for table in table_candidates],
            "detection_info": default_table_detector.get_detector_info(),
        }

        return {
            "status": "success",
            "message": f"シート '{decoded_sheet_name}' で {len(table_candidates)} 個の表を検出しました",
            "session_id": session_id,
            "data": response_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error detecting tables in sheet {sheet_name} (session: {session_id}): {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"表検出中にエラーが発生しました: {str(e)}"
        )


@router.post("/select-table/{session_id}/{table_id}")
async def select_table(session_id: str = Path(...), table_id: str = Path(...)):
    """選択された表のデータを取得し、最終処理を行うエンドポイント"""
    try:
        # セッションを取得
        session = session_manager.get_session_data(session_id)
        if not session:
            raise HTTPException(
                status_code=404, detail="セッションが見つからないか期限切れです"
            )

        # 検出済み表データを取得
        detected_tables = session.get("detected_tables")
        if not detected_tables:
            raise HTTPException(
                status_code=404, detail="検出済み表データが見つかりません"
            )

        # 指定された表を探す
        selected_table = None
        for table_data in detected_tables["tables"]:
            if table_data["table_id"] == table_id:
                selected_table = table_data
                break

        if not selected_table:
            raise HTTPException(
                status_code=404, detail=f"表ID '{table_id}' が見つかりません"
            )

        # ワークブックデータから指定範囲のデータを抽出
        workbook_data = session.get("raw_workbook_data")
        if not workbook_data:
            raise HTTPException(
                status_code=404, detail="Excelワークブックデータが見つかりません"
            )

        # 表の全データを取得
        full_table_data = extract_table_data(
            workbook_data, detected_tables["sheet_name"], selected_table
        )

        # データ型分析と品質分析を実行
        if full_table_data["records"]:
            import pandas as pd

            df = pd.DataFrame(full_table_data["records"])
            full_table_data["data_types"] = data_analyzer.analyze_data_types(df)
            full_table_data["quality_info"] = data_analyzer.analyze_data_quality(df)

        # セッションに最終データを保存
        session["selected_table"] = {
            "table_info": selected_table,
            "full_data": full_table_data,
            "selection_time": session_manager.get_current_time().isoformat(),
        }

        # ファイル情報を更新
        file_info = session.get("file_info", {})
        file_info.update(
            {
                "selected_sheet": detected_tables["sheet_name"],
                "selected_table_id": table_id,
                "final_rows": len(full_table_data["records"]),
                "final_columns": len(full_table_data["headers"]),
            }
        )
        session["file_info"] = file_info

        return {
            "status": "success",
            "message": f"表 '{table_id}' を選択しました",
            "session_id": session_id,
            "data": {
                "table_info": selected_table,
                "headers": full_table_data["headers"],
                "total_records": len(full_table_data["records"]),
                "sample_records": full_table_data["records"][:10],  # 最初の10件のみ
                "data_types": full_table_data.get("data_types", {}),
                "quality_info": full_table_data.get("quality_info", {}),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error selecting table {table_id} (session: {session_id}): {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"表選択中にエラーが発生しました: {str(e)}"
        )


# 後方互換性のため、シンプルなCSV処理関数を残しておく
async def process_csv(file_content: bytes, filename: str) -> Dict[str, Any]:
    """CSV ファイルを処理する（シンプル版）"""
    session_id = str(uuid.uuid4())
    result = await file_processor.process_csv_advanced(
        file_content, filename, session_id, session_manager
    )
    return result
