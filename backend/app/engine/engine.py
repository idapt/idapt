from typing import List

from app.engine.index import IndexSingleton
#from app.engine.tools import ToolFactory
from app.settings.app_settings import AppSettings
from llama_index.core.agent import AgentRunner
from llama_index.core.callbacks import CallbackManager
from llama_index.core.settings import Settings
from llama_index.core.tools import BaseTool, ToolMetadata
from llama_index.core.tools.query_engine import QueryEngineTool
from llama_index.postprocessor.colbert_rerank import ColbertRerank

import logging
logger = logging.getLogger(__name__)


def get_chat_engine(filters=None, params=None, event_handlers=None, **kwargs):
    try:
        # The tools that will be used by the agent
        tools: List[BaseTool] = []
        # Used to display the index events in the steps ui
        callback_manager = CallbackManager(handlers=event_handlers or [])

        # Create separate index ? # TODO : Only set the callback manager at index query time so that we avoid multiple chat issues
        index_singleton = IndexSingleton()
        # Get the global index
        files_index = index_singleton.global_index
        # Set the callback manager for the index to the chat engine callback manager
        files_index._callback_manager = callback_manager

        # Check if the index exists
        if files_index is None:
            raise ValueError("No index found")

        # Only return the top k results
        top_k = int(AppSettings.top_k)

        colbert_reranker = ColbertRerank(
            top_n=top_k,
            model="colbert-ir/colbertv2.0",
            tokenizer="colbert-ir/colbertv2.0",
            keep_retrieval_score=True,
        )
        # Build the query engine for the index
        files_query_engine = files_index.as_query_engine(
            filters=filters, **({"similarity_top_k": top_k*2} if top_k != 0 else {}),
            node_postprocessors=[colbert_reranker]
        )
        # Build the tool for the query engine
        # This will be used by the agent to answer questions
        files_query_engine_tool = QueryEngineTool(
            query_engine=files_query_engine,
            metadata=ToolMetadata(
                name="files_query_engine",
                description=AppSettings.files_tool_description
            ),
        )
        # Add the tool to the list of tools
        tools.append(files_query_engine_tool)

        # Add all available tools from the tool factory  # Not used for now
        #configured_tools: List[BaseTool] = ToolFactory.from_env()
        #tools.extend(configured_tools)

        # This creates the most appropriate agent for this llm
        return AgentRunner.from_llm(
            llm=Settings.llm,
            tools=tools,
            callback_manager=callback_manager,
            verbose=True,
            max_iterations=AppSettings.max_iterations
        )
    
    except Exception as e:
        logger.error(f"Error creating chat engine: {e}")
        raise e
