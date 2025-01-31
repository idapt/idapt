import logging
import os
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status, Depends
from llama_index.core.llms import MessageRole
from sqlalchemy.orm import Session

from app.chat.events import EventCallbackHandler
from app.chat.schemas import (
    ChatData,
    Message,
    Result,
    SourceNodes,
)
from app.chat.vercel_response import VercelStreamResponse
from app.engine.engine import get_chat_engine
from app.engine.query_filter import generate_filters
from app.api.utils import get_file_manager_db_session, get_user_id

chat_router = r = APIRouter()

logger = logging.getLogger("uvicorn")


# streaming endpoint - delete if not needed
@r.post("")
async def chat_route(
    request: Request,
    data: ChatData,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session),
):
    """
    Streaming endpoint for chat requests.
    Returns a stream of messages from the agent.
    """
    try:
        logger.info(f"Chat route called for user {user_id}")
        last_message_content = data.get_last_message_content()
        messages = data.get_history_messages()

        doc_ids = data.get_chat_document_ids()
        # Generate filters to prevent agent from getting the same document multiple times
        filters = generate_filters(doc_ids)
        params = data.data or {}
        logger.info(
            f"Creating chat engine with filters: {str(filters)}",
        )
        event_handler = EventCallbackHandler()
        chat_engine = get_chat_engine(
            session=session,
            user_id=user_id,
            filters=filters,
            params=params,
            event_handlers=[event_handler]
        )

        # Send the streaming query to the agent
        response = chat_engine.astream_chat(last_message_content, messages)

        return VercelStreamResponse(
            request, event_handler, response, data, background_tasks
        )
    except Exception as e:
        logger.error(f"Error in chat engine: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in chat engine: {e}",
        ) from e

@r.post("/request")
async def chat_request_route(
    data: ChatData,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session),
) -> Result:
    """
    Non-streaming endpoint for chat requests.
    Returns a single message from the agent.
    """
    try:
        logger.info(f"Chat request route called for user {user_id}")
        last_message_content = data.get_last_message_content()
        messages = data.get_history_messages()

        doc_ids = data.get_chat_document_ids()
        filters = generate_filters(doc_ids)
        params = data.data or {}
        logger.info(
            f"Creating chat engine with filters: {str(filters)}",
        )

        chat_engine = get_chat_engine(
            session=session,
            user_id=user_id,
            filters=filters,
            params=params
        )

        response = await chat_engine.achat(last_message_content, messages)
        return Result(
            result=Message(role=MessageRole.ASSISTANT, content=response.response),
            nodes=SourceNodes.from_source_nodes(response.source_nodes),
        )
    except Exception as e:
        logger.error(f"Error in chat request route: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in chat request route: {str(e)}"
        ) from e