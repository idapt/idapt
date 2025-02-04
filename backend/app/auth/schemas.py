
from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    user_uuid: str
    keyring_key: str
    #datasources_decryption_key: str | None = None
    #processing_decryption_key: str | None = None
    #processing_stacks_decryption_key: str | None = None
    #settings_decryption_key: str | None = None


class Keyring(BaseModel):
    user_uuid: str
    datasources_encryption_key: str | None = None
    processing_encryption_key: str | None = None
    processing_stacks_encryption_key: str | None = None
    settings_encryption_key: str | None = None