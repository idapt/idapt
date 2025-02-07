from app.datasources.chats.database.models import Chat
from app.chat.events import EventCallbackHandler
from app.chat.vercel_response import VercelStreamResponse
from app.chat.schemas import (
    ChatData,
    MessageData
)
from app.engine.engine import get_chat_engine
from app.engine.query_filter import generate_filters

from app.datasources.chats.service import get_chat, add_message_to_chat
from app.datasources.chats.schemas import MessageCreate
from app.settings.model_initialization import init_llm, init_embedding_model
from app.settings.schemas import SettingResponse, AppSettings
from app.settings.service import get_setting


from llama_index.core.llms import MessageRole

from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi import Request
from fastapi import BackgroundTasks
import logging
from datetime import datetime
import uuid

logger = logging.getLogger("uvicorn")

def chat_streaming_response(
    data: ChatData,
    chat_db_session: Session,
    settings_db_session: Session,
    datasources_db_session: Session,
    request: Request,
    background_tasks: BackgroundTasks,
    user_uuid: str,
  ) -> VercelStreamResponse:
  """
  Get the chat streaming response for a given chat id.
  """
  try:
    logger.info(f"Chat route called")    
    last_message_content = data.get_last_message_content()

    # Get the llama index messages
    llama_index_messages = data.get_llama_index_messages()
    # Get the chat
    chat = get_chat(chats_session=chat_db_session, chat_uuid=data.id, include_messages=True, create_if_not_found=False, update_last_opened_at=False)

    # Add the user message to the chat history
    user_message = MessageCreate(
      uuid=data.messages[-1].id,
      role=data.messages[-1].role,
      content=data.messages[-1].content,
      annotations=data.messages[-1].annotations,
      created_at=data.messages[-1].createdAt
    )
    add_message_to_chat(chats_session=chat_db_session, chat_uuid=chat.uuid, message=user_message)
    # Get the document ids already present in the chat
    doc_ids = data.get_chat_document_ids()
    # Generate filters to prevent agent from getting the same document multiple times
    filters = generate_filters(doc_ids)
    # Get the params for the chat engine
    params = data.chat_engine_params or {}
    # Create the event handler to handle the events from the agent
    event_handler = EventCallbackHandler()

    # Get the app settings
    app_setting_response : SettingResponse = get_setting(settings_db_session=settings_db_session, identifier="app")
    app_setting : AppSettings = AppSettings.model_validate_json(app_setting_response.value_json)
    # Get the llm provider from the settings
    llm_provider_setting : SettingResponse = get_setting(settings_db_session=settings_db_session, identifier=app_setting.llm_setting_identifier)
    # Init the llm from the app settings
    llm = init_llm(llm_provider_setting.schema_identifier, llm_provider_setting.value_json, app_setting_response.value_json)

    # Create the chat engine
    agent_runner = get_chat_engine(
        datasources_db_session=datasources_db_session,
        settings_db_session=settings_db_session,
        user_uuid=user_uuid,
        llm=llm,
        max_iterations=app_setting.max_iterations,
        system_prompt=app_setting.system_prompt,
        filters=filters,
        params=params,
        event_handlers=[event_handler]
    )

    # Send the streaming query to the agent
    response = agent_runner.astream_chat(last_message_content, llama_index_messages)

    return VercelStreamResponse(
        request=request, 
        event_handler=event_handler, 
        response=response, 
        chat_data=data, 
        llm=llm,
        chat_db_session=chat_db_session,
        background_tasks=background_tasks,
    )
  except Exception as e:
      logger.error(f"Error in chat streaming route: {str(e)}")
      raise HTTPException(
          status_code=500,
          detail=f"Error in chat streaming route: {str(e)}"
      ) from e


async def chat_request_response(
    data: ChatData,
    chat_db_session: Session,
    settings_db_session: Session,
    datasources_db_session: Session,
    user_uuid: str,
  ) -> ChatData:
  """
  Get the chat request response for a given chat id.
  """
  try:
    # Get the llama index messages
    llama_index_messages = data.get_llama_index_messages()
    last_message_content = data.get_last_message_content()
    # Get the document ids already present in the chat
    doc_ids = data.get_chat_document_ids()
    # Generate filters to prevent agent from getting the same document multiple times
    filters = generate_filters(doc_ids)
    # Get the params for the chat engine
    params = data.chat_engine_params or {}
    # Create the chat engine
    chat_engine = get_chat_engine(
        datasources_db_session=datasources_db_session,
        settings_db_session=settings_db_session,
        user_uuid=user_uuid,
        filters=filters,
        params=params
    )
    # Send the query to the agent
    response = await chat_engine.achat(last_message_content, llama_index_messages)
    # Update the chat with the new assistant message
    assistant_message = MessageData(
      id=str(uuid.uuid4()),
      role=MessageRole.ASSISTANT,
      content=response.response,
      createdAt=datetime.now()
    )
    data.messages.append(assistant_message)
    # Return the chat
    return data
  
  except Exception as e:
      logger.error(f"Error in chat request route: {str(e)}")
      raise HTTPException(
          status_code=500,
          detail=f"Error in chat request route: {str(e)}"
      ) from e