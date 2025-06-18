# Excel Matching System

ExcelファイルとAccounting Systemデータのマッチングを行うWebアプリケーションです。Next.js 15、FastAPI、PostgreSQL、Pineconeを使用してRAGベースの高精度マッチングを実現します。

## 🚀 主な機能

- **ファイルアップロード**: ドラッグ&ドロップによるExcel/CSVファイルのアップロード（最大5ファイル、10MB/ファイル）
- **自動スキーマ推論**: LLM（OpenAI GPT-4）による列マッピングの自動推論
- **データ確認・修正**: 推論されたマッピングの手動修正とリアルタイムプレビュー
- **RAGマッチング**: Pineconeベクトルデータベースを使用した高精度マッチング
- **結果表示**: カテゴリー別（完全一致、類似、未発見）のマッチング結果表示
- **監査ログ**: 全操作の追跡とセッション管理

## 🏗️ アーキテクチャ

```
┌──────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend       │    │   Backend        │    │   Database      │
│   (Next.js 15)   │◄──►│   (FastAPI)      │◄──►│   PostgreSQL    │
│   - TypeScript   │    │   - Python       │    │   (Supabase)    │
│   - Tailwind CSS │    │   - pandas       │    └─────────────────┘
│   - App Router   │    │   - openpyxl     │
└──────────────────┘    └──────────────────┘    ┌─────────────────┐
                                 ▲              │   Vector DB     │
                                 └──────────────┤   (Pinecone)    │
                                                └─────────────────┘
```

## 📋 必要条件

### システム要件
- Node.js 18.0+
- Python 3.10+
- npm または yarn

### 外部サービス
- Supabase アカウント（PostgreSQL）
- Pinecone アカウント（ベクトルデータベース）
- OpenAI アカウント（GPT-4 API）

## 🚀 セットアップ手順

### 1. リポジトリのクローン
```bash
git clone <repository-url>
cd excel-matching
```

### 2. フロントエンド（Next.js）のセットアップ
```bash
cd frontend
npm install
```

### 3. バックエンド（FastAPI）のセットアップ
```bash
cd ../backend

# Python仮想環境の作成
python -m venv .venv

# 仮想環境の有効化
source .venv/bin/activate  # Linux/macOS
# または
.venv\Scripts\activate     # Windows

# 依存関係のインストール
pip install fastapi uvicorn pandas openpyxl python-dotenv psycopg2-binary sqlalchemy pinecone-client
```

### 4. 環境変数の設定

#### backend/.env ファイルを作成：
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
DATABASE_URL=postgresql://postgres:your-password@db.your-project.supabase.co:5432/postgres

# Pinecone Configuration
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment

# OpenAI Configuration (for LLM schema inference)
OPENAI_API_KEY=your-openai-api-key
```

### 5. データベースの設定

Supabaseプロジェクトでデータベースが正しく設定されていることを確認してください。

### 6. Pineconeインデックスの作成

Pineconeコンソールで以下のインデックスを作成：
- Index名: `excel-matching-index`
- Dimension: 1536 (OpenAI embeddings用)
- Metric: cosine

## 🏃‍♂️ 開発サーバーの起動

### フロントエンド（ポート 3000）
```bash
cd frontend
npm run dev
```

### バックエンド（ポート 8000）
```bash
cd backend
source .venv/bin/activate  # 仮想環境の有効化
uvicorn main:app --reload
```

## 🧪 接続テスト

サーバー起動後、以下のエンドポイントで接続をテスト：

- **フロントエンド**: http://localhost:3000
- **API Health Check**: http://localhost:8000/health
- **Database Test**: http://localhost:8000/db-test
- **Pinecone Test**: http://localhost:8000/pinecone-test

## 📁 プロジェクト構造

```
excel-matching/
├── frontend/                 # Next.js フロントエンド
│   ├── app/                 # App Router
│   ├── components/          # Reactコンポーネント
│   ├── public/              # 静的ファイル
│   └── package.json
├── backend/                  # FastAPI バックエンド
│   ├── main.py              # FastAPIアプリケーション
│   ├── .env                 # 環境変数
│   ├── .venv/               # Python仮想環境
│   └── requirements.txt     # Python依存関係
├── .gitignore               # Git無視ファイル
├── README.md                # このファイル
└── CLAUDE.md                # プロジェクト指示
```

## 🔧 API エンドポイント

### 基本エンドポイント
- `GET /` - API情報
- `GET /health` - ヘルスチェック
- `GET /db-test` - データベース接続テスト
- `GET /pinecone-test` - Pinecone接続テスト

### 今後実装予定のエンドポイント
- `POST /api/parse-excel` - Excelファイル解析
- `POST /api/infer-schema` - スキーマ推論（LLM）
- `POST /api/extract-data` - データ抽出・正規化
- `POST /api/match-records` - RAGマッチング

## 🚨 トラブルシューティング

### よくある問題

1. **データベース接続エラー**
   - Supabaseプロジェクトがアクティブか確認
   - DATABASE_URLが正しく設定されているか確認

2. **Pinecone接続エラー**
   - API キーが正しく設定されているか確認
   - インデックスが作成されているか確認

3. **Python依存関係エラー**
   - 仮想環境がアクティブか確認
   - `pip install -r requirements.txt` を再実行

## 📜 ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します。

## 📞 サポート

問題や質問がある場合は、GitHubのIssuesページでお知らせください。
