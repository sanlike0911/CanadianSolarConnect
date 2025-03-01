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

# 環境変数を設定
ENV FLASK_APP=src/CanadianSolarHttpProxy.py
ENV FLASK_ENV=development

# コンテナ起動時に実行するコマンドを指定
CMD ["flask", "run", "--host=0.0.0.0"]