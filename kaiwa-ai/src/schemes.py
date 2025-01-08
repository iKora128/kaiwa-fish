from pydantic import BaseModel

# Schemes
class Message(BaseModel):
    role: str
    content: str

class KaiwaResponse(BaseModel):
    text: str
    audio: str | list[float] # str for base64, list[float] for audio tensor
    audio_duration: float
    emotion: int

class CharacterChangeRequest(BaseModel):
    character_name: str