from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
import os
import csv
import tempfile
from pathlib import Path
from datetime import datetime
import logging

# 必要なモジュールのインポート
from models.journal_entry import JournalEntry
from database import db_manager

# 環境変数とクライアント設定
from dotenv import load_dotenv
from supabase import create_client
from pinecone import Pinecone
import google.generativeai as genai

load_dotenv(Path(__file__).parent.parent.parent / ".env")

# ルーターの初期化
router = APIRouter(prefix="/api", tags=["journal-data"])

# 外部サービスクライアントの設定
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY")

# クライアント初期化
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY) if SUPABASE_URL and SUPABASE_ANON_KEY else None
pc = Pinecone(api_key=PINECONE_API_KEY) if PINECONE_API_KEY else None

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# ログ設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JournalDataRegistrationRequest(BaseModel):
    """会計仕訳データ登録リクエストモデル"""
    fiscal_year: int = Field(..., description="会計年度 (例: 2025)", ge=2000, le=2100)
    fiscal_month: int = Field(..., description="会計月 (1-12)", ge=1, le=12)
    overwrite: bool = Field(False, description="既存データの上書きを許可するか")


class JournalDataRegistrationResponse(BaseModel):
    """会計仕訳データ登録レスポンスモデル"""
    status: str
    message: str
    processed_count: int
    failed_count: int
    pinecone_index_name: str
    details: Optional[dict] = None


async def load_sample_journal_data() -> list[JournalEntry]:
    """サンプル仕訳データをCSVから読み込み"""
    csv_path = Path(__file__).parent.parent / "data" / "sample_journal_entries.csv"
    
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail=f"サンプルCSVファイルが見つかりません: {csv_path}")
    
    entries = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            # BOMを除去
            content = f.read()
            if content.startswith("\ufeff"):
                content = content[1:]
            
            # CSVを再度読み込み
            csv_reader = csv.DictReader(content.splitlines())
            
            for row in csv_reader:
                try:
                    entry = JournalEntry.from_csv_row(row)
                    entries.append(entry)
                except Exception as e:
                    logger.warning(f"CSVデータのパースに失敗: {row}, エラー: {e}")
                    continue
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSVファイルの読み込みに失敗: {str(e)}")
    
    return entries


async def save_entries_to_supabase(entries: list[JournalEntry], fiscal_year: int, fiscal_month: int, overwrite: bool) -> dict:
    """仕訳データをSupabaseに保存"""
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabaseクライアントが設定されていません")
    
    success_count = 0
    failed_count = 0
    
    try:
        # 上書きモードの場合、既存データを削除
        if overwrite:
            delete_response = supabase.table("journal_entries").delete().match({
                "fiscal_year": fiscal_year,
                "fiscal_month": fiscal_month
            }).execute()
            logger.info(f"既存データを削除しました: 年度={fiscal_year}, 月={fiscal_month}")
        
        # データを挿入
        for entry in entries:
            try:
                # Supabase用のデータ形式に変換
                supabase_data = {
                    "entry_date": entry.date.strftime("%Y-%m-%d"),
                    "amount": float(entry.total_amount),
                    "person": entry.customer_name or "",
                    "category": entry.account_name,
                    "description": entry.voucher_description,
                    "account_code": entry.account_code,
                    "department": entry.analysis_code_name or "",
                    "sub_account": entry.sub_account_name or "",
                    "partner": entry.customer_name or "",
                    "detail_description": entry.detail_description or "",
                    "original_data": entry.dict(),
                    "fiscal_year": fiscal_year,
                    "fiscal_month": fiscal_month,
                    "journal_number": entry.journal_number,
                    "debit_credit": entry.debit_credit,
                    "base_amount": float(entry.base_amount),
                    "tax_amount": float(entry.tax_amount),
                    "tax_category": entry.tax_category
                }
                
                insert_response = supabase.table("journal_entries").insert(supabase_data).execute()
                success_count += 1
                
            except Exception as e:
                logger.error(f"Supabaseへの挿入に失敗: {entry.journal_number}, エラー: {e}")
                failed_count += 1
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supabaseへの保存に失敗: {str(e)}")
    
    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "total_processed": len(entries)
    }


async def generate_embeddings_and_store_to_pinecone(entries: list[JournalEntry], fiscal_year: int, fiscal_month: int) -> dict:
    """エンベディングを生成してPineconeに保存"""
    if not pc:
        raise HTTPException(status_code=500, detail="Pineconeクライアントが設定されていません")
    
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini APIキーが設定されていません")
    
    index_name = "journal-entries"
    
    try:
        # インデックスの存在確認と作成
        existing_indexes = [index.name for index in pc.list_indexes()]
        
        if index_name not in existing_indexes:
            pc.create_index(
                name=index_name,
                dimension=768,  # Gemini text-embedding-004の次元数
                metric="cosine",
                spec={
                    "serverless": {
                        "cloud": "aws",
                        "region": "us-east-1"
                    }
                }
            )
            logger.info(f"Pineconeインデックス '{index_name}' を作成しました")
        
        # インデックスに接続
        index = pc.Index(index_name)
        
        # エンベディング生成とアップサート
        success_count = 0
        failed_count = 0
        
        for entry in entries:
            try:
                # テキスト形式に変換
                text_for_embedding = entry.to_text_for_embedding()
                
                # Geminiでエンベディング生成
                embedding_result = genai.embed_content(
                    model="models/text-embedding-004",
                    content=text_for_embedding
                )
                
                embedding_vector = embedding_result['embedding']
                
                # メタデータを準備
                metadata = entry.to_metadata_dict()
                metadata.update({
                    "fiscal_year": fiscal_year,
                    "fiscal_month": fiscal_month,
                    "text_content": text_for_embedding
                })
                
                # Pineconeにアップサート
                vector_id = f"{fiscal_year}_{fiscal_month}_{entry.journal_number}_{entry.line_number}"
                index.upsert([(vector_id, embedding_vector, metadata)])
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"エンベディング生成またはPinecone保存に失敗: {entry.journal_number}, エラー: {e}")
                failed_count += 1
        
        # インデックス統計情報を取得
        stats = index.describe_index_stats()
        
        return {
            "index_name": index_name,
            "success_count": success_count,
            "failed_count": failed_count,
            "total_vectors": stats.get("total_vector_count", 0),
            "index_stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pinecone処理に失敗: {str(e)}")


@router.post("/register-journal-data", response_model=JournalDataRegistrationResponse)
async def register_journal_data(
    request: JournalDataRegistrationRequest,
    background_tasks: BackgroundTasks
) -> JournalDataRegistrationResponse:
    """
    会計仕訳データを登録してPineconeベクトルストアを構築する
    
    指定された年月の会計データをSupabaseに保存し、
    Gemini 2.5 Flashでエンベディングを生成してPineconeに投入します。
    """
    logger.info(f"会計仕訳データ登録開始: 年度={request.fiscal_year}, 月={request.fiscal_month}, 上書き={request.overwrite}")
    
    try:
        # Step 1: サンプル仕訳データを読み込み
        logger.info("サンプル仕訳データを読み込み中...")
        entries = await load_sample_journal_data()
        logger.info(f"読み込み完了: {len(entries)}件の仕訳データ")
        
        if len(entries) == 0:
            raise HTTPException(status_code=400, detail="処理対象の仕訳データがありません")
        
        # Step 2: Supabaseに保存
        logger.info("Supabaseへのデータ保存を開始...")
        supabase_result = await save_entries_to_supabase(entries, request.fiscal_year, request.fiscal_month, request.overwrite)
        logger.info(f"Supabase保存完了: 成功={supabase_result['success_count']}, 失敗={supabase_result['failed_count']}")
        
        # Step 3: Pineconeにエンベディングを保存
        logger.info("Pineconeへのエンベディング保存を開始...")
        pinecone_result = await generate_embeddings_and_store_to_pinecone(entries, request.fiscal_year, request.fiscal_month)
        logger.info(f"Pinecone保存完了: 成功={pinecone_result['success_count']}, 失敗={pinecone_result['failed_count']}")
        
        # 成功レスポンスを構築
        total_success = min(supabase_result['success_count'], pinecone_result['success_count'])
        total_failed = max(supabase_result['failed_count'], pinecone_result['failed_count'])
        
        response = JournalDataRegistrationResponse(
            status="success" if total_failed == 0 else "partial_success",
            message=f"{request.fiscal_year}年{request.fiscal_month}月の会計仕訳データ登録とベクトルストア構築が完了しました",
            processed_count=total_success,
            failed_count=total_failed,
            pinecone_index_name=pinecone_result['index_name'],
            details={
                "supabase_result": supabase_result,
                "pinecone_result": pinecone_result,
                "fiscal_year": request.fiscal_year,
                "fiscal_month": request.fiscal_month,
                "overwrite_mode": request.overwrite
            }
        )
        
        logger.info(f"会計仕訳データ登録完了: ステータス={response.status}")
        return response
        
    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
    except Exception as e:
        logger.error(f"予期しないエラーが発生: {str(e)}")
        raise HTTPException(status_code=500, detail=f"処理中にエラーが発生しました: {str(e)}")


@router.get("/journal-data-status")
async def get_journal_data_status():
    """
    会計仕訳データの登録状況を確認する
    """
    try:
        status_info = {
            "supabase_connected": supabase is not None,
            "pinecone_connected": pc is not None,
            "gemini_configured": GEMINI_API_KEY is not None
        }
        
        # Pineconeインデックス情報を取得
        if pc:
            try:
                indexes = pc.list_indexes()
                journal_index_exists = any(index.name == "journal-entries" for index in indexes)
                status_info["pinecone_indexes"] = [index.name for index in indexes]
                status_info["journal_index_exists"] = journal_index_exists
                
                if journal_index_exists:
                    index = pc.Index("journal-entries")
                    stats = index.describe_index_stats()
                    status_info["journal_index_stats"] = stats
                    
            except Exception as e:
                status_info["pinecone_error"] = str(e)
        
        # Supabaseテーブル情報を取得
        if supabase:
            try:
                # journal_entriesテーブルの件数を取得
                response = supabase.table("journal_entries").select("*", count="exact").execute()
                status_info["supabase_journal_count"] = response.count
            except Exception as e:
                status_info["supabase_error"] = str(e)
        
        return {
            "status": "success",
            "data": status_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ステータス確認中にエラーが発生: {str(e)}")