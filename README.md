# 競馬分析AI — JRA-VAN × Vector DB × RAG

JRA-VANの過去レースデータをVector DB (Qdrant) に蓄積し、RAG (Retrieval-Augmented Generation) でClaudeが根拠ある競馬分析を行うシステムです。

## アーキテクチャ

```
JRA-VANデータ
     │
     ▼ data_pipeline/indexer.py (テキスト化 → Embedding → Qdrant)
┌─────────────┐     ┌─────────────────┐
│   Qdrant    │◄───►│  FastAPI Backend │◄───► Claude (RAG分析)
│ Vector DB   │     │  (Cloud Run)     │
└─────────────┘     └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  React Frontend  │
                    └─────────────────┘
```

**技術スタック:**
- **Backend**: Python 3.12 / FastAPI
- **Vector DB**: Qdrant (Qdrant Cloud or self-hosted)
- **LLM + Embeddings**: Claude (claude-sonnet-4-6) + voyage-3 embedding
- **Frontend**: React 18 + Vite
- **Infra**: GCP Cloud Run + Artifact Registry + Secret Manager

## ローカル開発

### 前提条件
- Docker / Docker Compose
- Anthropic API Key

### 起動

```bash
# 環境変数の設定
cp .env.example .env
# .env の ANTHROPIC_API_KEY を設定

# Docker Composeで起動 (Qdrant + Backend + Frontend)
docker-compose up --build

# ブラウザで http://localhost:8080 にアクセス
```

### JRA-VANデータのインデックス

```bash
# RAファイル (レース情報) をインデックス
docker-compose exec backend python -m data_pipeline.indexer \
  --data-path /data/jra_van/2024 \
  --data-type race

# SEファイル (成績データ) をインデックス
docker-compose exec backend python -m data_pipeline.indexer \
  --data-path /data/jra_van/2024 \
  --data-type result

# HNファイル (馬情報) をインデックス
docker-compose exec backend python -m data_pipeline.indexer \
  --data-path /data/jra_van/2024 \
  --data-type horse
```

UIからもインデックス操作が可能（「インデックス状況」タブ）。

## GCP デプロイ

### 1. 初回セットアップ

```bash
# プロジェクト設定
export PROJECT_ID=your-gcp-project-id
gcloud config set project $PROJECT_ID

# 必要なAPIを有効化
gcloud services enable run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com

# Artifact Registryリポジトリ作成
gcloud artifacts repositories create keiba-analysis \
  --repository-format=docker \
  --location=asia-northeast1

# Anthropic APIキーをSecret Managerに登録
echo -n "your_anthropic_api_key" | \
  gcloud secrets create anthropic-api-key --data-file=-
```

### 2. Qdrant Cloud の設定

[Qdrant Cloud](https://cloud.qdrant.io/) でクラスターを作成し、URLとAPIキーを取得する。

```bash
# Cloud BuildトリガーのQdrant URL環境変数を設定
# cloudbuild.yaml の QDRANT_URL を実際のURLに変更
```

### 3. デプロイ

```bash
# Cloud Buildでビルド＆デプロイ
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_QDRANT_URL=https://your-cluster.qdrant.io
```

## API エンドポイント

| Method | Path | 説明 |
|--------|------|------|
| POST | `/api/v1/analysis` | RAG競馬分析 |
| POST | `/api/v1/search` | セマンティック検索 |
| GET | `/api/v1/races` | レース一覧 |
| GET | `/api/v1/races/{race_id}` | レース詳細 |
| GET | `/api/v1/horses/search?name=` | 馬名検索 |
| GET | `/api/v1/horses/{horse_id}/history` | 馬の過去成績 |
| POST | `/api/v1/index` | データインデックス (非同期) |
| GET | `/api/v1/index/status` | インデックス状況 |
| GET | `/health` | ヘルスチェック |

## データフロー (RAG)

1. ユーザーが質問を入力（例: 「阪神芝2000mのG2で好走する血統は？」）
2. voyage-3でクエリをベクトル化
3. Qdrantでコサイン類似度の高いレース/馬データを検索
4. 検索結果をコンテキストに変換
5. Claudeがコンテキスト付きで分析テキストを生成

## ライセンス

MIT
