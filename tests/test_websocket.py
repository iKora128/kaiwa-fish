import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/speech"
    async with websockets.connect(uri) as websocket:
        # テストメッセージの送信
        message = {
            "text": "こんにちは"
        }
        await websocket.send(json.dumps(message))
        
        while True:
            try:
                response = await websocket.recv()
                if isinstance(response, str):
                    # JSON応答の処理
                    data = json.loads(response)
                    print("受信したJSON:", data)
                    if data.get("type") == "end":
                        break
                else:
                    # バイナリデータ（音声）の処理
                    print("音声データを受信:", len(response), "バイト")
            except websockets.ConnectionClosed:
                break

asyncio.run(test_websocket())