# ===== Stage 1: フロントエンドビルド =====
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# ===== Stage 2: バックエンド =====
FROM python:3.12-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app/ ./app/
COPY backend/data_pipeline/ ./data_pipeline/

# フロントエンドのビルド成果物をコピー
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
