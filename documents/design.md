# CanadianSolarHttpProxy 設計書

## 1. 概要

本プログラムは、Canadian Solar社の太陽光発電インバータ（以下、CSインバータ）のAPIと通信するための中継プロキシサーバーである。
CSインバータのAPIはDigest認証を必要とし、また独自のパラメータ形式を持つ。本プロキシサーバーは、これらの複雑な仕様を抽象化し、一般的なWebクライアントからよりシンプルなHTTPリクエストでCSインバータの情報を取得する手段を提供する。

## 2. プロジェクトファイル構成

```sh
/
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── README.md
├── requirements.txt
├── .venv/
└── src/
    └── CanadianSolarHttpProxy.py
```

- **`src/CanadianSolarHttpProxy.py`**: アプリケーション本体のソースコード。
- **`Dockerfile`, `docker-compose.yml`**: Dockerコンテナでアプリケーションを実行するための設定ファイル。
- **`requirements.txt`**: Pythonの依存ライブラリリスト。
- **`README.md`**: プロジェクトの概要と基本的な使用方法を記述したドキュメント。

## 3. システム構成

- **Webフレームワーク:** Flask
- **HTTPクライアント:** requests
- **実行環境:** Python 3.x / Docker

本サーバーはFlaskを用いて構築されており、特定のエンドポイントへのリクエストを受け付ける。受け取ったリクエストに基づき、`requests`ライブラリを使用してCSインバータのAPIへDigest認証付きのHTTPリクエストを送信する。

## 4. API仕様

### GET /getinfo

CSインバータから電力関連情報を取得する。

#### 4.1. 説明

指定された期間やパラメータに基づき、CSインバータの`/getinfo.cgi`エンドポイントにリクエストを中継する。サーバー側でシーケンス番号の管理や、非標準的なクエリパラメータの解析を自動的に行う。

#### 4.2. クエリパラメータ

| パラメータ名 | 型 | 説明 | デフォルト値 |
| :--- | :--- | :--- | :--- |
| `startDate` | string | (任意) データ取得開始日 (YYYYMMDD形式)。 | 当日 |
| `endDate` | string | (任意) データ取得終了日 (YYYYMMDD形式)。 | 当日 |
| `sequenceCounter` | int | (任意) リクエストのシーケンス番号。指定しない場合はサーバーが自動でインクリメントする。 | - |
| `getParams` | string | (任意) CSインバータに要求するデータ項目を`&`で連結した文字列。 | `V2HST&DST&...` (固定値) |

#### 4.3. 使用例

##### リクエスト例

```http
GET /getinfo?startDate=20250813&endDate=20250813&sequenceCounter=1&getParams=V2HST&DST&IEVD&IEVC&IEVR&IG0&IBE&ISE&ICE&TG0&IDD&IDC&IDR&IGE
```

##### 正常系レスポンス例 (200 OK)

CSインバータから取得した情報をJSON形式で返す。

```json
{
  "DST": "-2",
  "IBE": "0.0",
  "ICE": "2.0",
  "IDC": "0.0",
  "IDD": "0.0",
  "IDR": "0",
  "IEVC": "-1",
  "IEVD": "-1",
  "IEVR": "0",
  "IG0": "3.4",
  "IGE": "3380",
  "ISE": "1.4",
  "TG0": "6.0",
  "V2HST": "-2"
}
```
*(注: 上記以外のキーが含まれる場合もあります)*

##### 異常系レスポンス例

リクエストに失敗した場合、エラーステータスコードと共にエラーメッセージを返す。

```json
{
  "error": "Failed to retrieve data, status code: 500"
}
```

## 5. 認証

CSインバータAPIが必要とするDigest認証を、サーバーが自動的に処理する。
認証情報は環境変数から読み込まれ、リクエスト時に`requests`ライブラリの`HTTPDigestAuth`を用いて認証ヘッダを生成する。

## 6. 設定

本サーバーの設定は、プロジェクトルートの`.env`ファイルに記述された環境変数によって行う。

- `CANADIAN_SOLAR_AP_USERNAME`: CSインバータのAPIユーザー名
- `CANADIAN_SOLAR_AP_PASSWORD`: CSインバータのAPIパスワード
- `CANADIAN_SOLAR_AP_IP_ADDRESS`: CSインバータのIPアドレス

これらの値が設定されていない場合、サーバーは起動時にエラーを発生させる。

## 7. デバック環境

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```
