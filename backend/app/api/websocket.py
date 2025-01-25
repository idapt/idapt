from fastapi import WebSocket, WebSocketDisconnect
from typing import Any, Callable, Awaitable, Union
import asyncio
from contextlib import asynccontextmanager
import logging
import inspect

logger = logging.getLogger("uvicorn")

class StatusWebSocket:
    def __init__(
        self,
        websocket: WebSocket,
        status_getter: Union[Callable[[], Any], Callable[[], Awaitable[Any]]],
        interval: float = 2.0
    ):
        self.websocket = websocket
        self.status_getter = status_getter
        self.interval = interval
        self._task = None
        self._closing = False
        self._is_async = inspect.iscoroutinefunction(status_getter)
        
    async def accept(self):
        await self.websocket.accept()
        #logger.debug("WebSocket connection opened")
        
    @asynccontextmanager
    async def status_loop(self):
        try:
            self._task = asyncio.create_task(self._run_status_loop())
            yield
        except WebSocketDisconnect as e:
            if e.code not in (1000, 1001, 1012):  # Normal close codes
                logger.error(f"WebSocket disconnected with code {e.code}")
        finally:
            self._closing = True
            if self._task and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                except (asyncio.CancelledError, WebSocketDisconnect):
                    pass
            #logger.debug("WebSocket connection closed")
                
    async def _run_status_loop(self):
        prev_status = None
        try:
            while not self._closing:
                try:
                    current_status = await self.status_getter() if self._is_async else self.status_getter()
                    if current_status != prev_status:
                        await self.websocket.send_json(current_status)
                        prev_status = current_status
                    await asyncio.sleep(self.interval)
                except WebSocketDisconnect:
                    break
        except asyncio.CancelledError:
            #logger.debug("WebSocket status loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in status loop: {str(e)}") 