from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from pinecone import Pinecone
from routers import upload, excel_parser
from database import db_manager
import os
import psycopg2
import time
from urllib.parse import urlparse
from supabase import create_client
from typing import cast, Any

# 環境変数を読み込み
load_dotenv()

# 型チェックのためのAnyタイプ（import時の問題を回避）
# Supabaseライブラリの型定義が不完全または見つからない場合にAnyを使用
CountMethodType = Any

# データベース接続の設定
DATABASE_URL = os.getenv("DATABASE_URL")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

if DATABASE_URL:
    # 接続プールとタイムアウトの設定を追加
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # 接続の有効性をチェック
        pool_recycle=300,    # 5分で接続をリサイクル
        connect_args={
            "connect_timeout": 30,  # 接続タイムアウト30秒
            "sslmode": "require"    # SSL接続を必須に
        },
        echo=True  # デバッグ用にSQLを出力
    )
else:
    engine = None

# Supabaseクライアントの設定
if SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
else:
    supabase = None

# Pinecone接続の設定
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if PINECONE_API_KEY:
    pc = Pinecone(api_key=PINECONE_API_KEY)
else:
    pc = None

app = FastAPI(
    title="Excel Matching API",
    description="Excel file matching and analysis API",
    version="1.0.0"
)

# CORSの設定（フロントエンドからのアクセスを許可）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],  # Next.jsのポート
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターを追加
app.include_router(upload.router)
app.include_router(excel_parser.router)

@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {"message": "Excel Matching API is running"}

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "ok", "message": "Server is healthy"}

@app.get("/db-test")
async def test_database_connection():
    """データベース接続テストエンドポイント（Supabaseクライアント優先）"""
    # まずSupabaseクライアントを試す
    if supabase:
        try:
            # Supabaseクライアントでテスト（型チェックを無視）
            response = supabase.table('business_requests').select('*', count=cast(CountMethodType, 'exact')).execute()
            files_response = supabase.table('uploaded_files').select('*', count=cast(CountMethodType, 'exact')).execute()
            
            return {
                "status": "success",
                "message": "Database connection successful (Supabase Client)",
                "connection_method": "Supabase Python Client",
                "business_requests_count": response.count,
                "uploaded_files_count": files_response.count,
                "supabase_url": SUPABASE_URL
            }
        except Exception as supabase_error:
            print(f"Supabase client failed: {supabase_error}")
            # Supabaseクライアントが失敗した場合はSQLAlchemyを試す
            pass
    
    # SQLAlchemyでの接続テスト（フォールバック）
    if not engine:
        raise HTTPException(status_code=500, detail="Neither Supabase client nor database engine configured")
    
    try:
        print(f"Attempting SQLAlchemy connection at: {time.time()}")
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            
            if row is None:
                raise Exception("No result returned from test query")
            
            test_value = row[0]
            
            # テーブル存在確認
            table_check = connection.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('business_requests', 'uploaded_files')
            """))
            tables = [row[0] for row in table_check.fetchall()]
            
            return {
                "status": "success",
                "message": "Database connection successful (SQLAlchemy)",
                "connection_method": "SQLAlchemy",
                "test_query_result": test_value,
                "available_tables": tables
            }
    except Exception as e:
        error_msg = f"All database connection methods failed. SQLAlchemy error: {str(e)}"
        print(f"Error at: {time.time()} - {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@app.get("/db-test-direct")
async def test_database_connection_direct():
    """psycopg2を使った直接データベース接続テスト"""
    if not DATABASE_URL:
        raise HTTPException(status_code=500, detail="Database URL not configured")
    
    try:
        print(f"Attempting direct connection to database at: {time.time()}")
        
        # URL解析
        parsed = urlparse(DATABASE_URL)
        
        # psycopg2で直接接続
        connection = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # "/"を除去
            user=parsed.username,
            password=parsed.password,
            connect_timeout=30,
            sslmode='require'
        )
        
        print(f"Direct connection established at: {time.time()}")
        
        cursor = connection.cursor()
        
        # 基本テストクエリ
        cursor.execute("SELECT 1 as test")
        result = cursor.fetchone()
        test_value = result[0] if result else None
        
        # テーブル存在確認
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('business_requests', 'uploaded_files')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        # データベース情報取得
        cursor.execute("SELECT version()")
        version_result = cursor.fetchone()
        db_version = version_result[0] if version_result else "Unknown"
        
        cursor.close()
        connection.close()
        
        print(f"Direct query completed at: {time.time()}")
        
        return {
            "status": "success",
            "message": "Direct database connection successful",
            "test_query_result": test_value,
            "available_tables": tables,
            "database_version": db_version,
            "connection_info": {
                "host": parsed.hostname,
                "port": parsed.port,
                "database": parsed.path[1:],
                "user": parsed.username
            }
        }
        
    except Exception as e:
        error_msg = f"Direct database connection failed: {str(e)}"
        print(f"Direct connection error at: {time.time()} - {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@app.get("/db-test-supabase")
async def test_database_connection_supabase():
    """Supabaseクライアントを使った接続テスト"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client not configured")
    
    try:
        print(f"Attempting Supabase client connection at: {time.time()}")
        
        # テーブル一覧取得でテスト（型チェックを無視）
        response = supabase.table('business_requests').select('*', count=cast(CountMethodType, 'exact')).execute()
        print(f"Supabase query completed at: {time.time()}")
        
        # uploaded_filesテーブルも確認
        files_response = supabase.table('uploaded_files').select('*', count=cast(CountMethodType, 'exact')).execute()
        
        return {
            "status": "success",
            "message": "Supabase client connection successful",
            "business_requests_count": response.count,
            "uploaded_files_count": files_response.count,
            "supabase_url": SUPABASE_URL,
            "connection_method": "Supabase Python Client"
        }
        
    except Exception as e:
        error_msg = f"Supabase client connection failed: {str(e)}"
        print(f"Supabase connection error at: {time.time()} - {error_msg}")
        raise HTTPException(
            status_code=500,
            detail=error_msg
        )

@app.get("/pinecone-test")
async def test_pinecone_connection():
    """Pinecone接続テストエンドポイント"""
    if not pc:
        raise HTTPException(status_code=500, detail="Pinecone API key not configured")
    
    try:
        # インデックス一覧を取得して接続確認
        indexes = pc.list_indexes()
        return {
            "status": "success",
            "message": "Pinecone connection successful",
            "available_indexes": [index.name for index in indexes]
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Pinecone connection failed: {str(e)}"
        )

@app.get("/db-simple-test")
async def simple_database_test():
    """シンプルなデータベース接続テスト"""
    result = db_manager.test_connection()
    if result["status"] == "success":
        return result
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Database connection failed"))

@app.get("/business-requests")
async def get_business_requests():
    """ビジネスリクエスト一覧取得"""
    result = db_manager.get_business_requests()
    if result["status"] == "success":
        return {
            "status": "success",
            "data": result["data"],
            "method": result["method"]
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to fetch business requests"))

@app.post("/business-requests")
async def create_business_request(title: str, description: str = ""):
    """新しいビジネスリクエストを作成"""
    desc = description if description else None
    result = db_manager.create_business_request(title, desc)
    if result["status"] == "success":
        return {
            "status": "success",
            "data": result["data"],
            "method": result["method"]
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to create business request"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)