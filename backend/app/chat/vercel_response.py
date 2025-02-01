import json
import logging
from datetime import datetime
from typing import Awaitable, List, Optional
import uuid

from aiostream import stream
from fastapi import BackgroundTasks, Request
from sqlalchemy.orm import Session
from fastapi.responses import StreamingResponse
from llama_index.core.chat_engine.types import StreamingAgentChatResponse
from llama_index.core.schema import NodeWithScore
from llama_index.core.llms import LLM

from app.chat.events import EventCallbackHandler
from app.chat.schemas import ChatData, MessageData, SourceNodes
from app.chat.suggestion import NextQuestionSuggestion
from app.chat.schemas import MessageRole
from app.chat.title import ChatTitleGenerator

from app.datasources.chats.schemas import MessageCreate
from app.datasources.chats.service import add_message_to_chat, update_chat_title

logger = logging.getLogger("uvicorn")


class VercelStreamResponse(StreamingResponse):
    """
    Class to convert the response from the chat engine to the streaming format expected by Vercel
    """

    TEXT_PREFIX = "0:"
    DATA_PREFIX = "8:"
    ERROR_PREFIX = "3:"

    def __init__(
        self,
        request: Request,
        chat_db_session: Session,
        event_handler: EventCallbackHandler,
        response: Awaitable[StreamingAgentChatResponse],
        chat_data: ChatData,
        llm: LLM,
        background_tasks: BackgroundTasks,
    ):
        content = VercelStreamResponse.content_generator(
            request, event_handler, response, chat_data, llm, background_tasks, chat_db_session
        )
        super().__init__(content=content)

    @classmethod
    async def content_generator(
        cls,
        request: Request,
        event_handler: EventCallbackHandler,
        response: Awaitable[StreamingAgentChatResponse],
        chat_data: ChatData,
        llm: LLM,
        background_tasks: BackgroundTasks,
        chat_db_session: Session,
    ):
        chat_response_generator = cls._chat_response_generator(
            response, background_tasks, event_handler, chat_data, llm, chat_db_session
        )
        event_generator = cls._event_generator(event_handler)

        # Merge the chat response generator and the event generator
        combine = stream.merge(chat_response_generator, event_generator)
        is_stream_started = False
        try:
            async with combine.stream() as streamer:
                async for output in streamer:
                    if await request.is_disconnected():
                        break

                    if not is_stream_started:
                        is_stream_started = True
                        # Stream a blank message to start displaying the response in the UI
                        yield cls.convert_text("")

                    yield output
        except Exception:
            logger.exception("Error in stream response")
            yield cls.convert_error(
                "An unexpected error occurred while processing your request, preventing the creation of a final answer. Please try again."
            )
        finally:
            # Ensure event handler is marked as done even if connection breaks
            event_handler.is_done = True

    @classmethod
    async def _event_generator(cls, event_handler: EventCallbackHandler):
        """
        Yield the events from the event handler
        """
        async for event in event_handler.async_event_gen():
            event_response = event.to_response()
            if event_response is not None:
                yield cls.convert_data(event_response)

    @classmethod
    async def _chat_response_generator(
        cls,
        response: Awaitable[StreamingAgentChatResponse],
        background_tasks: BackgroundTasks,
        event_handler: EventCallbackHandler,
        chat_data: ChatData,
        llm: LLM,
        chat_db_session: Session,
    ):
        """
        Yield the text response and source nodes from the chat engine
        """
        # Wait for the response from the chat engine
        result = await response

        # Once we got a source node, start a background task to download the files (if needed)
        # cls._process_response_nodes(result.source_nodes, background_tasks)

        # Yield the source nodes
        yield cls.convert_data(
            {
                "type": "sources",
                "data": {
                    "nodes": [
                        SourceNodes.from_source_node(node).model_dump()
                        for node in result.source_nodes
                    ]
                },
            }
        )

        final_response = ""
        async for token in result.async_response_gen():
            final_response += token
            yield cls.convert_text(token)

        # Generate next questions if next question prompt is configured
        #question_data = await cls._generate_next_questions(
        #    chat_data.messages, final_response
        #)
        #if question_data:
        #    yield cls.convert_data(question_data)

        # Add the final response to the chat history
        assistant_message = MessageCreate(
            uuid=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            content=final_response,
            annotations=None,
            created_at=datetime.now()
        )
        add_message_to_chat(chats_session=chat_db_session, chat_uuid=chat_data.id, message=assistant_message)

        # Create the message data for the final response and add it to the chat data
        assistant_message_data = MessageData(
            id=str(uuid.uuid4()),
            role=MessageRole.ASSISTANT,
            content=final_response,
            createdAt=datetime.now()
        )
        chat_data.messages.append(assistant_message_data)

        # Generate a title for the chat
        title = await cls._generate_chat_title(llm, chat_data.messages)
        if title:
            yield cls.convert_data({"type": "title", "data": title})
            # Set the title for the chat
            update_chat_title(chat_db_session, chat_data.id, title)

        # the text_generator is the leading stream, once it's finished, also finish the event stream
        event_handler.is_done = True

    @classmethod
    def convert_text(cls, token: str):
        # Escape newlines and double quotes to avoid breaking the stream
        token = json.dumps(token)
        return f"{cls.TEXT_PREFIX}{token}\n"

    @classmethod
    def convert_data(cls, data: dict):
        data_str = json.dumps(data)
        return f"{cls.DATA_PREFIX}[{data_str}]\n"

    @classmethod
    def convert_error(cls, error: str):
        error_str = json.dumps(error)
        return f"{cls.ERROR_PREFIX}{error_str}\n"

    @staticmethod
    async def _generate_next_questions(chat_history: List[MessageData], response: str):
        questions = await NextQuestionSuggestion.suggest_next_questions(
            chat_history, response
        )
        if questions:
            return {
                "type": "suggested_questions",
                "data": questions,
            }
        return None

    async def _generate_chat_title(llm: LLM, chat_history: List[MessageData]) -> Optional[str]:
        title = await ChatTitleGenerator.generate_title(llm, chat_history)
        return title