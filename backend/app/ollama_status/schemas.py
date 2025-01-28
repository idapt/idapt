from pydantic import BaseModel

class OllamaStatusResponse(BaseModel):
    is_downloading: bool