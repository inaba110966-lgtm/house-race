FROM python:3.12-slim

WORKDIR /app

# 依存関係インストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY app/ ./app/
COPY data_pipeline/ ./data_pipeline/

# フロントエンドのビルド済み成果物（マルチステージでコピー）
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
