import asyncio
import logging
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from kaiwa import create_kaiwa, Kaiwa
from schemes import CharacterChangeRequest
from log import setup_logging
from config_loader import load_config, load_character

# nltk
# import nltk
# nltk.download('all')

# FastAPI app
app = FastAPI()

# logging
setup_logging()

# config
config = load_config()
characters = load_character()
CHARACTER_NAME = "marui"

# CORSミドルウェアを追加
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切なオリジンを設定してください
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kaiwaのインスタンスを作成
kaiwa: Kaiwa = create_kaiwa(config, characters, CHARACTER_NAME)

@app.websocket("/speech")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket接続が確立されました")
    
    try:
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                parsed_data = json.loads(data)

                if 'text' in parsed_data:
                    user_message = kaiwa.process_speech_input(parsed_data['text'])
                    
                    if user_message:
                        llm_response = await kaiwa.generate_llm_response(user_message)
                        if llm_response:
                            # テタデータを送信
                            response_data = {
                                "type": "metadata",
                                "text": llm_response,
                                "emotion": kaiwa.analyzer.analyze(llm_response)
                            }
                            await websocket.send_text(json.dumps(response_data))

                            # Fish-Speechのストリーミングレスポンスを処理
                            async for chunk in kaiwa.tts_model.stream_speak(llm_response):
                                if chunk:  # チャンクが空でない場合のみ送信
                                    await websocket.send_bytes(chunk)

                            # 音声生成完了を通知
                            await websocket.send_text(json.dumps({"type": "end"}))

            except asyncio.TimeoutError:
                print("タイムアウトが発生しました。接続を維持します。")
                continue
            except json.JSONDecodeError:
                print(f"無効なJSONデータを受信しました: {data}")
            except Exception as e:
                print(f"メッセージの処理中にエラーが発生しました: {e}")
                error_data = {"type": "error", "message": str(e)}
                await websocket.send_text(json.dumps(error_data))

    except WebSocketDisconnect:
        print("WebSocket接続が閉じられました")

# キャラクターを変更するエンドポイント
@app.post("/change_character")
async def change_character(request: CharacterChangeRequest):
    character = request.character_name
    
    if character not in characters:
        raise HTTPException(status_code=400, detail="Character not found")
    
    try:
        kaiwa.character = character
        kaiwa.tts_model.update_model(character)  # reference_idとしてキャラクター名を使用
        kaiwa.llm_model.set_system_prompt(Path(characters[character]["prompt_path"]))
        kaiwa.conversation_history = []
        
        return JSONResponse(
            status_code=200, 
            content={"detail": f"Character changed to {character}"}
        )
    
    except Exception as e:
        logging.error(f"Failed to update character: {e}")
        raise HTTPException(status_code=500, detail="Failed to update character")

# キャラクターを取得するエンドポイント
@app.get("/character")
async def get_character():
    return {"current_character": kaiwa.character}

# プロンプトのみを変更するエンドポイント（実験的）
@app.post("/change_only_prompt")
async def change_prompt(character: str | None = None, raw_prompt: str | None = None):
    if not character and not raw_prompt:
        raise HTTPException(status_code=400, detail="Either character or prompt must be provided")

    try:
        if character:
            if character not in characters:
                raise ValueError(f"Invalid character: {character}")
            prompt_path = Path(characters[character]["prompt_path"])
            kaiwa.llm_model.set_system_prompt(prompt_path=prompt_path)
        else:
            kaiwa.llm_model.set_system_prompt(prompt=raw_prompt)

        return JSONResponse(status_code=200, content={"detail": "Prompt changed successfully"})

    except ValueError as ve:
        logging.error(f"Invalid input: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except FileNotFoundError as fnf:
        logging.error(f"Prompt file not found: {fnf}")
        raise HTTPException(status_code=404, detail="Prompt file not found")
    except Exception as e:
        logging.error(f"Failed to update prompt: {e}")
        raise HTTPException(status_code=500, detail="Failed to update prompt")
    
# ルートエンドポイント
@app.get("/")
async def root():
    return {"message": "WebSocketサーバーが稼働中です"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)