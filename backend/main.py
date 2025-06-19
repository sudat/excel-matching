from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from pinecone import Pinecone
from routers import upload
import os

# 環境変数を読み込み
load_dotenv()

# データベース接続の設定
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    engine = None

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
    allow_origins=["http://localhost:3000", "http://localhost:3002"],  # Next.jsのポート
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターを追加
app.include_router(upload.router)

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
    """データベース接続テストエンドポイント"""
    if not engine:
        raise HTTPException(status_code=500, detail="Database URL not configured")
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            return {
                "status": "success",
                "message": "Database connection successful",
                "test_query_result": test_value
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database connection failed: {str(e)}"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)