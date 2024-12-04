import logging

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from llama_index.core.llms import MessageRole
from llama_index.postprocessor.colbert_rerank import ColbertRerank

from app.api.routers.events import EventCallbackHandler
from app.api.routers.models import (
    ChatData,
    Message,
    Result,
    SourceNodes,
)
from app.api.routers.vercel_response import VercelStreamResponse
from app.engine.engine import get_chat_engine
from app.engine.query_filter import generate_filters
from app.engine.storage_context import StorageContextSingleton

chat_router = r = APIRouter()

logger = logging.getLogger("uvicorn")


# streaming endpoint - delete if not needed
@r.post("")
async def chat(
    request: Request,
    data: ChatData,
    background_tasks: BackgroundTasks,
):
    try:
        last_message_content = data.get_last_message_content()
        messages = data.get_history_messages()

        doc_ids = data.get_chat_document_ids()
        #filters = generate_filters(doc_ids)
        filters = None # Do not use filters as we now use the zettelkasten index
        params = data.data or {}
        logger.info(
            f"Creating chat engine with filters: {str(filters)}",
        )
        event_handler = EventCallbackHandler()
        chat_engine = get_chat_engine(
            filters=filters,
            params=params,
            event_handlers=[event_handler]
        )

        ## Do a naive first query on the files index with the last message to get initial results and increase responsiveness
        #files_index = StorageContextSingleton().index
        #top_k = 4
        #colbert_reranker = ColbertRerank(
        #    top_n=top_k,
        #    model="colbert-ir/colbertv2.0",
        #    tokenizer="colbert-ir/colbertv2.0",
        #    keep_retrieval_score=True,
        #)
        #files_query_engine = files_index.as_query_engine( 
        #    **({"similarity_top_k": top_k*2} if top_k != 0 else {}),
        #    node_postprocessors=[colbert_reranker]
        #)
        #initial_query_response = files_query_engine.query(last_message_content)
        ## Add the results to the last message content at the end of it so that the agent can use it right away
        #last_message_content = f"{last_message_content}\n\nHere is some context to help you answer the user query:\n##{initial_query_response}"
  
        # Send the streaming query to the agent
        response = chat_engine.astream_chat(last_message_content, messages)

        return VercelStreamResponse(
            request, event_handler, response, data, background_tasks
        )
    except Exception as e:
        logger.exception("Error in chat engine", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in chat engine: {e}",
        ) from e


# non-streaming endpoint - delete if not needed
@r.post("/request")
async def chat_request(
    data: ChatData,
) -> Result:
    last_message_content = data.get_last_message_content()
    messages = data.get_history_messages()

    doc_ids = data.get_chat_document_ids()
    filters = generate_filters(doc_ids)
    params = data.data or {}
    logger.info(
        f"Creating chat engine with filters: {str(filters)}",
    )

    chat_engine = get_chat_engine(filters=filters, params=params)

    response = await chat_engine.achat(last_message_content, messages)
    return Result(
        result=Message(role=MessageRole.ASSISTANT, content=response.response),
        nodes=SourceNodes.from_source_nodes(response.source_nodes),
    )
