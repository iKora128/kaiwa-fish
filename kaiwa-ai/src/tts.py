import logging
from pathlib import Path
from typing import AsyncGenerator
import requests
import ormsgpack
from pydantic import BaseModel
import struct
import io
import time
from urllib.parse import urljoin

AMPLITUDE = 32768  # 16-bit PCMのための振幅スケーリング係数

class ServeReferenceAudio(BaseModel):
    audio: bytes
    text: str

class ServeTTSRequest(BaseModel):
    audio: bytes
    text: str
    reference_id: str | None = None
    references: list[ServeReferenceAudio] | None = None
    streaming: bool = False
    format: str = "wav"
    normalize: bool = True

def parse_wav_header(wav_data: bytes) -> tuple[int, bytes]:
    """WAVヘッダーを解析してサンプルレートと音声データを取得"""
    with io.BytesIO(wav_data) as wav_io:
        # RIFFヘッダーをチェック
        if wav_io.read(4) != b'RIFF':
            raise ValueError("Invalid WAV file: RIFF header not found")
        
        # ファイルサイズをスキップ
        wav_io.read(4)
        
        # WAVEフォーマットをチェック
        if wav_io.read(4) != b'WAVE':
            raise ValueError("Invalid WAV file: WAVE format not found")
        
        # fmtチャンクを探す
        while True:
            chunk_id = wav_io.read(4)
            if not chunk_id:
                raise ValueError("Invalid WAV file: fmt chunk not found")
            
            chunk_size = struct.unpack('<I', wav_io.read(4))[0]
            
            if chunk_id == b'fmt ':
                # フォーマットチャンクを解析
                format_tag = struct.unpack('<H', wav_io.read(2))[0]
                channels = struct.unpack('<H', wav_io.read(2))[0]
                sample_rate = struct.unpack('<I', wav_io.read(4))[0]
                
                # 残りのfmtチャンクをスキップ
                wav_io.read(chunk_size - 8)
                
                # dataチャンクまでスキップ
                while True:
                    chunk_id = wav_io.read(4)
                    if not chunk_id:
                        raise ValueError("Invalid WAV file: data chunk not found")
                    
                    chunk_size = struct.unpack('<I', wav_io.read(4))[0]
                    
                    if chunk_id == b'data':
                        # 音声データを取得
                        audio_data = wav_io.read(chunk_size)
                        return sample_rate, audio_data
                    
                    # 他のチャンクをスキップ
                    wav_io.read(chunk_size)
            
            else:
                # 他のチャンクをスキップ
                wav_io.read(chunk_size)

class FishSpeechTTS:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip('/')
        self.tts_url = f"{self.base_url}/v1/tts"
        self.health_url = f"{self.base_url}/v1/health"
        self.current_reference_id = None
        self._check_server_availability()

    def _check_server_availability(self, max_retries: int = 3, retry_delay: int = 5) -> None:
        """Fish-Speechサーバーの可用性を確認"""
        for attempt in range(max_retries):
            try:
                response = requests.get(self.health_url)
                if response.status_code == 200:
                    logging.info("Fish-Speech サーバーが利用可能です")
                    return
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    logging.warning(f"Fish-Speechサーバーに接続できません。{retry_delay}秒後に再試行します。(試行 {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    logging.error("Fish-Speechサーバーに接続できません。サーバーが起動していることを確認してください。")
                    raise ConnectionError("Fish-Speechサーバーに接続できません")

    async def speak(self, text: str) -> tuple[int, bytes]:
        """
        テキストから音声を生成
        Returns:
            tuple[int, bytes]: (サンプルレート, 音声データ)
        """
        try:
            if not self._is_server_available():
                self._check_server_availability()  # 再確認を試みる
            data = {
                "text": text,
                "reference_id": self.current_reference_id,
                "streaming": False,
                "format": "wav",
                "normalize": True
            }

            response = requests.post(
                self.tts_url,
                data=ormsgpack.packb(data, option=ormsgpack.OPT_SERIALIZE_PYDANTIC),
                headers={"content-type": "application/msgpack"}
            )

            if response.status_code != 200:
                raise Exception(f"TTS request failed: {response.text}")

            # WAVヘッダーを解析してサンプルレートと音声データを取得
            sample_rate, audio_data = parse_wav_header(response.content)
            return sample_rate, audio_data

        except Exception as e:
            logging.error(f"Error in speech generation: {e}")
            raise

    async def stream_speak(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        テキストから音声をストリーミングで生成
        Fish-Speechのストリーミング仕様に従って実装
        """
        try:
            data = {
                "text": text,
                "reference_id": self.current_reference_id,
                "streaming": True,
                "format": "wav",
                "normalize": True
            }

            response = requests.post(
                self.tts_url,
                data=ormsgpack.packb(data, option=ormsgpack.OPT_SERIALIZE_PYDANTIC),
                headers={"content-type": "application/msgpack"},
                stream=True
            )

            if response.status_code != 200:
                raise Exception(f"TTS streaming request failed: {response.text}")

            # Fish-Speechのストリーミングレスポンスを処理
            for chunk in response.iter_content(chunk_size=None):  # チャンクサイズはサーバー側で制御
                if chunk:
                    # サーバー側でAMPLITUDEによるスケーリングと16bit変換が行われているため
                    # クライアント側での追加処理は不要
                    yield chunk

        except Exception as e:
            logging.error(f"Error in speech streaming: {e}")
            raise

    def update_model(self, reference_id: str):
        """リファレンスIDを更新"""
        self.current_reference_id = reference_id
        logging.info(f"Updated reference_id to: {reference_id}")