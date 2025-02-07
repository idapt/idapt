from typing import Annotated
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.routing import APIRouter
from fastapi import Depends, HTTPException, status

from app.auth.service import get_new_access_sk_token_with_password, get_keyring_with_access_sk_token_from_auth_header, create_jwt_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.auth.schemas import Token, Keyring

auth_router = r = APIRouter()

@r.post("/token", response_model=Token)
async def login_for_access_sk_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Login with user password to get an access token
    """
    token_data = get_new_access_sk_token_with_password(form_data.username, form_data.password)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_jwt_access_token(
        data={
            "user_uuid": token_data.user_uuid,
            "sk_uuid": token_data.sk_uuid,
            "sk_str": token_data.sk_str,
        }, 
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@r.post("/register", response_model=Token)
async def register(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Register a new user
    """
    token_data = None#init_new_keyring(form_data.username, form_data.password)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
@r.get("/keyring", response_model=Keyring)
async def read_keyring(
    keyring: Annotated[Keyring, Depends(get_keyring_with_access_sk_token_from_auth_header)],
):
    return keyring


@r.get("/keyring/datasources")
async def read_keyring_datasources(
    keyring: Annotated[Keyring, Depends(get_keyring_with_access_sk_token_from_auth_header)],
):
    return keyring.kek_datasources