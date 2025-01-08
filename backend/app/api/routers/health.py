from fastapi import APIRouter

health_router = r = APIRouter()

@r.get("")
async def health_route() -> str:
    return "OK"