# Excel Matching System

Excel ファイルと Accounting System データのマッチングを行う Web アプリケーションです。Next.js 15、FastAPI、PostgreSQL、Pinecone を使用して RAG ベースの高精度マッチングを実現します。

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
