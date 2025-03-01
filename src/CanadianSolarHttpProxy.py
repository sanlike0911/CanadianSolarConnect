import os
import requests
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from requests.auth import HTTPDigestAuth
from datetime import datetime

app = Flask(__name__)

# シーケンスカウンタを初期化
sequenceCounter = 0

# .envファイルを読み込む
load_dotenv()

# 環境変数を取得
CANADIAN_SOLAR_AP_USERNAME = os.getenv('CANADIAN_SOLAR_AP_USERNAME')
CANADIAN_SOLAR_AP_PASSWORD = os.getenv('CANADIAN_SOLAR_AP_PASSWORD')
CANADIAN_SOLAR_AP_IP_ADDRESS = os.getenv('CANADIAN_SOLAR_AP_IP_ADDRESS')

# 環境変数が取得できない場合はエラーを出力
if not CANADIAN_SOLAR_AP_USERNAME or not CANADIAN_SOLAR_AP_PASSWORD or not CANADIAN_SOLAR_AP_IP_ADDRESS:
    raise EnvironmentError("Required environment variables (USERNAME, PASSWORD, IP_ADDRESS) are not set.")

def get_query_params():
    startDate = request.args.get('startDate', datetime.now().strftime('%Y%m%d'))
    endDate = request.args.get('endDate', datetime.now().strftime('%Y%m%d'))
    sequenceCounterParam = request.args.get('sequenceCounter')
    getParams = request.args.get('getParams', 'V2HST&DST&IEVD&IEVC&IEVR&IG0&IBE&ISE&ICE&TG0&IDD&IDC&IDR&IGE')
    return startDate, endDate, sequenceCounterParam, getParams

def update_sequence_counter(sequenceCounterParam):
    global sequenceCounter
    if sequenceCounterParam is not None:
        sequenceCounter = int(sequenceCounterParam)
    else:
        sequenceCounter = (sequenceCounter + 1) % (65535 + 1)
    return sequenceCounter

@app.route('/getinfo', endpoint='get_info')
def get_info_digest():
    startDate, endDate, sequenceCounterParam, getParams = get_query_params()
    sequenceCounter = update_sequence_counter(sequenceCounterParam)

    url = f"http://{CANADIAN_SOLAR_AP_IP_ADDRESS}/getinfo.cgi?24080038&PC1f7eed87-b&{startDate}&{endDate}&Z{sequenceCounter}&{getParams}"
    auth = HTTPDigestAuth(CANADIAN_SOLAR_AP_USERNAME, CANADIAN_SOLAR_AP_PASSWORD)
    response = requests.get(url, auth=auth)

    if response.status_code == 200:
        data = response.text.strip('{}\n').split('&')
        result = {item.split(':')[0]: item.split(':')[1] if ':' in item else None for item in data}
        return jsonify(result)
    else:
        return jsonify({"error": f"Failed to retrieve data, status code: {response.status_code}"}), response.status_code

if __name__ == '__main__':
    app.run(debug=False)
