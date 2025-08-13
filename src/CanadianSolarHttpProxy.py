import os
import re
import requests
import logging
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from requests.auth import HTTPDigestAuth
from requests.exceptions import RequestException, Timeout, ConnectionError
from datetime import datetime

app = Flask(__name__)

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# .envファイルを読み込む
load_dotenv()

# 環境変数を取得
CANADIAN_SOLAR_AP_USERNAME = os.getenv('CANADIAN_SOLAR_AP_USERNAME')
CANADIAN_SOLAR_AP_PASSWORD = os.getenv('CANADIAN_SOLAR_AP_PASSWORD')
CANADIAN_SOLAR_AP_IP_ADDRESS = os.getenv('CANADIAN_SOLAR_AP_IP_ADDRESS')
CANADIAN_SOLAR_SERIAL_NUMBER = os.getenv('CANADIAN_SOLAR_SERIAL_NUMBER')
CANADIAN_SOLAR_SESSION_ID = os.getenv('CANADIAN_SOLAR_SESSION_ID')

# 環境変数が取得できない場合はエラーを出力
missing_vars = []
if not CANADIAN_SOLAR_AP_USERNAME:
    missing_vars.append('CANADIAN_SOLAR_AP_USERNAME')
if not CANADIAN_SOLAR_AP_PASSWORD:
    missing_vars.append('CANADIAN_SOLAR_AP_PASSWORD')
if not CANADIAN_SOLAR_AP_IP_ADDRESS:
    missing_vars.append('CANADIAN_SOLAR_AP_IP_ADDRESS')
if not CANADIAN_SOLAR_SERIAL_NUMBER:
    missing_vars.append('CANADIAN_SOLAR_SERIAL_NUMBER')
if not CANADIAN_SOLAR_SESSION_ID:
    missing_vars.append('CANADIAN_SOLAR_SESSION_ID')

if missing_vars:
    raise EnvironmentError(f"Required environment variables are not set: {', '.join(missing_vars)}")

# 有効なgetParamsパラメータのリスト
VALID_GET_PARAMS = {
    'V2HST', 'DST', 'IEVD', 'IEVC', 'IEVR', 'IG0', 
    'IBE', 'ISE', 'ICE', 'TG0', 'IDD', 'IDC', 'IDR', 'IGE'
}

def validate_get_params(get_params_str):
    """getParamsの値をバリデーション"""
    if not get_params_str or not get_params_str.strip():
        raise ValueError("getParams cannot be empty")
    
    # &で分割してパラメータリストを取得
    params = [param.strip() for param in get_params_str.split('&') if param.strip()]
    
    if not params:
        raise ValueError("getParams must contain at least one valid parameter")
    
    # 無効なパラメータをチェック
    invalid_params = []
    for param in params:
        if param not in VALID_GET_PARAMS:
            invalid_params.append(param)
    
    if invalid_params:
        valid_params_str = '&'.join(sorted(VALID_GET_PARAMS))
        raise ValueError(f"Invalid getParams: {', '.join(invalid_params)}. Valid parameters are: {valid_params_str}")
    
    return get_params_str

def validate_sequence_counter(sequence_param):
    """シーケンスカウンタの型と範囲をチェック"""
    if sequence_param is None:
        return 0  # デフォルト値
    
    try:
        # 文字列から整数への変換を試行
        sequence_value = int(sequence_param)
    except (ValueError, TypeError):
        raise ValueError(f"Sequence counter must be an integer, got: {type(sequence_param).__name__}")
    
    # 範囲チェック (16ビット符号なし整数の範囲)
    if not (0 <= sequence_value <= 65535):
        raise ValueError(f"Sequence counter must be between 0 and 65535, got: {sequence_value}")
    
    return sequence_value

def get_query_params():
    try:
        startDate = request.args.get('startDate', datetime.now().strftime('%Y%m%d'))
        endDate = request.args.get('endDate', datetime.now().strftime('%Y%m%d'))
        sequence_param = request.args.get('sequenceCounter')

        # 日付形式の検証
        if not re.match(r'^\d{8}$', startDate) or not re.match(r'^\d{8}$', endDate):
            raise ValueError("Date format must be YYYYMMDD")

        # シーケンスカウンタの検証
        sequenceCounter = validate_sequence_counter(sequence_param)

        # The query string is non-standard, e.g., getParams=A&B&C instead of getParams=A&getParams=B...
        # We parse the raw query string to extract all parameters after 'getParams='.
        raw_query = request.query_string.decode('utf-8')
        match = re.search(r'getParams=(.*)', raw_query)
        if match:
            getParams = match.group(1)
            # getParamsのバリデーション
            getParams = validate_get_params(getParams)
        else:
            raise ValueError("getParams is required. Please specify the parameters to retrieve.")

        return startDate, endDate, sequenceCounter, getParams
    except ValueError as e:
        logger.error(f"Parameter validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error parsing query parameters: {e}")
        raise

@app.route('/getinfo', endpoint='get_info')
def get_info_digest():
    try:
        # パラメータの取得と検証
        startDate, endDate, sequenceCounter, getParams = get_query_params()

        url = f"http://{CANADIAN_SOLAR_AP_IP_ADDRESS}/getinfo.cgi?{CANADIAN_SOLAR_SERIAL_NUMBER}&{CANADIAN_SOLAR_SESSION_ID}&{startDate}&{endDate}&Z{sequenceCounter}&{getParams}"
        auth = HTTPDigestAuth(CANADIAN_SOLAR_AP_USERNAME, CANADIAN_SOLAR_AP_PASSWORD)
        
        logger.info(f"Requesting data from inverter: {url[:50]}...")
        
        # ネットワークリクエストの実行（タイムアウト付き）
        response = requests.get(url, auth=auth, timeout=30)

        if response.status_code == 200:
            try:
                # データのパースとフォーマット
                raw_data = response.text.strip('{}\n')
                if not raw_data:
                    logger.warning("Received empty response from inverter")
                    return jsonify({"error": "Empty response from inverter"}), 502
                
                data_items = raw_data.split('&')
                result = {}
                
                for item in data_items:
                    if ':' in item:
                        key, value = item.split(':', 1)
                        result[key] = value
                    elif item.strip():  # 空でないアイテムのみ処理
                        result[item] = None
                
                logger.info(f"Successfully retrieved {len(result)} data points")
                return jsonify(result)
                
            except Exception as e:
                logger.error(f"Error parsing response data: {e}")
                return jsonify({"error": "Failed to parse response data"}), 502
        else:
            logger.error(f"HTTP error from inverter: {response.status_code}")
            return jsonify({"error": f"Failed to retrieve data, status code: {response.status_code}"}), response.status_code

    except ConnectionError as e:
        logger.error(f"Connection error to inverter: {e}")
        return jsonify({"error": "Connection failed to inverter"}), 503
    
    except Timeout as e:
        logger.error(f"Timeout connecting to inverter: {e}")
        return jsonify({"error": "Request timeout"}), 504
    
    except RequestException as e:
        logger.error(f"Request error: {e}")
        return jsonify({"error": "Network error occurred"}), 502
    
    except ValueError as e:
        logger.error(f"Parameter validation error: {e}")
        return jsonify({"error": str(e)}), 400
    
    except Exception as e:
        logger.error(f"Unexpected error in get_info_digest: {e}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/health')
def health_check():
    """ヘルスチェック用エンドポイント（シーケンスカウンタ状態含む）"""
    return jsonify({
        "status": "healthy"
    })

if __name__ == '__main__':
    app.run(debug=False)
