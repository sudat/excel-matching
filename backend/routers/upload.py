from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional, cast, Any
from sqlalchemy import create_engine, text
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime
import asyncio
import logging
import time

# 環境変数を読み込み
load_dotenv()

# 型チェックのためのAnyタイプ（import時の問題を回避）
# Supabaseライブラリの型定義が不完全または見つからない場合にAnyを使用
FileOptionsType = Any

router = APIRouter(prefix="/upload", tags=["File Upload"])

# ログ設定
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 環境変数からSupabase設定を取得
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Supabaseクライアントの型定義を修正
supabase: Optional[Client] = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

if DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,
        echo=False  # デバッグ時はTrueに変更可能
    )
else:
    engine = None

# 許可されるファイルタイプ
ALLOWED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}
ALLOWED_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
    'application/vnd.ms-excel',  # .xls
    'text/csv',  # .csv
    'application/csv'  # .csv
}

def sanitize_filename(filename: str) -> str:
    """ファイル名をSupabase Storage対応形式に変換（日本語文字対応）"""
    import re
    import os
    from datetime import datetime
    
    # ファイル名と拡張子を分離
    name, ext = os.path.splitext(filename)
    
    # 日本語文字やSupabaseで許可されていない文字を削除/置換
    # 許可される文字: 英数字（a-z, A-Z, 0-9）、アンダースコア、ハイフンのみ
    sanitized_name = re.sub(r'[^a-zA-Z0-9\-_]', '_', name)
    
    # 連続するアンダースコアを単一に
    sanitized_name = re.sub(r'_+', '_', sanitized_name)
    
    # 先頭末尾のアンダースコアを削除
    sanitized_name = sanitized_name.strip('_')
    
    # 空になった場合はタイムスタンプを使用
    if not sanitized_name or sanitized_name == '':
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sanitized_name = f"file_{timestamp}"
    
    return f"{sanitized_name}{ext}"

# ファイルサイズ制限（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes

def validate_file(file: UploadFile) -> bool:
    """ファイルの検証"""
    # ファイル拡張子チェック
    file_extension = os.path.splitext(file.filename.lower())[1] if file.filename else ""
    if file_extension not in ALLOWED_EXTENSIONS:
        return False
    
    # MIMEタイプチェック
    if file.content_type not in ALLOWED_MIME_TYPES:
        return False
    
    return True

@router.post("/business-request")
async def create_business_request_with_files(
    title: str = Form(...),
    description: Optional[str] = Form(None),
    files: List[UploadFile] = File(...)
):
    """業務依頼とファイルアップロードを一括処理"""
    if not supabase or not engine:
        raise HTTPException(status_code=500, detail="Database or Supabase not configured")
    
    # ファイル数制限チェック（最大5ファイル）
    if len(files) > 5:
        raise HTTPException(status_code=400, detail="最大5ファイルまでアップロード可能です")
    
    # ファイル検証とコンテンツ読み取りを一括実行
    file_data = []
    for file in files:
        if not validate_file(file):
            raise HTTPException(
                status_code=400, 
                detail=f"サポートされていないファイル形式です: {file.filename}"
            )
        
        # ファイル内容を一度だけ読み取り
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"ファイルサイズが大きすぎます（最大10MB）: {file.filename}"
            )
        
        file_data.append({
            "file": file,
            "content": file_content,
            "size": len(file_content)
        })
    
    business_request_id = str(uuid.uuid4())
    uploaded_files = []
    uploaded_storage_paths = []  # クリーンアップ用
    
    try:
        # 1. 業務依頼をデータベースに保存（Supabaseクライアント使用）
        # 型チェックを無視してSupabaseクライアントを使用
        supabase_client = cast(Client, supabase)
        
        business_request_response = supabase_client.table('business_requests').insert({
            "id": business_request_id,
            "title": title,
            "description": description,
            "status": "pending"
        }).execute()
        
        if not business_request_response.data:
            raise HTTPException(status_code=500, detail="Failed to create business request")
        
        # 2. ファイルアップロードとメタデータ保存
        logger.info(f"Starting file upload for request {business_request_id}, {len(file_data)} files")
        
        async def upload_single_file(file_info):
            file = file_info["file"]
            content = file_info["content"]
            size = file_info["size"]
            
            # 元のファイル名をサニタイズしてStorage用ファイル名を生成
            original_filename = file.filename
            sanitized_filename = sanitize_filename(original_filename)
            
            # ストレージパスを生成（サニタイズされたファイル名を使用）
            storage_path = f"{business_request_id}/{sanitized_filename}"
            
            try:
                logger.info(f"Starting upload for {original_filename} -> {sanitized_filename} ({size} bytes)")
                start_time = time.time()
                
                # Supabase Storageにアップロード（タイムアウト時間を60秒に延長）
                # 型チェックを無視してSupabaseクライアントを使用
                storage_response = await asyncio.wait_for(
                    asyncio.to_thread(
                        lambda: supabase_client.storage.from_("uploaded-files").upload(
                            path=storage_path,
                            file=content,
                            file_options=cast(FileOptionsType, {"content-type": file.content_type, "upsert": False})
                        )
                    ),
                    timeout=60.0  # タイムアウトを60秒に延長
                )
                
                upload_time = time.time() - start_time
                logger.info(f"Upload completed for {original_filename} in {upload_time:.2f}s")
                
                return {
                    "success": True,
                    "file_id": str(uuid.uuid4()),
                    "original_filename": original_filename,  # 元のファイル名
                    "sanitized_filename": sanitized_filename,  # サニタイズ後のファイル名
                    "filename": original_filename,  # 後方互換性のため
                    "file_size": size,
                    "file_type": file.content_type,
                    "storage_path": storage_path,
                    "content": content
                }
            except asyncio.TimeoutError:
                logger.error(f"Upload timeout for {original_filename}")
                return {
                    "success": False,
                    "filename": original_filename,
                    "error": "Upload timeout (60s)"
                }
            except Exception as e:
                logger.error(f"Upload error for {original_filename}: {str(e)}")
                return {
                    "success": False,
                    "filename": original_filename,
                    "error": str(e)
                }
        
        # 並列アップロード実行（最大2つまで同時実行に調整）
        semaphore = asyncio.Semaphore(2)  # 同時実行数を減らして安定性向上
        
        async def upload_with_semaphore(file_info):
            async with semaphore:
                return await upload_single_file(file_info)
        
        logger.info(f"Starting parallel upload with semaphore (max 2 concurrent)")
        total_start_time = time.time()
        
        upload_results = await asyncio.gather(
            *[upload_with_semaphore(file_info) for file_info in file_data]
        )
        
        total_upload_time = time.time() - total_start_time
        logger.info(f"All uploads completed in {total_upload_time:.2f}s")
        
        # アップロード結果をチェック
        failed_uploads = [result for result in upload_results if not result["success"]]
        if failed_uploads:
            error_details = ", ".join([f"{result['filename']}: {result['error']}" for result in failed_uploads])
            raise Exception(f"ファイルアップロードに失敗しました: {error_details}")
        
        # 成功したアップロードのストレージパスを記録
        uploaded_storage_paths = [result["storage_path"] for result in upload_results if result["success"]]
        
        # 3. データベースにファイルメタデータを一括保存（Supabaseクライアント使用）
        file_records = []
        for result in upload_results:
            if result["success"]:
                file_record = {
                    "id": result["file_id"],
                    "business_request_id": business_request_id,
                    "original_filename": result["original_filename"],  # 元のファイル名（表示用）
                    "file_size": result["file_size"],
                    "file_type": result["file_type"],
                    "storage_path": result["storage_path"],  # サニタイズ後のファイル名を含むパス
                    "upload_status": "uploaded"
                }
                file_records.append(file_record)
                
                uploaded_files.append({
                    "file_id": result["file_id"],
                    "original_filename": result["original_filename"],  # 元のファイル名
                    "sanitized_filename": result["sanitized_filename"],  # サニタイズ後のファイル名
                    "filename": result["original_filename"],  # 後方互換性のため
                    "file_size": result["file_size"],
                    "file_type": result["file_type"],
                    "storage_path": result["storage_path"]
                })
        
        # 一括データベース挿入（Supabaseクライアント使用）
        if file_records:
            files_response = supabase_client.table('uploaded_files').insert(file_records).execute()
            if not files_response.data:
                raise HTTPException(status_code=500, detail="Failed to save file metadata")
        
        return {
            "status": "success",
            "message": "業務依頼とファイルアップロードが完了しました",
            "business_request_id": business_request_id,
            "uploaded_files": uploaded_files,
            "total_files": len(uploaded_files)
        }
        
    except Exception as e:
        # エラーが発生した場合のクリーンアップ（効率化）
        cleanup_errors = []
        
        try:
            # アップロード済みファイルをStorageから削除（復活）
            if uploaded_storage_paths and supabase:
                logger.info(f"Cleaning up {len(uploaded_storage_paths)} files from Storage")
                supabase_client = cast(Client, supabase)
                remove_response = supabase_client.storage.from_("uploaded-files").remove(uploaded_storage_paths)
                logger.info(f"Storage cleanup response: {remove_response}")
        except Exception as cleanup_e:
            cleanup_errors.append(f"Storage cleanup error: {str(cleanup_e)}")
        
        try:
            # データベースから業務依頼とファイル記録を削除（Supabaseクライアント使用）
            if supabase:
                supabase_client = cast(Client, supabase)
                # 関連ファイル記録を削除
                supabase_client.table('uploaded_files').delete().eq('business_request_id', business_request_id).execute()
                # 業務依頼を削除
                supabase_client.table('business_requests').delete().eq('id', business_request_id).execute()
        except Exception as cleanup_e:
            cleanup_errors.append(f"Database cleanup error: {str(cleanup_e)}")
        
        error_message = f"アップロード処理中にエラーが発生しました: {str(e)}"
        if cleanup_errors:
            error_message += f" (クリーンアップエラー: {'; '.join(cleanup_errors)})"
        
        raise HTTPException(status_code=500, detail=error_message)

@router.get("/business-request/{business_request_id}")
async def get_business_request_files(business_request_id: str):
    """業務依頼に関連するファイル一覧を取得"""
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        with engine.connect() as connection:
            # 業務依頼情報を取得
            business_request = connection.execute(
                text("SELECT * FROM business_requests WHERE id = :id"),
                {"id": business_request_id}
            ).fetchone()
            
            if not business_request:
                raise HTTPException(status_code=404, detail="業務依頼が見つかりません")
            
            # 関連ファイル一覧を取得
            files = connection.execute(
                text("""
                SELECT * FROM uploaded_files 
                WHERE business_request_id = :business_request_id 
                ORDER BY created_at
                """),
                {"business_request_id": business_request_id}
            ).fetchall()
            
            return {
                "business_request": {
                    "id": business_request.id,
                    "title": business_request.title,
                    "description": business_request.description,
                    "status": business_request.status,
                    "created_at": business_request.created_at.isoformat(),
                    "updated_at": business_request.updated_at.isoformat()
                },
                "files": [
                    {
                        "id": file.id,
                        "original_filename": file.original_filename,
                        "file_size": file.file_size,
                        "file_type": file.file_type,
                        "storage_path": file.storage_path,
                        "upload_status": file.upload_status,
                        "created_at": file.created_at.isoformat(),
                        "updated_at": file.updated_at.isoformat()
                    }
                    for file in files
                ]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"データ取得中にエラーが発生しました: {str(e)}"
        )

@router.get("/upload-progress/{business_request_id}")
async def get_upload_progress(business_request_id: str):
    """アップロード進行状況を取得"""
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        with engine.connect() as connection:
            # 業務依頼の状態を確認
            business_request = connection.execute(
                text("SELECT status, created_at FROM business_requests WHERE id = :id"),
                {"id": business_request_id}
            ).fetchone()
            
            if not business_request:
                raise HTTPException(status_code=404, detail="業務依頼が見つかりません")
            
            # アップロード済みファイル数を取得
            file_count = connection.execute(
                text("""
                SELECT COUNT(*) as total_files,
                       COUNT(CASE WHEN upload_status = 'uploaded' THEN 1 END) as uploaded_files,
                       COUNT(CASE WHEN upload_status = 'failed' THEN 1 END) as failed_files
                FROM uploaded_files 
                WHERE business_request_id = :business_request_id
                """),
                {"business_request_id": business_request_id}
            ).fetchone()
            
            # 進行率を計算
            total_files = getattr(file_count, 'total_files', 0) or 0
            uploaded_files = getattr(file_count, 'uploaded_files', 0) or 0
            failed_files = getattr(file_count, 'failed_files', 0) or 0
            
            if total_files > 0:
                progress_percentage = (uploaded_files / total_files) * 100
            else:
                progress_percentage = 0
            
            return {
                "business_request_id": business_request_id,
                "status": business_request.status,
                "progress_percentage": round(progress_percentage, 2),
                "total_files": total_files,
                "uploaded_files": uploaded_files,
                "failed_files": failed_files,
                "created_at": business_request.created_at.isoformat()
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"データ取得中にエラーが発生しました: {str(e)}"
        )

@router.get("/business-requests")
async def list_business_requests():
    """業務依頼一覧を取得"""
    if not engine:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    try:
        with engine.connect() as connection:
            requests = connection.execute(
                text("""
                SELECT br.*, COUNT(uf.id) as file_count
                FROM business_requests br
                LEFT JOIN uploaded_files uf ON br.id = uf.business_request_id
                GROUP BY br.id, br.title, br.description, br.status, br.created_at, br.updated_at
                ORDER BY br.created_at DESC
                """)
            ).fetchall()
            
            return {
                "business_requests": [
                    {
                        "id": req.id,
                        "title": req.title,
                        "description": req.description,
                        "status": req.status,
                        "file_count": req.file_count,
                        "created_at": req.created_at.isoformat(),
                        "updated_at": req.updated_at.isoformat()
                    }
                    for req in requests
                ]
            }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"データ取得中にエラーが発生しました: {str(e)}"
        )