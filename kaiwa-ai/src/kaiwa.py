import logging
from pathlib import Path
import base64

from llm import LLMModel
from tts import FishSpeechTTS
from emotion_analysis import SentimentAnalyzer
from schemes import Message, KaiwaResponse

class Kaiwa:
    def __init__(self, llm_model: LLMModel, tts_model: FishSpeechTTS, analyzer: SentimentAnalyzer, character_name="uzuki"):
        self.llm_model = llm_model
        self.tts_model = tts_model
        self.analyzer = analyzer
        self.conversation_history: list[Message] = []
        self.character = character_name
        self.current_text = ""

    def process_speech_input(self, input_text: str) -> str:
        self.current_text += input_text + " "
        return self.current_text

    async def generate_audio_response(self, text: str) -> KaiwaResponse:
        try:
            _, audio_data = await self.tts_model.speak(text)
            
            response = KaiwaResponse(
                text=text,
                audio=base64.b64encode(audio_data).decode('utf-8'),
                audio_duration=0.0,  # 実際の長さはクライアント側で計算
                emotion=self.analyzer.analyze(text),
            )

            logging.info(f"テキスト: {response.text}")
            logging.info(f"感情: {response.emotion}")

            return response

        except Exception as e:
            logging.error(f"音声生成中にエラーが発生しました: {e}")
            raise

    async def generate_llm_response(self, user_message: str) -> str | None:
        try:
            if user_message:
                self.conversation_history.append(Message(role="user", content=user_message))
                
                print("ユーザー入力を受信: LLM応答を生成します")
                print("LLMへの入力テキスト: ", user_message)

                llm_response = await self.llm_model.reply(self.get_recent_history())
                print(f"LLMの応答: {llm_response}")

                if llm_response:
                    self.conversation_history.append(Message(role="assistant", content=llm_response))
                    self.current_text = ""
                    return llm_response
                
                self.current_text = ""
                return None

        except Exception as e:
            logging.error(f"LLM応答生成中にエラーが発生しました: {e}")
            self.current_text = ""
            return None

    def get_recent_history(self, max_history: int = 20) -> list[Message]:
        return self.conversation_history[-max_history:]


def create_kaiwa(config, characters: dict, character_name: str) -> Kaiwa:
    llm_model = LLMModel(config, character_name=character_name)
    tts_model = FishSpeechTTS()
    tts_model.update_model(characters[character_name]["reference_id"])
    analyzer = SentimentAnalyzer()
    
    return Kaiwa(
        llm_model=llm_model,
        tts_model=tts_model,
        analyzer=analyzer,
        character_name=character_name
    )