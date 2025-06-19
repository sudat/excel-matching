"""
データベース接続と操作のユーティリティクラス
Supabaseクライアントを優先し、SQLAlchemyをフォールバックとして使用
"""

import os
from typing import Optional, Dict, Any, List
from supabase import create_client
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
        self.database_url = os.getenv("DATABASE_URL")
        
        # Supabaseクライアントの初期化
        if self.supabase_url and self.supabase_anon_key:
            self.supabase = create_client(self.supabase_url, self.supabase_anon_key)
        else:
            self.supabase = None
        
        # SQLAlchemyエンジンの初期化（フォールバック用）
        if self.database_url:
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={
                    "connect_timeout": 30,
                    "sslmode": "require"
                }
            )
        else:
            self.engine = None
    
    def test_connection(self) -> Dict[str, Any]:
        """接続テストを実行"""
        if self.supabase:
            try:
                # Supabaseクライアントでテスト
                response = self.supabase.table('business_requests').select('*').limit(1).execute()
                return {
                    "status": "success",
                    "method": "Supabase Client",
                    "url": self.supabase_url
                }
            except Exception as e:
                print(f"Supabase client test failed: {e}")
        
        if self.engine:
            try:
                with self.engine.connect() as connection:
                    result = connection.execute(text("SELECT 1"))
                    result.fetchone()
                    return {
                        "status": "success",
                        "method": "SQLAlchemy",
                        "url": self.database_url
                    }
            except Exception as e:
                print(f"SQLAlchemy test failed: {e}")
        
        return {
            "status": "failed",
            "method": "None",
            "error": "No working database connection available"
        }
    
    def create_business_request(self, title: str, description: Optional[str] = None) -> Dict[str, Any]:
        """新しいビジネスリクエストを作成"""
        if self.supabase:
            try:
                response = self.supabase.table('business_requests').insert({
                    'title': title,
                    'description': description,
                    'status': 'pending'
                }).execute()
                return {"status": "success", "data": response.data, "method": "Supabase"}
            except Exception as e:
                print(f"Supabase insert failed: {e}")
        
        if self.engine:
            try:
                with self.engine.connect() as connection:
                    result = connection.execute(text("""
                        INSERT INTO business_requests (title, description, status)
                        VALUES (:title, :description, 'pending')
                        RETURNING id, title, description, status, created_at
                    """), {"title": title, "description": description})
                    connection.commit()
                    row = result.fetchone()
                    return {
                        "status": "success",
                        "data": dict(row._mapping) if row else None,
                        "method": "SQLAlchemy"
                    }
            except Exception as e:
                print(f"SQLAlchemy insert failed: {e}")
        
        return {"status": "failed", "error": "No working database connection available"}
    
    def get_business_requests(self, limit: int = 100) -> Dict[str, Any]:
        """ビジネスリクエスト一覧を取得"""
        if self.supabase:
            try:
                response = self.supabase.table('business_requests').select('*').limit(limit).execute()
                return {"status": "success", "data": response.data, "method": "Supabase"}
            except Exception as e:
                print(f"Supabase select failed: {e}")
        
        if self.engine:
            try:
                with self.engine.connect() as connection:
                    result = connection.execute(text("""
                        SELECT id, title, description, status, created_at, updated_at
                        FROM business_requests
                        ORDER BY created_at DESC
                        LIMIT :limit
                    """), {"limit": limit})
                    rows = result.fetchall()
                    return {
                        "status": "success",
                        "data": [dict(row._mapping) for row in rows],
                        "method": "SQLAlchemy"
                    }
            except Exception as e:
                print(f"SQLAlchemy select failed: {e}")
        
        return {"status": "failed", "error": "No working database connection available"}
    
    def create_uploaded_file(self, business_request_id: str, filename: str, 
                           file_size: int, file_type: str, storage_path: str) -> Dict[str, Any]:
        """アップロードファイル情報を作成"""
        if self.supabase:
            try:
                response = self.supabase.table('uploaded_files').insert({
                    'business_request_id': business_request_id,
                    'original_filename': filename,
                    'file_size': file_size,
                    'file_type': file_type,
                    'storage_path': storage_path,
                    'upload_status': 'uploaded'
                }).execute()
                return {"status": "success", "data": response.data, "method": "Supabase"}
            except Exception as e:
                print(f"Supabase file insert failed: {e}")
        
        if self.engine:
            try:
                with self.engine.connect() as connection:
                    result = connection.execute(text("""
                        INSERT INTO uploaded_files 
                        (business_request_id, original_filename, file_size, file_type, storage_path, upload_status)
                        VALUES (:business_request_id, :filename, :file_size, :file_type, :storage_path, 'uploaded')
                        RETURNING id, business_request_id, original_filename, file_size, file_type, storage_path, upload_status, created_at
                    """), {
                        "business_request_id": business_request_id,
                        "filename": filename,
                        "file_size": file_size,
                        "file_type": file_type,
                        "storage_path": storage_path
                    })
                    connection.commit()
                    row = result.fetchone()
                    return {
                        "status": "success",
                        "data": dict(row._mapping) if row else None,
                        "method": "SQLAlchemy"
                    }
            except Exception as e:
                print(f"SQLAlchemy file insert failed: {e}")
        
        return {"status": "failed", "error": "No working database connection available"}

# グローバルインスタンス
db_manager = DatabaseManager()