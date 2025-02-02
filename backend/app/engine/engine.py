from typing import List

from llama_index.core.agent.react import ReActAgent, ReActChatFormatter
from llama_index.core.agent import AgentRunner
from llama_index.core.callbacks import CallbackManager
from llama_index.core.tools import BaseTool
from llama_index.core.llms import LLM
from sqlalchemy.orm import Session
#from app.engine.tools import ToolFactory
from app.settings.model_initialization import init_embedding_model
from app.datasources.file_manager.service.llama_index import create_query_tool, create_vector_store, create_doc_store
from app.settings.schemas import SettingResponse, AppSettings
from app.settings.service import get_setting
from app.datasources.database.models import Datasource

import logging

logger = logging.getLogger("uvicorn")


def get_chat_engine(session: Session,
                    user_id: str,
                    llm: LLM,
                    max_iterations: int,
                    system_prompt: str,
                    datasource_identifier: str = None,
                    filters=None,
                    params=None,
                    event_handlers=None,
                    **kwargs) -> AgentRunner:
    try:
        # The tools that will be used by the agent
        tools: List[BaseTool] = []
        # Used to display the index events in the steps ui
        callback_manager = CallbackManager(handlers=event_handlers or [])

        # Get the datasources tools
        if datasource_identifier:
            # Get the corresponding datasource
            datasource = session.query(Datasource).filter(Datasource.identifier == datasource_identifier).first()
            # Get the vector store and doc store from the datasource identifier
            vector_store = create_vector_store(datasource.identifier, user_id)
            doc_store = create_doc_store(datasource.identifier, user_id)
            # Get the embedding model setting for the datasource
            embedding_model_setting = get_setting(session, datasource.embedding_setting_identifier)
            # Init the embedding model from the app settings
            embed_model = init_embedding_model(embedding_model_setting.schema_identifier, embedding_model_setting.value_json)
            # Get specific datasource tool
            tool = create_query_tool(session, datasource.identifier, vector_store, doc_store, embed_model, llm)
            tools.append(tool)
        else:
            # Get all datasource tools
            datasources = session.query(Datasource).all()
            for datasource in datasources:
                # Get the vector store and doc store from the datasource identifier
                vector_store = create_vector_store(datasource.identifier, user_id)
                doc_store = create_doc_store(datasource.identifier, user_id)
                # Get the embedding model setting for the datasource
                embedding_model_setting = get_setting(session, datasource.embedding_setting_identifier)
                # Init the embedding model from the app settings
                embed_model = init_embedding_model(embedding_model_setting.schema_identifier, embedding_model_setting.value_json)
                # Get specific datasource tool
                tool = create_query_tool(
                    file_manager_session=session, 
                    datasource_identifier=datasource.identifier, vector_store=vector_store, doc_store=doc_store, embed_model=embed_model, llm=llm)
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

        return ReActAgent.from_llm(
            # Use the initialized llm
            llm=llm,
            tools=tools,
            callback_manager=callback_manager,
            verbose=True,
            max_iterations=max_iterations,
            react_chat_formatter=ReActChatFormatter.from_defaults(
                #system_header=react_agent_prompt, #Use the default system header react
                context=system_prompt # Give the app setting system prompt as base context for the chat formatter
            )
        )
    except Exception as e:
        logger.error(f"Error creating chat engine: {e}")
        raise e
