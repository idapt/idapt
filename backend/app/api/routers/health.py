import logging

from fastapi import APIRouter, HTTPException

health_router = r = APIRouter()

logger = logging.getLogger("uvicorn")


@r.get("")
async def health_route() -> str:
    return "OK"