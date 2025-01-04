from typing import List
import os

from llama_index.core.agent.react import ReActAgent, ReActChatFormatter
from llama_index.core.callbacks import CallbackManager
from llama_index.core.settings import Settings
from llama_index.core.tools import BaseTool
#from app.engine.tools import ToolFactory
from app.settings.manager import AppSettingsManager
from app.services.database import get_session
from app.services.datasource import get_query_tool, get_all_datasources
app_settings = AppSettingsManager.get_instance().settings

import logging
logger = logging.getLogger(__name__)


def get_chat_engine(datasource_identifier: str = None, filters=None, params=None, event_handlers=None, **kwargs):
    try:
        # The tools that will be used by the agent
        tools: List[BaseTool] = []
        # Used to display the index events in the steps ui
        callback_manager = CallbackManager(handlers=event_handlers or [])

        # Get the datasources tools
        if datasource_identifier:
            # Get specific datasource tool
            tool = get_query_tool(datasource_identifier)
            tools.append(tool)
        else:
            # Get all datasource tools
            with get_session() as session:
                datasources = get_all_datasources(session)
                for ds in datasources:
                    tool = get_query_tool(ds.identifier)
                    tools.append(tool)

        # For each tool, set the callback manager to be able to display the events in the steps ui
        for tool in tools:
            if tool.query_engine:
                # Set the callback manager for the query engine, this is partly useless as it sets the callback manager of the retriever at creation time
                tool.query_engine.callback_manager = callback_manager
        
        # For each tool, set the filters
        for tool in tools:
            if tool.query_engine:
                if filters and tool.query_engine._retriever:
                    # Set the filters for the retriever directly as it is already created
                    tool.query_engine._retriever._filters = filters
                    # Set the callback manager for the retriever directly as it is already created
                    tool.query_engine._retriever.callback_manager = callback_manager

        # Add all available tools from the tool factory  # Not used for now
        #configured_tools: List[BaseTool] = ToolFactory.from_env()
        #tools.extend(configured_tools)

        # Get the directory where the current module (engine.py) is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        prompt_file_path = os.path.join(current_dir, "react_agent_system_prompt.md")
        react_agent_and_system_prompt = open(prompt_file_path, "r").read()
        react_agent_and_system_prompt = app_settings.system_prompt + "\n\n" + react_agent_and_system_prompt

        return ReActAgent.from_llm(
            llm=Settings.llm,
            tools=tools,
            callback_manager=callback_manager,
            verbose=True,
            max_iterations=app_settings.max_iterations,
            react_chat_formatter=ReActChatFormatter(
                system_header=react_agent_and_system_prompt,
                context=""
            )
        )
    except Exception as e:
        logger.error(f"Error creating chat engine: {e}")
        raise e
