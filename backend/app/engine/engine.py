from typing import List
import os

from app.engine.tools.filtered_query_engine import FilteredQueryEngineTool
from llama_index.core.agent.react import ReActAgent, ReActChatFormatter
from llama_index.core.callbacks import CallbackManager
from llama_index.core.settings import Settings
from llama_index.core.tools import BaseTool, ToolMetadata
from llama_index.core.tools.query_engine import QueryEngineTool
from llama_index.postprocessor.colbert_rerank import ColbertRerank
from llama_index.core.retrievers import AutoMergingRetriever, VectorIndexRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.query_engine import RetrieverQueryEngine
#from llama_index.indices.vector_store.retrievers import (
#    VectorIndexAutoRetriever,
#)
#from app.engine.tools import ToolFactory
from app.settings.manager import AppSettingsManager
from app.services import ServiceManager
app_settings = AppSettingsManager.get_instance().settings

import logging
logger = logging.getLogger(__name__)


def get_chat_engine(datasource_identifier: str = None, filters=None, params=None, event_handlers=None, **kwargs):
    try:
        # The tools that will be used by the agent
        tools: List[BaseTool] = []
        # Used to display the index events in the steps ui
        callback_manager = CallbackManager(handlers=event_handlers or [])

        datasource_service = ServiceManager.get_instance().datasource_service
        
        if datasource_identifier:
            # Get specific datasource tool
            tool = datasource_service.get_query_tool(datasource_identifier)
            tools.append(tool)
        else:
            # Get all datasource tools
            session = ServiceManager.get_instance().db_service.get_session()
            datasources = datasource_service.get_all_datasources(session)
            for ds in datasources:
                tool = datasource_service.get_query_tool(ds.name)
                tools.append(tool)

        # Add all available tools from the tool factory  # Not used for now
        #configured_tools: List[BaseTool] = ToolFactory.from_env()
        #tools.extend(configured_tools)

        # Get the directory where the current module (engine.py) is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_file_path = os.path.join(current_dir, "react_agent_system_prompt.md")
        react_agent_system_prompt = open(prompt_file_path, "r").read()
        react_agent_system_prompt = app_settings.system_prompt + "\n\n" + react_agent_system_prompt

        return ReActAgent.from_llm(
            llm=Settings.llm,
            tools=tools,
            callback_manager=callback_manager,
            verbose=True,
            max_iterations=app_settings.max_iterations,
            react_chat_formatter=ReActChatFormatter(
                system_header=react_agent_system_prompt,
                context=""
            )
        )
    except Exception as e:
        logger.error(f"Error creating chat engine: {e}")
        raise e
