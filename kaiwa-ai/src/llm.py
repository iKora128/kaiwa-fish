import logging
from openai import AsyncOpenAI
from pydantic import BaseModel
from pathlib import Path

from schemes import Message
from config_loader import load_config, load_character

MODEL = "gpt-4o-mini"
config = load_config()
characters = load_character()

# Message scheme for LLM
class Message(BaseModel):
    role: str
    content: str

class LLMModel:
    def __init__(self, config: dict, character_name: str, max_token: int = 300):
        self.api_key = config["openai"]["api_key"]
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.openai = AsyncOpenAI(api_key=self.api_key)
        self.max_token = max_token
        self.system_prompt = ""
        self.set_system_prompt(prompt_path=Path(characters[character_name]["prompt_path"]))

    def set_system_prompt(self, prompt_path: Path | None = None, prompt: str | None = None) -> None:
        """システムプロンプトを設定するメソッド"""
        if prompt:
            self.system_prompt = prompt
        elif prompt_path:
            self.system_prompt = prompt_path.read_text(encoding="utf-8").strip()
        else:
            raise ValueError("Either prompt or prompt_path must be provided")

    def set_max_token(self, max_token: int) -> None:
        """最大トークン数を設定するメソッド"""
        self.max_token = max_token

    def get_system_prompt(self) -> str:
        """現在のシステムプロンプトを取得するメソッド"""
        return self.system_prompt

    async def reply(self, history: list[Message]) -> str | None:
        try:
            messages = [{"role": "system", "content": self.system_prompt}] + [entry.model_dump() for entry in history]
            response = await self.openai.chat.completions.create(
                model=MODEL,
                messages=messages,
                max_tokens=self.max_token
            )
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(e)
            logging.error(f"Error in LLM answer generation: {e}")
            return None
        
    async def is_conv_ongoing(self, input: str) -> bool:
        try:
            prompt = f"""
            以下のテキストが会話の途中であるかどうかを判断してください。
            テキスト: "{input}"

            会話の途中である場合は 0 を、そうでない場合は 1 を返してください。
            """
            response = await self.openai.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "あなたは会話の文脈を分析する専門家です。"},
                    {"role": "user", "content": prompt}
                ]
            )
            result = response.choices[0].message.content.strip()
            print(result)
            is_mid_conversation = result.split("\n", 1)[0] == "0"
            reason = result.split("\n", 1)[1] if "\n" in result else ""
            
            logging.info(f"Conversation context detection: {is_mid_conversation}. Reason: {reason}")
            return is_mid_conversation

        except Exception as e:
            logging.error(f"Error in conversation context detection: {e}")
            return False