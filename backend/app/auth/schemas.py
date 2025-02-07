
from pydantic import BaseModel
from pydantic import field_validator
import re

class Token(BaseModel):
    access_token: str
    token_type: str

class AccessSKTokenData(BaseModel):
    user_uuid: str
    sk_uuid: str
    sk_str: str

class RegisterRequest(BaseModel):
    user_uuid: str # Validated to be a sha256 hash
    @field_validator("user_uuid")
    def validate_user_uuid(cls, v):
        if not v:
            raise ValueError("User uuid is required")
        # Check if the user uuid is a valid sha256 hash
        if not re.match(r'^[a-fA-F0-9]{64}$', v):
            raise ValueError("User uuid is not a valid sha256 hash")
        return v
    hashed_password: str # Validated to be a sha256 hash
    @field_validator("hashed_password")
    def validate_hashed_password(cls, v):
        if not v:
            raise ValueError("Hashed password is required")
        # Check if the hashed password is a valid sha256 hash
        if not re.match(r'^[a-fA-F0-9]{64}$', v):
            raise ValueError("Hashed password is not a valid sha256 hash")
        return v

class Keyring(BaseModel):
    user_uuid: str
    kek_datasources: bytes | None = None
    kek_processing: bytes | None = None
    kek_processing_stacks: bytes | None = None
    kek_settings: bytes | None = None