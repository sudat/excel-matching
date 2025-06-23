from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
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
supabase = (
    create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    if SUPABASE_URL and SUPABASE_ANON_KEY
    else None
)
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
    details: Optional[Dict[str, Any]] = None
    data_exists: Optional[bool] = None
    existing_count: Optional[int] = None


async def load_sample_journal_data() -> list[JournalEntry]:
    """サンプル仕訳データをCSVから読み込み"""
    csv_path = Path(__file__).parent.parent / "data" / "sample_journal_entries.csv"

    if not csv_path.exists():
        raise HTTPException(
            status_code=404, detail=f"サンプルCSVファイルが見つかりません: {csv_path}"
        )

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
        raise HTTPException(
            status_code=500, detail=f"CSVファイルの読み込みに失敗: {str(e)}"
        )

    return entries


async def save_entries_to_supabase(
    entries: list[JournalEntry], fiscal_year: int, fiscal_month: int, overwrite: bool
) -> dict:
    """仕訳データをSupabaseに保存"""
    if not supabase:
        # HTTPExceptionを投げる代わりに、エラー情報を返す
        logger.error("Supabaseクライアントが設定されていません")
        return {
            "success_count": 0,
            "failed_count": len(entries),
            "total_processed": len(entries),
            "error": "Supabaseクライアントが設定されていません",
        }

    success_count = 0
    failed_count = 0

    try:
        # 上書きモードの場合、既存データを削除
        if overwrite:
            delete_response = (
                supabase.table("journal_entries")
                .delete()
                .match({"fiscal_year": fiscal_year, "fiscal_month": fiscal_month})
                .execute()
            )
            logger.info(
                f"既存データを削除しました: 年度={fiscal_year}, 月={fiscal_month}"
            )

        # 全データを事前に変換
        supabase_data_list = []
        conversion_errors = 0

        for entry in entries:
            try:
                # Supabase用のデータ形式に変換
                # entry.dict()の代わりにjson_encodersを適用したJSON互換形式を使用
                original_data_dict = entry.dict()
                # datetimeをISO形式の文字列に変換
                if "date" in original_data_dict:
                    original_data_dict["date"] = entry.date.strftime("%Y-%m-%d")
                # Decimalをfloatに変換
                for field in ["base_amount", "tax_amount", "total_amount"]:
                    if field in original_data_dict:
                        original_data_dict[field] = float(original_data_dict[field])

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
                    "original_data": original_data_dict,
                    "fiscal_year": fiscal_year,
                    "fiscal_month": fiscal_month,
                    "journal_number": entry.journal_number,
                    "debit_credit": entry.debit_credit,
                    "base_amount": float(entry.base_amount),
                    "tax_amount": float(entry.tax_amount),
                    "tax_category": entry.tax_category,
                }

                supabase_data_list.append(supabase_data)

            except Exception as e:
                logger.error(f"データ変換に失敗: {entry.journal_number}, エラー: {e}")
                conversion_errors += 1

        # バッチ挿入の実行（適切なバッチサイズで分割）
        batch_size = 100  # Supabaseの推奨バッチサイズ
        total_batches = (len(supabase_data_list) + batch_size - 1) // batch_size

        logger.info(
            f"バッチ挿入開始: {len(supabase_data_list)}件を{total_batches}バッチで処理"
        )

        for i in range(0, len(supabase_data_list), batch_size):
            batch_data = supabase_data_list[i : i + batch_size]
            batch_num = (i // batch_size) + 1

            try:
                insert_response = (
                    supabase.table("journal_entries").insert(batch_data).execute()
                )
                batch_success = len(batch_data)
                success_count += batch_success
                logger.info(
                    f"バッチ {batch_num}/{total_batches} 完了: {batch_success}件挿入"
                )

            except Exception as e:
                logger.error(f"バッチ {batch_num}/{total_batches} の挿入に失敗: {e}")
                # バッチ全体が失敗した場合、そのバッチの件数を失敗としてカウント
                batch_failed = len(batch_data)
                failed_count += batch_failed

                # 個別挿入でリトライ（オプション：より詳細なエラー情報が必要な場合）
                if batch_failed <= 10:  # 小さなバッチの場合のみリトライ
                    logger.info(f"バッチ失敗のため個別挿入でリトライ: {batch_failed}件")
                    individual_success = 0
                    for single_data in batch_data:
                        try:
                            supabase.table("journal_entries").insert(
                                single_data
                            ).execute()
                            individual_success += 1
                        except Exception as individual_error:
                            logger.error(
                                f"個別挿入も失敗: {single_data.get('journal_number', 'unknown')}, エラー: {individual_error}"
                            )

                    # 成功・失敗数を調整
                    failed_count -= batch_failed  # バッチ失敗分を戻す
                    success_count += individual_success
                    failed_count += batch_failed - individual_success

        # 変換エラーも失敗数に追加
        failed_count += conversion_errors

    except Exception as e:
        # HTTPExceptionを投げる代わりに、エラー情報を返す
        logger.error(f"Supabaseへの保存処理中にエラーが発生: {str(e)}")
        return {
            "success_count": success_count,
            "failed_count": failed_count
            + (len(entries) - success_count - failed_count),
            "total_processed": len(entries),
            "error": str(e),
        }

    logger.info(f"バッチ挿入完了: 成功={success_count}, 失敗={failed_count}")
    return {
        "success_count": success_count,
        "failed_count": failed_count,
        "total_processed": len(entries),
    }


async def generate_embeddings_and_store_to_pinecone(
    entries: list[JournalEntry], fiscal_year: int, fiscal_month: int
) -> dict:
    """エンベディングを生成してPineconeに保存"""
    if not pc:
        logger.error("Pineconeクライアントが設定されていません")
        return {
            "index_name": "journal-entries",
            "success_count": 0,
            "failed_count": len(entries),
            "total_vectors": 0,
            "index_stats": {},
            "error": "Pineconeクライアントが設定されていません",
        }

    if not GEMINI_API_KEY:
        logger.error("Gemini APIキーが設定されていません")
        return {
            "index_name": "journal-entries",
            "success_count": 0,
            "failed_count": len(entries),
            "total_vectors": 0,
            "index_stats": {},
            "error": "Gemini APIキーが設定されていません",
        }

    index_name = "journal-entries"

    try:
        # インデックスの存在確認と作成
        existing_indexes = [index.name for index in pc.list_indexes()]

        if index_name not in existing_indexes:
            pc.create_index(
                name=index_name,
                dimension=768,  # Gemini text-embedding-004の次元数
                metric="cosine",
                spec={"serverless": {"cloud": "aws", "region": "us-east-1"}},
            )
            logger.info(f"Pineconeインデックス '{index_name}' を作成しました")

        # インデックスに接続
        index = pc.Index(index_name)

        # 全データのエンベディングを事前に生成
        vectors_to_upsert = []
        embedding_errors = 0

        logger.info(f"エンベディング生成開始: {len(entries)}件のデータを処理")

        for entry in entries:
            try:
                # テキスト形式に変換
                text_for_embedding = entry.to_text_for_embedding()

                # Geminiでエンベディング生成
                embedding_result = genai.embed_content(
                    model="models/text-embedding-004", content=text_for_embedding
                )

                embedding_vector = embedding_result["embedding"]

                # メタデータを準備
                metadata = entry.to_metadata_dict()
                metadata.update(
                    {
                        "fiscal_year": fiscal_year,
                        "fiscal_month": fiscal_month,
                        "text_content": text_for_embedding,
                    }
                )

                # ベクトルIDを生成
                vector_id = f"{fiscal_year}_{fiscal_month}_{entry.journal_number}_{entry.line_number}"

                # バッチ用のタプルを追加
                vectors_to_upsert.append((vector_id, embedding_vector, metadata))

            except Exception as e:
                logger.error(
                    f"エンベディング生成に失敗: {entry.journal_number}, エラー: {e}"
                )
                embedding_errors += 1

        # バッチアップサートの実行（適切なバッチサイズで分割）
        batch_size = 100  # Pineconeの推奨バッチサイズ
        total_batches = (len(vectors_to_upsert) + batch_size - 1) // batch_size
        success_count = 0
        failed_count = 0

        logger.info(
            f"Pineconeバッチアップサート開始: {len(vectors_to_upsert)}件を{total_batches}バッチで処理"
        )

        for i in range(0, len(vectors_to_upsert), batch_size):
            batch_vectors = vectors_to_upsert[i : i + batch_size]
            batch_num = (i // batch_size) + 1

            try:
                # バッチでアップサート
                index.upsert(batch_vectors)
                batch_success = len(batch_vectors)
                success_count += batch_success
                logger.info(
                    f"Pineconeバッチ {batch_num}/{total_batches} 完了: {batch_success}件アップサート"
                )

            except Exception as e:
                logger.error(
                    f"Pineconeバッチ {batch_num}/{total_batches} の処理に失敗: {e}"
                )
                # バッチ全体が失敗した場合、そのバッチの件数を失敗としてカウント
                batch_failed = len(batch_vectors)
                failed_count += batch_failed

                # 個別アップサートでリトライ（オプション：小さなバッチの場合のみ）
                if batch_failed <= 10:  # 小さなバッチの場合のみリトライ
                    logger.info(
                        f"Pineconeバッチ失敗のため個別アップサートでリトライ: {batch_failed}件"
                    )
                    individual_success = 0
                    for single_vector in batch_vectors:
                        try:
                            index.upsert([single_vector])
                            individual_success += 1
                        except Exception as individual_error:
                            logger.error(
                                f"Pinecone個別アップサートも失敗: {single_vector[0]}, エラー: {individual_error}"
                            )

                    # 成功・失敗数を調整
                    failed_count -= batch_failed  # バッチ失敗分を戻す
                    success_count += individual_success
                    failed_count += batch_failed - individual_success

        # エンベディング生成エラーも失敗数に追加
        failed_count += embedding_errors

        # インデックス統計情報を取得
        stats = index.describe_index_stats()

        # statsがNoneの場合のフォールバック処理
        if stats is None:
            logger.warning("Pineconeのindex統計情報が取得できませんでした")
            stats = {}

        # statsを辞書形式に変換（Pineconeのstatsオブジェクトを通常の辞書に）
        stats_dict = {}
        if hasattr(stats, "__dict__"):
            # オブジェクトの場合、dictに変換
            stats_dict = {
                k: v for k, v in stats.__dict__.items() if not k.startswith("_")
            }
        elif isinstance(stats, dict):
            stats_dict = stats
        else:
            logger.warning(f"予期しないstatsの型: {type(stats)}")
            stats_dict = {"raw_stats": str(stats)}

        # ネストされたオブジェクトも辞書に変換
        def convert_to_dict(obj):
            if hasattr(obj, "__dict__"):
                return {
                    k: convert_to_dict(v)
                    for k, v in obj.__dict__.items()
                    if not k.startswith("_")
                }
            elif isinstance(obj, dict):
                return {k: convert_to_dict(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [convert_to_dict(item) for item in obj]
            else:
                return obj

        stats_dict = convert_to_dict(stats_dict)

        logger.info(
            f"Pineconeバッチアップサート完了: 成功={success_count}, 失敗={failed_count}"
        )
        return {
            "index_name": index_name,
            "success_count": success_count,
            "failed_count": failed_count,
            "total_vectors": (
                stats_dict.get("total_vector_count", 0)
                if isinstance(stats_dict, dict)
                else 0
            ),
            "index_stats": stats_dict,
        }

    except Exception as e:
        logger.error(f"Pinecone処理に失敗: {str(e)}")
        return {
            "index_name": index_name,
            "success_count": 0,
            "failed_count": len(entries),
            "total_vectors": 0,
            "index_stats": {},
            "error": str(e),
        }


@router.post("/register-journal-data", response_model=JournalDataRegistrationResponse)
async def register_journal_data(
    fiscal_year: int = Form(...),
    fiscal_month: int = Form(...),
    files: list[UploadFile] = File(...),
    overwrite: bool = Form(False),
) -> JournalDataRegistrationResponse:
    """
    会計仕訳データを登録してPineconeベクトルストアを構築する

    指定された年月の会計データをSupabaseに保存し、
    Gemini 2.5 Flashでエンベディングを生成してPineconeに投入します。
    """
    logger.info(
        f"会計仕訳データ登録開始: 年度={fiscal_year}, 月={fiscal_month}, 上書き={overwrite}"
    )

    try:
        # Step 0: 既存データの確認
        if not overwrite and supabase:
            # count='exact' の代わりに count="exact" を文字列として使用
            existing_check = (
                supabase.table("journal_entries")
                .select("*")
                .eq("fiscal_year", fiscal_year)
                .eq("fiscal_month", fiscal_month)
                .execute()
            )

            existing_count = len(existing_check.data) if existing_check.data else 0

            if existing_count > 0:
                logger.info(f"既存データが見つかりました: {existing_count}件")
                return JournalDataRegistrationResponse(
                    status="data_exists",
                    message=f"{fiscal_year}年{fiscal_month}月には既に{existing_count}件の仕訳データが登録されています。上書きしますか？",
                    processed_count=0,
                    failed_count=0,
                    pinecone_index_name="journal-entries",
                    data_exists=True,
                    existing_count=existing_count,
                    details={
                        "existing_data_count": existing_count,
                        "fiscal_year": fiscal_year,
                        "fiscal_month": fiscal_month,
                    },
                )

        # Step 1: アップロードされたファイルから仕訳データを読み込み
        logger.info(
            f"アップロードファイルから仕訳データを読み込み中... ({len(files)}ファイル)"
        )
        entries = []

        for file in files:
            if file.content_type not in [
                "text/csv",
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ]:
                raise HTTPException(
                    status_code=400,
                    detail=f"サポートされていないファイル形式: {file.filename}",
                )

            # ファイル内容を読み込み
            content = await file.read()

            # 一時ファイルに保存して処理
            with tempfile.NamedTemporaryFile(
                mode="wb", delete=False, suffix=".csv"
            ) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name

            try:
                # CSVファイルとして読み込み
                with open(temp_path, "r", encoding="utf-8") as f:
                    csv_content = f.read()
                    if csv_content.startswith("\ufeff"):
                        csv_content = csv_content[1:]  # BOM除去

                    csv_reader = csv.DictReader(csv_content.splitlines())

                    for row in csv_reader:
                        try:
                            entry = JournalEntry.from_csv_row(row)
                            entries.append(entry)
                        except Exception as e:
                            logger.warning(
                                f"CSVデータのパースに失敗: {row}, エラー: {e}"
                            )
                            continue

            finally:
                # 一時ファイルを削除
                os.unlink(temp_path)

        logger.info(f"読み込み完了: {len(entries)}件の仕訳データ")

        if len(entries) == 0:
            raise HTTPException(
                status_code=400, detail="処理対象の仕訳データがありません"
            )

        # Step 2: Supabaseに保存
        logger.info("Supabaseへのデータ保存を開始...")
        supabase_result = await save_entries_to_supabase(
            entries, fiscal_year, fiscal_month, overwrite
        )
        logger.info(
            f"Supabase保存完了: 成功={supabase_result['success_count']}, 失敗={supabase_result['failed_count']}"
        )

        # Supabase保存でエラーがあった場合の処理
        if "error" in supabase_result:
            logger.warning(f"Supabase保存時にエラー: {supabase_result['error']}")

        # Step 3: Pineconeにエンベディングを保存
        logger.info("Pineconeへのエンベディング保存を開始...")
        pinecone_result = await generate_embeddings_and_store_to_pinecone(
            entries, fiscal_year, fiscal_month
        )
        logger.info(
            f"Pinecone保存完了: 成功={pinecone_result['success_count']}, 失敗={pinecone_result['failed_count']}"
        )

        # Pinecone保存でエラーがあった場合の処理
        if "error" in pinecone_result:
            logger.warning(f"Pinecone保存時にエラー: {pinecone_result['error']}")

        # 成功レスポンスを構築
        total_success = min(
            supabase_result["success_count"], pinecone_result["success_count"]
        )
        total_failed = max(
            supabase_result["failed_count"], pinecone_result["failed_count"]
        )

        # detailsからerrorキーを除外
        supabase_result_clean = {
            k: v for k, v in supabase_result.items() if k != "error"
        }
        pinecone_result_clean = {
            k: v for k, v in pinecone_result.items() if k != "error"
        }

        response = JournalDataRegistrationResponse(
            status="success" if total_failed == 0 else "partial_success",
            message=f"{fiscal_year}年{fiscal_month}月の会計仕訳データ登録とベクトルストア構築が完了しました",
            processed_count=total_success,
            failed_count=total_failed,
            pinecone_index_name=pinecone_result["index_name"],
            details={
                "supabase_result": supabase_result_clean,
                "pinecone_result": pinecone_result_clean,
                "fiscal_year": fiscal_year,
                "fiscal_month": fiscal_month,
                "uploaded_files": [file.filename for file in files],
            },
        )

        logger.info(f"会計仕訳データ登録完了: ステータス={response.status}")
        return response

    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
    except Exception as e:
        logger.error(f"予期しないエラーが発生: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"処理中にエラーが発生しました: {str(e)}"
        )


@router.get("/journal-data-status")
async def get_journal_data_status():
    """
    会計仕訳データの登録状況を確認する
    """
    try:
        status_info: Dict[str, Any] = {
            "supabase_connected": supabase is not None,
            "pinecone_connected": pc is not None,
            "gemini_configured": GEMINI_API_KEY is not None,
        }

        # Pineconeインデックス情報を取得
        if pc:
            try:
                indexes = pc.list_indexes()
                journal_index_exists = any(
                    index.name == "journal-entries" for index in indexes
                )
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
                response = supabase.table("journal_entries").select("*").execute()
                status_info["supabase_journal_count"] = (
                    len(response.data) if response.data else 0
                )
            except Exception as e:
                status_info["supabase_error"] = str(e)

        return {"status": "success", "data": status_info}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"ステータス確認中にエラーが発生: {str(e)}"
        )


@router.get("/journal-data")
async def get_journal_data(
    search: Optional[str] = None,
    date_filter: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """
    登録済み仕訳データの一覧を取得
    """
    if not supabase:
        raise HTTPException(
            status_code=500, detail="Supabaseクライアントが設定されていません"
        )

    try:
        # クエリを構築
        query = supabase.table("journal_entries").select("*")

        # 検索条件を追加
        if search:
            query = query.or_(
                f"person.ilike.%{search}%,description.ilike.%{search}%,category.ilike.%{search}%"
            )

        # 日付フィルタを追加
        if date_filter:
            # YYYY-MM形式の場合
            year_month = date_filter.split("-")
            if len(year_month) == 2:
                year, month = year_month
                query = query.eq("fiscal_year", int(year)).eq(
                    "fiscal_month", int(month)
                )

        # ページネーション
        query = query.range(offset, offset + limit - 1).order("entry_date", desc=True)

        # データを取得
        response = query.execute()

        # 総件数を取得
        count_response = supabase.table("journal_entries").select("*").execute()

        return {
            "status": "success",
            "total_count": len(count_response.data) if count_response.data else 0,
            "data": response.data,
            "date_range": {
                "from": "2024-01-01",  # TODO: 実際の最小日付を取得
                "to": "2024-12-31",  # TODO: 実際の最大日付を取得
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"データ取得中にエラーが発生: {str(e)}"
        )


@router.delete("/journal-data/{entry_id}")
async def delete_journal_entry(entry_id: str):
    """
    指定された仕訳データを削除
    """
    if not supabase:
        raise HTTPException(
            status_code=500, detail="Supabaseクライアントが設定されていません"
        )

    try:
        # データの存在確認
        check_response = (
            supabase.table("journal_entries").select("*").eq("id", entry_id).execute()
        )

        if not check_response.data:
            raise HTTPException(
                status_code=404, detail="指定された仕訳データが見つかりません"
            )

        # データを削除
        delete_response = (
            supabase.table("journal_entries").delete().eq("id", entry_id).execute()
        )

        # TODO: Pineconeからも対応するベクトルを削除

        return {
            "status": "success",
            "message": "仕訳データを削除しました",
            "deleted_id": entry_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"削除中にエラーが発生: {str(e)}")


@router.get("/journal-data/history")
async def get_journal_data_history(limit: int = 50, offset: int = 0):
    """
    仕訳データの操作履歴を取得
    """
    if not supabase:
        raise HTTPException(
            status_code=500, detail="Supabaseクライアントが設定されていません"
        )

    try:
        # audit_logsテーブルから仕訳データ関連の操作履歴を取得
        # journal_entriesテーブルの作成、更新、削除操作を追跡
        query = supabase.table("audit_logs").select("*")

        # 仕訳データ関連のアクションのみをフィルタ
        query = query.in_(
            "action_type",
            ["JOURNAL_DATA_UPLOAD", "JOURNAL_DATA_DELETE", "JOURNAL_DATA_UPDATE"],
        )

        # 最新順でソート
        query = query.order("created_at", desc=True)

        # ページネーション
        query = query.range(offset, offset + limit - 1)

        response = query.execute()

        # 総数を取得
        count_response = (
            supabase.table("audit_logs")
            .select("*")
            .in_(
                "action_type",
                ["JOURNAL_DATA_UPLOAD", "JOURNAL_DATA_DELETE", "JOURNAL_DATA_UPDATE"],
            )
            .execute()
        )

        # レスポンス形式を整理
        history_items = []
        for log in response.data:
            history_items.append(
                {
                    "id": log.get("id"),
                    "timestamp": log.get("created_at"),
                    "action": log.get("action_type"),
                    "user_id": log.get("user_id", "system"),
                    "details": log.get("details", {}),
                    "result": log.get("result", "unknown"),
                    "description": format_history_description(log),
                }
            )

        return {
            "status": "success",
            "total_count": len(count_response.data) if count_response.data else 0,
            "history": history_items,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": len(response.data) == limit,
            },
        }

    except Exception as e:
        # audit_logsテーブルが存在しない場合のフォールバック
        logger.warning(f"audit_logsテーブルからの履歴取得に失敗: {str(e)}")

        # journal_entriesテーブルから基本的な履歴情報を取得
        try:
            query = (
                supabase.table("journal_entries")
                .select("fiscal_year, fiscal_month, created_at, source_file")
                .order("created_at", desc=True)
            )

            # 重複を除去して登録操作の履歴を構築
            response = query.execute()

            # 期間ごとに集約
            history_by_period = {}
            for entry in response.data:
                key = f"{entry.get('fiscal_year')}_{entry.get('fiscal_month')}"
                if key not in history_by_period:
                    history_by_period[key] = {
                        "fiscal_year": entry.get("fiscal_year"),
                        "fiscal_month": entry.get("fiscal_month"),
                        "created_at": entry.get("created_at"),
                        "source_files": set(),
                        "count": 0,
                    }
                history_by_period[key]["source_files"].add(
                    entry.get("source_file", "unknown")
                )
                history_by_period[key]["count"] += 1

            # 履歴リストを構築
            history_items = []
            for period_data in sorted(
                history_by_period.values(), key=lambda x: x["created_at"], reverse=True
            ):
                history_items.append(
                    {
                        "id": f"period_{period_data['fiscal_year']}_{period_data['fiscal_month']}",
                        "timestamp": period_data["created_at"],
                        "action": "JOURNAL_DATA_UPLOAD",
                        "user_id": "system",
                        "details": {
                            "fiscal_year": period_data["fiscal_year"],
                            "fiscal_month": period_data["fiscal_month"],
                            "source_files": list(period_data["source_files"]),
                            "entry_count": period_data["count"],
                        },
                        "result": "success",
                        "description": f"{period_data['fiscal_year']}年{period_data['fiscal_month']}月の仕訳データ登録 ({period_data['count']}件)",
                    }
                )

            # ページネーション適用
            paginated_items = history_items[offset : offset + limit]

            return {
                "status": "success",
                "total_count": len(history_items),
                "history": paginated_items,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < len(history_items),
                },
            }

        except Exception as fallback_error:
            raise HTTPException(
                status_code=500,
                detail=f"履歴データ取得中にエラーが発生: {str(fallback_error)}",
            )


def format_history_description(log_entry: dict) -> str:
    """
    ログエントリから人間可読な説明文を生成
    """
    action = log_entry.get("action_type", "")
    details = log_entry.get("details", {})

    if action == "JOURNAL_DATA_UPLOAD":
        fiscal_year = details.get("fiscal_year", "不明")
        fiscal_month = details.get("fiscal_month", "不明")
        file_count = len(details.get("uploaded_files", []))
        processed_count = details.get("processed_count", 0)
        return f"{fiscal_year}年{fiscal_month}月の仕訳データをアップロード ({file_count}ファイル, {processed_count}件処理)"

    elif action == "JOURNAL_DATA_DELETE":
        entry_id = details.get("entry_id", "不明")
        return f"仕訳データを削除 (ID: {entry_id})"

    elif action == "JOURNAL_DATA_UPDATE":
        return "仕訳データを更新"

    return f"操作: {action}"


@router.get("/journal-data/stats")
async def get_journal_data_stats():
    """
    仕訳データの統計情報を取得
    """
    if not supabase:
        raise HTTPException(
            status_code=500, detail="Supabaseクライアントが設定されていません"
        )

    try:
        # 基本統計を取得
        total_response = supabase.table("journal_entries").select("*").execute()
        total_count = len(total_response.data) if total_response.data else 0

        # 月別集計を取得
        monthly_response = (
            supabase.table("journal_entries")
            .select("fiscal_year, fiscal_month, amount")
            .execute()
        )

        # 科目別集計を取得
        category_response = (
            supabase.table("journal_entries").select("category, amount").execute()
        )

        # 担当者別集計を取得
        person_response = (
            supabase.table("journal_entries").select("person, amount").execute()
        )

        # 最新・最古の仕訳データを取得
        latest_response = (
            supabase.table("journal_entries")
            .select("entry_date")
            .order("entry_date", desc=True)
            .limit(1)
            .execute()
        )
        earliest_response = (
            supabase.table("journal_entries")
            .select("entry_date")
            .order("entry_date", desc=False)
            .limit(1)
            .execute()
        )

        # 統計情報を計算
        monthly_breakdown = {}
        category_breakdown = {}
        person_breakdown = {}
        total_amount = 0
        amounts = []

        # 月別集計を処理
        for entry in monthly_response.data:
            year = entry.get("fiscal_year")
            month = entry.get("fiscal_month")
            amount = float(entry.get("amount", 0))

            key = f"{year}-{month:02d}"
            if key not in monthly_breakdown:
                monthly_breakdown[key] = {
                    "count": 0,
                    "total_amount": 0,
                    "year": year,
                    "month": month,
                }

            monthly_breakdown[key]["count"] += 1
            monthly_breakdown[key]["total_amount"] += amount
            total_amount += amount
            amounts.append(amount)

        # 科目別集計を処理
        for entry in category_response.data:
            category = entry.get("category", "不明")
            amount = float(entry.get("amount", 0))

            if category not in category_breakdown:
                category_breakdown[category] = {"count": 0, "total_amount": 0}

            category_breakdown[category]["count"] += 1
            category_breakdown[category]["total_amount"] += amount

        # 担当者別集計を処理
        for entry in person_response.data:
            person = entry.get("person", "不明")
            amount = float(entry.get("amount", 0))

            if person not in person_breakdown:
                person_breakdown[person] = {"count": 0, "total_amount": 0}

            person_breakdown[person]["count"] += 1
            person_breakdown[person]["total_amount"] += amount

        # 金額統計を計算
        amount_stats = {}
        if amounts:
            amount_stats = {
                "total": total_amount,
                "average": total_amount / len(amounts),
                "max": max(amounts),
                "min": min(amounts),
                "count": len(amounts),
            }

        # 月別集計をリスト形式に変換（日付順でソート）
        monthly_list = []
        for key in sorted(monthly_breakdown.keys()):
            data = monthly_breakdown[key]
            monthly_list.append(
                {
                    "period": key,
                    "year": data["year"],
                    "month": data["month"],
                    "count": data["count"],
                    "total_amount": data["total_amount"],
                }
            )

        # 科目別集計をリスト形式に変換（金額順でソート）
        category_list = []
        for category, data in sorted(
            category_breakdown.items(), key=lambda x: x[1]["total_amount"], reverse=True
        ):
            category_list.append(
                {
                    "category": category,
                    "count": data["count"],
                    "total_amount": data["total_amount"],
                }
            )

        # 担当者別集計をリスト形式に変換（金額順でソート）
        person_list = []
        for person, data in sorted(
            person_breakdown.items(), key=lambda x: x[1]["total_amount"], reverse=True
        ):
            person_list.append(
                {
                    "person": person,
                    "count": data["count"],
                    "total_amount": data["total_amount"],
                }
            )

        # 日付範囲を設定
        date_range = {
            "from": (
                earliest_response.data[0]["entry_date"]
                if earliest_response.data
                else None
            ),
            "to": (
                latest_response.data[0]["entry_date"] if latest_response.data else None
            ),
        }

        return {
            "status": "success",
            "stats": {
                "total_entries": total_count,
                "last_updated": datetime.now().isoformat(),
                "date_range": date_range,
                "amount_stats": amount_stats,
                "monthly_breakdown": monthly_list,
                "category_breakdown": category_list[:10],  # 上位10件
                "person_breakdown": person_list[:10],  # 上位10件
                "summary": {
                    "total_amount": total_amount,
                    "total_entries": total_count,
                    "unique_categories": len(category_breakdown),
                    "unique_persons": len(person_breakdown),
                    "active_months": len(monthly_breakdown),
                },
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"統計情報取得中にエラーが発生: {str(e)}"
        )
