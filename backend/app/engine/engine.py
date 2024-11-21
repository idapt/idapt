import os
from typing import List

from app.engine.index import IndexConfig, create_index
from app.engine.tools import ToolFactory
from app.settings.app_settings import AppSettings
from llama_index.core.agent import AgentRunner
from llama_index.core.callbacks import CallbackManager
from llama_index.core.settings import Settings
from llama_index.core.tools import BaseTool
from llama_index.core.tools.query_engine import QueryEngineTool


def get_chat_engine(filters=None, params=None, event_handlers=None, **kwargs):
    system_prompt = AppSettings.system_prompt
    top_k = int(AppSettings.top_k)
    tools: List[BaseTool] = []
    callback_manager = CallbackManager(handlers=event_handlers or [])

    # Add query tool if index exists
    index_config = IndexConfig(callback_manager=callback_manager, **(params or {}))
    # Create separate index ?
    index = create_index(index_config)
    if index is not None:
        query_engine = index.as_query_engine(
            filters=filters, **({"similarity_top_k": top_k} if top_k != 0 else {})
        )
        query_engine_tool = QueryEngineTool.from_defaults(query_engine=query_engine)
        tools.append(query_engine_tool)

    # Not used for now
    # Add additional tools
    #configured_tools: List[BaseTool] = ToolFactory.from_env()
    #tools.extend(configured_tools)

    return AgentRunner.from_llm(
        llm=Settings.llm,
        tools=tools,
        system_prompt=system_prompt,
        callback_manager=callback_manager,
        verbose=True,
        max_iterations=AppSettings.max_iterations
    )
