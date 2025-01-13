from typing import List
import os

from llama_index.core.agent.react import ReActAgent, ReActChatFormatter
from llama_index.core.callbacks import CallbackManager
from llama_index.core.settings import Settings
from llama_index.core.tools import BaseTool
from sqlalchemy.orm import Session
#from app.engine.tools import ToolFactory
from app.settings.models import AppSettings
from app.settings.model_initialization import init_llm, init_embedding_model
from app.services.datasource import get_all_datasources
from app.services.llama_index import create_query_tool, create_vector_store, create_doc_store

import logging
logger = logging.getLogger("uvicorn")


def get_chat_engine(session: Session,
                    app_settings: AppSettings,
                    user_id: str,
                    datasource_identifier: str = None,
                    filters=None,
                    params=None,
                    event_handlers=None,
                    **kwargs):
    try:
        # The tools that will be used by the agent
        tools: List[BaseTool] = []
        # Used to display the index events in the steps ui
        callback_manager = CallbackManager(handlers=event_handlers or [])

        # Init the llm from the app settings
        llm = init_llm(app_settings)
        # Init the embedding model from the app settings
        embed_model = init_embedding_model(app_settings)

        # Get the datasources tools
        if datasource_identifier:
            # Get the vector store and doc store from the datasource identifier
            vector_store = create_vector_store(datasource_identifier, user_id)
            doc_store = create_doc_store(datasource_identifier, user_id)
            # Get specific datasource tool
            tool = create_query_tool(session, datasource_identifier, vector_store, doc_store, embed_model, llm, app_settings)
            tools.append(tool)
        else:
            # Get all datasource tools
            datasources = get_all_datasources(session)
            for ds in datasources:
                # Get the vector store and doc store from the datasource identifier
                logger.info(f"Creating vector store and doc store for datasource {ds.identifier}")
                vector_store = create_vector_store(ds.identifier, user_id)
                doc_store = create_doc_store(ds.identifier, user_id)
                # Get specific datasource tool
                tool = create_query_tool(
                    session=session, 
                    datasource_identifier=ds.identifier, vector_store=vector_store, doc_store=doc_store, embed_model=embed_model, llm=llm, app_settings=app_settings)
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
            # Use the initialized llm
            llm=llm,
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
