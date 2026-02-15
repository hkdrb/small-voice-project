# 1. ビルド用ステージ
FROM python:3.10-slim AS builder

WORKDIR /app

# ビルドに必要なシステム依存関係をインストール
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt をコピー
COPY requirements.txt .

# PyTorch を CPU 版に限定してインストール (イメージサイズ削減の肝)
# その後、requirements.txt の他の依存関係をインストール
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

# 2. 実行用ステージ
FROM python:3.10-slim

WORKDIR /app

# 実行に必要な最小限のシステムライブラリのみインストール
RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# builder ステージからインストール済みの Python パッケージをコピー
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# アプリケーションコードをコピー
COPY alembic.ini .
COPY alembic/ /app/alembic/
COPY backend/ /app/backend/
COPY scripts/ /app/scripts/

# 環境変数の設定
ENV PYTHONPATH=/app

# ポートの開放
EXPOSE 8000

# アプリケーションの起動
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
