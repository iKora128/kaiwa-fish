import sys
from pathlib import Path

# ソースコードのディレクトリをPythonパスに追加
sys.path.append(str(Path(__file__).parent.parent / "kaiwa-ai" / "src"))

import pytest
from fastapi.testclient import TestClient
from kaiwa_server import app
import json

@pytest.fixture
def client():
    return TestClient(app)

# 基本的なエンドポイントのテスト
def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "WebSocketサーバーが稼働中です"}

# キャラクター取得エンドポイントのテスト
def test_get_character(client):
    response = client.get("/character")
    assert response.status_code == 200
    assert "current_character" in response.json()

# キャラクター変更エンドポイントのテスト
def test_change_character(client):
    response = client.post(
        "/change_character",
        json={"character_name": "marui"}
    )
    assert response.status_code == 200

# WebSocketテスト
def test_websocket_connection():
    with TestClient(app).websocket_connect("/speech") as websocket:
        # テストメッセージの送信
        test_message = {
            "text": "こんにちは"
        }
        websocket.send_text(json.dumps(test_message))
        
        # メタデータの受信
        response = websocket.receive_json()
        assert response["type"] == "metadata"
        assert "text" in response
        assert "emotion" in response
        
        # 音声データの受信（バイナリデータ）
        binary_data = websocket.receive_bytes()
        assert len(binary_data) > 0
        
        # 終了メッセージの受信
        end_response = websocket.receive_json()
        assert end_response["type"] == "end" 