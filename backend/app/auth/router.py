from typing import Annotated
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.routing import APIRouter
from fastapi import Depends, HTTPException, status
import re

from app.auth.service import register_new_user, get_new_access_sk_token_with_password, create_jwt_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, delete_user
from app.auth.schemas import Token, Keyring, RegisterRequest
from app.auth.dependencies import get_keyring_with_user_data_mounting_dependency, mount_user_data_dir_dependency

auth_router = r = APIRouter()

def validate_form_data_username_and_password(form_data: OAuth2PasswordRequestForm):
    """
    Validate the username and password
    """
    if not re.match(r'^[a-fA-F0-9]{64}$', form_data.username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid hashed email",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not re.match(r'^[a-fA-F0-9]{64}$', form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid hashed password",
            headers={"WWW-Authenticate": "Bearer"},
        )

@r.post("/token", response_model=Token)
async def login_for_access_sk_token_route(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Login with user password to get an access token
    """
    # Verify the hashed email and password are valid sha256 hashes
    # User uuid is the hashed email
    validate_form_data_username_and_password(form_data)
    user_uuid = form_data.username
    if not re.match(r'^[a-fA-F0-9]{64}$', user_uuid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid hashed email",
            headers={"WWW-Authenticate": "Bearer"},
        )
    hashed_password = form_data.password
    if not re.match(r'^[a-fA-F0-9]{64}$', hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid hashed password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Mount the user data directory only for the login attempt, it will be unmounted after the login and remounted as a dependency for subsequent requests
    with mount_user_data_dir_dependency(user_uuid):
        # Get the token data
        token_data = get_new_access_sk_token_with_password(user_uuid, hashed_password)
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

@r.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_route(
    register_request: RegisterRequest,
) -> Token:
    """
    Register a new user
    """
    token_data = register_new_user(register_request.user_uuid, register_request.hashed_password)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error registering new user",
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
    
@r.delete("/delete", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_route(
    user_uuid: str,
    keyring: Annotated[Keyring, Depends(get_keyring_with_user_data_mounting_dependency)],
):
    """
    Delete a registered user
    Will not ask for confirmation, be careful with this endpoint
    """
    try:
        delete_user(user_uuid, keyring)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

@r.get("/keyring", response_model=Keyring)
async def read_keyring_route(
    keyring: Annotated[Keyring, Depends(get_keyring_with_user_data_mounting_dependency)],
) -> Keyring:
    """
    Read the keyring of the authenticated user directly
    """
    try:
        return keyring
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
