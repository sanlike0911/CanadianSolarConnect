
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask
import os

# テスト対象のモジュールをインポートする前に、環境変数を設定
os.environ['CANADIAN_SOLAR_AP_USERNAME'] = 'testuser'
os.environ['CANADIAN_SOLAR_AP_PASSWORD'] = 'testpass'
os.environ['CANADIAN_SOLAR_AP_IP_ADDRESS'] = '192.168.1.1'
os.environ['CANADIAN_SOLAR_SERIAL_NUMBER'] = '1234567890'
os.environ['CANADIAN_SOLAR_SESSION_ID'] = 'dummy_session'

from src.CanadianSolarHttpProxy import app, validate_get_params, validate_sequence_counter, get_query_params

@pytest.fixture
def client():
    """Flaskテストクライアントのフィクスチャ"""
    with app.test_client() as client:
        yield client

# --- 単体テスト ---

def test_validate_get_params_valid():
    """validate_get_params: 有効なパラメータ"""
    assert validate_get_params("V2HST&DST") == "V2HST&DST"
    assert validate_get_params("  IG0 & IBE  ") == "  IG0 & IBE  "

def test_validate_get_params_invalid():
    """validate_get_params: 無効なパラメータ"""
    with pytest.raises(ValueError, match="Invalid getParams: INVALID"):
        validate_get_params("V2HST&INVALID")

def test_validate_get_params_empty():
    """validate_get_params: 空のパラメータ"""
    with pytest.raises(ValueError, match="getParams cannot be empty"):
        validate_get_params("")
    with pytest.raises(ValueError, match="getParams cannot be empty"):
        validate_get_params("   ")

def test_validate_get_params_only_delimiters():
    """validate_get_params: デリミタのみ"""
    with pytest.raises(ValueError, match="getParams must contain at least one valid parameter"):
        validate_get_params("& &&")

def test_validate_sequence_counter_valid():
    """validate_sequence_counter: 有効なシーケンスカウンタ"""
    assert validate_sequence_counter("123") == 123
    assert validate_sequence_counter(456) == 456
    assert validate_sequence_counter("0") == 0
    assert validate_sequence_counter("65535") == 65535
    assert validate_sequence_counter(None) == 0 # デフォルト値

def test_validate_sequence_counter_invalid_type():
    """validate_sequence_counter: 無効な型"""
    with pytest.raises(ValueError, match="Sequence counter must be an integer"):
        validate_sequence_counter("abc")
    with pytest.raises(ValueError, match="Sequence counter must be an integer"):
        validate_sequence_counter(12.34)

def test_validate_sequence_counter_out_of_range():
    """validate_sequence_counter: 範囲外"""
    with pytest.raises(ValueError, match="Sequence counter must be between 0 and 65535"):
        validate_sequence_counter("-1")
    with pytest.raises(ValueError, match="Sequence counter must be between 0 and 65535"):
        validate_sequence_counter("65536")

def test_get_query_params_valid():
    """get_query_params: 有効なクエリパラメータ"""
    with app.test_request_context('/?getParams=V2HST&DST&startDate=20240101&endDate=20240102&sequenceCounter=100'):
        startDate, endDate, sequenceCounter, getParams = get_query_params()
        assert startDate == '20240101'
        assert endDate == '20240102'
        assert sequenceCounter == 100
        assert getParams == 'V2HST&DST'

def test_get_query_params_missing_getparams():
    """get_query_params: getParamsが欠落"""
    with app.test_request_context('/?startDate=20240101'):
        with pytest.raises(ValueError, match="getParams is required"):
            get_query_params()

def test_get_query_params_invalid_date():
    """get_query_params: 無効な日付フォーマット"""
    with app.test_request_context('/?getParams=V2HST&startDate=2024-01-01'):
        with pytest.raises(ValueError, match="Date format must be YYYYMMDD"):
            get_query_params()

# --- 統合テスト ---

@patch('src.CanadianSolarHttpProxy.requests.get')
def test_get_info_digest_success(mock_get, client):
    """/getinfo: 正常なレスポンス"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{V2HST:230.5&DST:10.2}'
    mock_get.return_value = mock_response

    response = client.get('/getinfo?getParams=V2HST&DST')
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['V2HST'] == '230.5'
    assert json_data['DST'] == '10.2'
    mock_get.assert_called_once()

@patch('src.CanadianSolarHttpProxy.requests.get')
def test_get_info_digest_inverter_error(mock_get, client):
    """/getinfo: パワーコンディショナからのエラーステータス"""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_get.return_value = mock_response

    response = client.get('/getinfo?getParams=V2HST')
    
    assert response.status_code == 500
    json_data = response.get_json()
    assert 'error' in json_data
    assert json_data['error'] == 'Failed to retrieve data, status code: 500'

def test_get_info_digest_bad_request(client):
    """/getinfo: 不正なリクエスト（無効なgetParams）"""
    response = client.get('/getinfo?getParams=INVALID_PARAM')
    
    assert response.status_code == 400
    json_data = response.get_json()
    assert 'error' in json_data
    assert 'Invalid getParams: INVALID_PARAM' in json_data['error']

@patch('src.CanadianSolarHttpProxy.requests.get')
def test_get_info_digest_connection_error(mock_get, client):
    """/getinfo: 接続エラー"""
    mock_get.side_effect = requests.exceptions.ConnectionError

    response = client.get('/getinfo?getParams=V2HST')
    
    assert response.status_code == 503
    json_data = response.get_json()
    assert json_data['error'] == 'Connection failed to inverter'

@patch('src.CanadianSolarHttpProxy.requests.get')
def test_get_info_digest_timeout(mock_get, client):
    """/getinfo: タイムアウトエラー"""
    mock_get.side_effect = requests.exceptions.Timeout

    response = client.get('/getinfo?getParams=V2HST')
    
    assert response.status_code == 504
    json_data = response.get_json()
    assert json_data['error'] == 'Request timeout'

@patch('src.CanadianSolarHttpProxy.requests.get')
def test_get_info_digest_empty_response(mock_get, client):
    """/getinfo: パワーコンディショナからの空レスポンス"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = '{}\n' # 空のデータ
    mock_get.return_value = mock_response

    response = client.get('/getinfo?getParams=V2HST')
    
    assert response.status_code == 502
    json_data = response.get_json()
    assert json_data['error'] == 'Empty response from inverter'

def test_health_check(client):
    """/health: ヘルスチェックエンドポイント"""
    response = client.get('/health')
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['status'] == 'healthy'

