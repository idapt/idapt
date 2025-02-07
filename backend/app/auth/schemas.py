
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class AccessSKTokenData(BaseModel):
    user_uuid: str
    sk_uuid: str
    sk_str: str


class Keyring(BaseModel):
    user_uuid: str
    kek_datasources: bytes | None = None
    kek_processing: bytes | None = None
    kek_processing_stacks: bytes | None = None
    kek_settings: bytes | None = None