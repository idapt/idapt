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

#from app.engine.tools import ToolFactory
from app.engine.storage_context import StorageContextSingleton
from app.settings.app_settings import AppSettings

import logging
logger = logging.getLogger(__name__)


def get_chat_engine(filters=None, params=None, event_handlers=None, **kwargs):
    try:
        # The tools that will be used by the agent
        tools: List[BaseTool] = []
        # Used to display the index events in the steps ui
        callback_manager = CallbackManager(handlers=event_handlers or [])

        # TODO : Only set the callback manager at index query time so that we avoid multiple chat issues
        files_index = StorageContextSingleton().index
        
        # Only return the top k results
        top_k = int(AppSettings.top_k)
        
        # Init the query engine that will be reused for each node
        # Configure retriever
        retriever = VectorIndexRetriever(
            index=files_index,
            similarity_top_k=top_k,
        )

        # Configure Colbert reranker to improve the retrieval quality
        #colbert_reranker = ColbertRerank(
        #    top_n=top_k,
        #    model="colbert-ir/colbertv2.0",
        #    tokenizer="colbert-ir/colbertv2.0",
        #    keep_retrieval_score=False, # Do not keep the retrieval score in the metadata
        #)

        # Configure dummy response synthesizer
        response_synthesizer = get_response_synthesizer(
            response_mode="compact",
            llm=Settings.llm
        )

        retriever = AutoMergingRetriever(
            retriever, 
            StorageContextSingleton().storage_context, 
            verbose=True,
            callback_manager=callback_manager
        )

        files_query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            filters=filters,
            response_synthesizer=response_synthesizer,
            #node_postprocessors=[colbert_reranker],
        )
        
        # Build the tool for the query engine
        # This will be used by the agent to answer questions
        files_query_engine_tool = FilteredQueryEngineTool(
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

        # Get the directory where the current module (engine.py) is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Construct the path to the prompt file
        prompt_file_path = os.path.join(current_dir, "react_agent_system_prompt.md")
        # Read the prompt file
        react_agent_system_prompt = open(prompt_file_path, "r").read()
        # Add the user system prompt to it
        react_agent_system_prompt = AppSettings.system_prompt + "\n\n" + react_agent_system_prompt

        # This creates the most appropriate agent for this llm
        return ReActAgent.from_llm(
            llm=Settings.llm,
            tools=tools,
            callback_manager=callback_manager,
            verbose=True,
            max_iterations=AppSettings.max_iterations,
            react_chat_formatter=ReActChatFormatter(
                system_header=react_agent_system_prompt,
                context=""
            )

        )
    
    except Exception as e:
        logger.error(f"Error creating chat engine: {e}")
        raise e
