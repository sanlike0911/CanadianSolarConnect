# AGENTS.md — CanadianSolarConnect 開発指示書

AI コーディングエージェント（Codex / Claude Code など）と開発者に向けた、本リポジトリの共通指示書。
詳細設計は `documents/design.md`、API 利用者向け情報は `README.md` を参照。

## プロジェクト概要

Canadian Solar 社の太陽光発電インバータ（検証済み機種: 電力検出ユニット CSPDUE）から電力情報を取得するための **HTTP 中継プロキシサーバー**。
インバータの API は Digest 認証と独自のクエリ形式を要求するため、それらを抽象化し、一般的な Web クライアントからシンプルな HTTP GET で情報取得できるようにする。

- 本体は `src/CanadianSolarHttpProxy.py` の **単一ファイル Flask アプリ**（エンドポイントは `/getinfo` と `/health` の 2 つ）。
- インバータのパラメータ仕様（`IG0`, `TG0` 等）は**リバースエンジニアリングによる非公式情報**（`README.md` の表を参照）。公式仕様は存在しないため、既存の挙動を正として扱うこと。

## コマンド

すべて**リポジトリルート**で実行する。

```sh
# 開発環境セットアップ
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# テスト実行（必ず `python -m pytest` を使う。素の `pytest` は
# リポジトリルートが sys.path に載らず `No module named 'src'` で失敗する）
python -m pytest tests/ -v

# 単一テストの実行
python -m pytest tests/test_canadian_solar_http_proxy.py::test_health_check -v

# ローカル起動（要 .env — 「環境変数」の節を参照）
FLASK_APP=src/CanadianSolarHttpProxy.py flask run

# Docker 起動（ホスト 8300 → コンテナ 5000）
docker compose up --build
```

## 環境変数

以下 5 つすべてが必須。**モジュール import 時に検証され、欠けていると `EnvironmentError` で起動失敗する**。ローカルではプロジェクトルートの `.env`（gitignore 済み）から `python-dotenv` で読み込む。

| 変数名 | 内容 |
| --- | --- |
| `CANADIAN_SOLAR_AP_USERNAME` | インバータ API のユーザー名（Digest 認証） |
| `CANADIAN_SOLAR_AP_PASSWORD` | インバータ API のパスワード（Digest 認証） |
| `CANADIAN_SOLAR_AP_IP_ADDRESS` | インバータの IP アドレス |
| `CANADIAN_SOLAR_SERIAL_NUMBER` | ユニットのシリアル番号（例: `s24080038`） |
| `CANADIAN_SOLAR_SESSION_ID` | セッション ID（例: `PC1f7eed87-b`） |

`docker-compose.yml` の environment には例示値がハードコードされている。実環境の値に合わせて変更するか `.env` 参照に置き換えて使う。

## アーキテクチャ上の重要ポイント

コードを読む前に知っておくべき「罠」を挙げる。

### 1. getParams は非標準クエリ形式（URL の最後に置く必要がある）

**本プロキシの `/getinfo` エンドポイント**は `getParams=V2HST&DST&IEVD...` のように、**`&` を含む値の羅列**を 1 つのパラメータとして受け取る独自形式を使う。標準的なクエリパーサ（`request.args`）では `DST` 以降が別パラメータに分解されてしまうため、`get_query_params()` は**生のクエリ文字列を正規表現 `getParams=(.*)` で切り出す**実装になっている。

なお、上流のインバータ API へ `getParams=` というキーが送られるわけではない。切り出した値は素の `&` 区切りトークン列として上流 URL の末尾にそのまま付加される（「罠 3」の URL 形式を参照）。

この実装の帰結として:

- **`getParams` はリクエスト URL の最後のパラメータでなければならない**（`getParams=` 以降がすべて値として扱われるため）。
- `getParams` の値は `VALID_GET_PARAMS`（14 項目のホワイトリスト）で検証され、未知の項目は 400 エラーになる。
- この解析ロジックを `request.args` ベースに「修正」してはいけない。非標準形式こそが仕様。

### 2. 環境変数検証が import 時に走る（テストの書き方に影響）

`src/CanadianSolarHttpProxy.py` はモジュールトップレベルで環境変数を検証するため、**テストコードでは `os.environ` を設定してからモジュールを import する**必要がある（`tests/test_canadian_solar_http_proxy.py` 冒頭参照）。import 順を変えるとテストが全滅するので注意。

### 3. インバータへのリクエスト URL とレスポンス形式

上流へのリクエストは以下の形式（Digest 認証付き、タイムアウト 30 秒）:

```
http://{IP}/getinfo.cgi?{SERIAL}&{SESSION_ID}&{startDate}&{endDate}&Z{sequenceCounter}&{getParams}
```

レスポンスは `{KEY:VALUE&KEY:VALUE&...}` という独自テキスト形式で返り、`get_info_digest()` が `{}` と改行を剥がして `&` で分割し、`:` を含む項目は key/value、含まない項目は `key: null` として JSON 化する。

### 4. エラーコードのマッピング

| 状況 | ステータス |
| --- | --- |
| パラメータ検証エラー（`ValueError`） | 400 |
| インバータからの空レスポンス / パース失敗 / その他ネットワークエラー | 502 |
| インバータへの接続失敗（`ConnectionError`）。**接続タイムアウト（`ConnectTimeout`）もここに含まれる** — `ConnectTimeout` は `ConnectionError` と `Timeout` の両方を継承しており、実装は `ConnectionError` を先に捕捉するため | 503 |
| `ConnectionError` に該当しないタイムアウト（`ReadTimeout` 等） | 504 |
| インバータが非 200 を返した場合 | 上流のステータスをそのまま返す |

## ドキュメントと実装の既知の不一致

`README.md` / `documents/design.md` は実装と一部食い違っている。**実装が正**として扱い、ドキュメントを修正する際は以下を参考にすること。

- `getParams`: ドキュメントには「省略時はデフォルト値」とあるが、**実装では必須**（省略すると 400）。
- `sequenceCounter`: design.md には「サーバーが自動でインクリメント」とあるが、**実装は自動インクリメントしない**（省略時は固定で 0）。
- design.md の環境変数一覧には `SERIAL_NUMBER` / `SESSION_ID` が載っていないが、実装では必須。

## 既知のテスト失敗（2026-07-28 時点）

`python -m pytest tests/` は **13 passed / 4 failed**。失敗はいずれも既存の問題で、原因は特定済み:

1. `test_get_info_digest_connection_error` / `test_get_info_digest_timeout`: テストファイルに `import requests` が無く `NameError`（テスト側のバグ）。
2. `test_validate_sequence_counter_invalid_type`: `validate_sequence_counter(12.34)` が `ValueError` になることを期待しているが、実装は `int()` で切り捨てて受理する（テストと実装の仕様不一致）。
3. `test_get_query_params_valid`: テストが `getParams` をクエリの**先頭**に置いているため、生クエリ解析仕様（上記「罠 1」）により後続の `startDate=...` まで getParams の値として扱われ失敗する（テスト側が仕様と不整合）。

新規変更でこれ以外のテストを壊さないこと。上記 4 件を修正する場合は、仕様（実装挙動）とテストのどちらに寄せるかを明確にしてから直すこと。

## 開発時の注意

- 変更後は必ず `python -m pytest tests/ -v` を実行し、結果（新たな失敗が無いこと）を確認してから完了とする。
- コード内コメント・テスト docstring は日本語で統一されている。合わせること。
- 依存関係は `requirements.txt` でバージョン固定。追加時もバージョンを固定する。
