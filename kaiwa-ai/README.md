# Kaiwa AI server
`Kaiwa`のAIサーバー

## Technical
- FastAPI (API Server)
- Style-berts-Vits2 (TTS)
- ChatGPT (LLM)

## Directory
```
kaiwa/
├── models # ttsモデルなど
├── prompts # LLM用のcharacter_promptのtxt
├── scripts # 一時的に使うスクリプト
└── src/
    ├── config_loader.py
    ├── config.toml # API_KEYなど重要情報を格納
    ├── emotion_analysis.py # lukeを使った感情分析
    ├── log.py
    ├── schemes.py # Server用のPydantic scheme
    ├── llm.py # 脳みそ, LLMまわり（現在はChatGPT API）
    ├── tts.py # TTSまわり
    ├── kaiwa.py # LLMとTTSの統合している
    └── kaiwa_server.py # wrappingしたkaiwa.pyをAPI server化
```

## Endpoints
```
ws: /speech # list形式の音声ファイルをreturn
ws: /speech-bytes # base64encode形式のbyte音声ファイルをreturn
get: /character # 現在設定のキャラクターを取得
post: /change_character # キャラクター変更エンドポイント
```

## Set up
1. src/config.tomlを用意（API KEYなどを準備）

2. uvで環境設定
```
uv sync
```

3. `kaiwa_server.py`を実行