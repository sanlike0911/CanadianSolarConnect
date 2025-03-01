# ベースイメージを指定
FROM python:3.11-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係をコピー
COPY requirements.txt .

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをコピー
COPY src/ ./src/

# コンテナ起動時に実行するコマンドを指定
CMD ["flask", "run", "--host=0.0.0.0"]