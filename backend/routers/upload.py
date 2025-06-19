from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
from sqlalchemy import create_engine, text
from supabase import create_client, Client
import os
import uuid
from datetime import datetime
import mimetypes

router = APIRouter(prefix="/upload", tags=["File Upload"])

# 環境変数からSupabase設定を取得
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

if SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
else:
    supabase = None

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
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
    
    # ファイル検証
    for file in files:
        if not validate_file(file):
            raise HTTPException(
                status_code=400, 
                detail=f"サポートされていないファイル形式です: {file.filename}"
            )
        
        # ファイルサイズチェック（実際の内容をチェック）
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"ファイルサイズが大きすぎます（最大10MB）: {file.filename}"
            )
        
        # ファイルポインタをリセット
        await file.seek(0)
    
    try:
        # 1. 業務依頼をデータベースに保存
        business_request_id = str(uuid.uuid4())
        
        with engine.connect() as connection:
            connection.execute(
                text("""
                INSERT INTO business_requests (id, title, description, status)
                VALUES (:id, :title, :description, 'pending')
                """),
                {
                    "id": business_request_id,
                    "title": title,
                    "description": description
                }
            )
            connection.commit()
        
        uploaded_files = []
        
        # 2. 各ファイルをSupabase Storageにアップロード
        for file in files:
            # ファイル内容を読み取り
            file_content = await file.read()
            
            # ストレージパスを生成（業務依頼ID/ファイル名）
            storage_path = f"{business_request_id}/{file.filename}"
            
            # Supabase Storageにアップロード
            storage_response = supabase.storage.from_("uploaded-files").upload(
                path=storage_path,
                file=file_content,
                file_options={"content-type": file.content_type}
            )
            
            if storage_response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=500,
                    detail=f"ファイルアップロードに失敗しました: {file.filename}"
                )
            
            # 3. ファイルメタデータをデータベースに保存
            file_id = str(uuid.uuid4())
            
            with engine.connect() as connection:
                connection.execute(
                    text("""
                    INSERT INTO uploaded_files 
                    (id, business_request_id, original_filename, file_size, file_type, storage_path, upload_status)
                    VALUES (:id, :business_request_id, :filename, :file_size, :file_type, :storage_path, 'uploaded')
                    """),
                    {
                        "id": file_id,
                        "business_request_id": business_request_id,
                        "filename": file.filename,
                        "file_size": len(file_content),
                        "file_type": file.content_type,
                        "storage_path": storage_path
                    }
                )
                connection.commit()
            
            uploaded_files.append({
                "file_id": file_id,
                "filename": file.filename,
                "file_size": len(file_content),
                "file_type": file.content_type,
                "storage_path": storage_path
            })
            
            # ファイルポインタをリセット（念のため）
            await file.seek(0)
        
        return {
            "status": "success",
            "message": "業務依頼とファイルアップロードが完了しました",
            "business_request_id": business_request_id,
            "uploaded_files": uploaded_files,
            "total_files": len(uploaded_files)
        }
        
    except Exception as e:
        # エラーが発生した場合、可能な限りクリーンアップ
        try:
            # アップロード済みファイルをStorageから削除
            for file in files:
                storage_path = f"{business_request_id}/{file.filename}"
                supabase.storage.from_("uploaded-files").remove([storage_path])
            
            # データベースから業務依頼を削除
            with engine.connect() as connection:
                connection.execute(
                    text("DELETE FROM business_requests WHERE id = :id"),
                    {"id": business_request_id}
                )
                connection.commit()
        except:
            pass  # クリーンアップエラーは無視
        
        raise HTTPException(
            status_code=500,
            detail=f"アップロード処理中にエラーが発生しました: {str(e)}"
        )

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