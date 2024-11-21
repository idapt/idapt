import os
from typing import List

from app.engine.index import IndexConfig, create_index
from app.engine.tools import ToolFactory
from app.settings.app_settings import AppSettings
from llama_index.core.agent import AgentRunner
from llama_index.core.callbacks import CallbackManager
from llama_index.core.settings import Settings
from llama_index.core.tools import BaseTool, ToolMetadata
from llama_index.core.tools.query_engine import QueryEngineTool


def get_chat_engine(filters=None, params=None, event_handlers=None, **kwargs):
    
    tools: List[BaseTool] = []

    callback_manager = CallbackManager(handlers=event_handlers or [])

    # Add query tool if index exists
    index_config = IndexConfig(callback_manager=callback_manager, **(params or {}))
    # Create separate index ?
    files_index = create_index(index_config)

    if files_index is not None:
        
        top_k = int(AppSettings.top_k)
        
        files_query_engine = files_index.as_query_engine(
            filters=filters, **({"similarity_top_k": top_k} if top_k != 0 else {})
        )
        
        files_query_engine_tool = QueryEngineTool(
            query_engine=files_query_engine,
            metadata=ToolMetadata(
                name="files_query_engine",
                description=AppSettings.files_tool_description
            ),
        )
        
        tools.append(files_query_engine_tool)

    # Not used for now
    # Add additional tools
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
