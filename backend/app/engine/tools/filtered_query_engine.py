from typing import List, Any, Optional, Set
from llama_index.core.schema import BaseNode, Document, NodeRelationship
from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.core.tools.query_engine import QueryEngineTool
from llama_index.core.tools.types import ToolMetadata, ToolOutput
from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters
from llama_index.core.node_parser import get_deeper_nodes
import logging

logger = logging.getLogger(__name__)

DEFAULT_NAME = "filtered_query_engine_tool"
DEFAULT_DESCRIPTION = """Useful for running a natural language query against a knowledge base and get back a natural language response.
This tool keeps track of previously retrieved nodes to avoid repetition."""

class FilteredQueryEngineTool(QueryEngineTool):
    """Query engine tool that filters out previously retrieved nodes and their children.

    Args:
        query_engine (BaseQueryEngine): A query engine.
        metadata (ToolMetadata): The associated metadata of the query engine.
    """

    def __init__(
        self,
        query_engine: BaseQueryEngine,
        metadata: ToolMetadata,
        resolve_input_errors: bool = True,
    ) -> None:
        super().__init__(query_engine, metadata, resolve_input_errors)
        self._retrieved_node_ids: Set[str] = set()

    def reset_retrieved_nodes(self) -> None:
        """Reset the list of retrieved node IDs."""
        self._retrieved_node_ids.clear()

    def _get_all_child_node_ids(self, node: NodeWithScore) -> Set[str]:
        """Recursively get all child node IDs from a node."""
        child_ids = set()
        
        try:
            # Handle both direct node and NodeWithScore cases
            target_node = node.node if hasattr(node, 'node') else node
            
            # Recursively add child node IDs if they exist
            for relationship in target_node.relationships:
                if relationship == NodeRelationship.CHILD:
                    for child in target_node.relationships[relationship]:
                        #logger.error(f"Func Child ID: {child.node_id}")
                        # Add the child node's ID to the retrieved nodes set
                        child_ids.add(child.node_id)
                        # Recursively add child node IDs if they exist
                        child_ids.add(self._get_all_child_node_ids(child))
                        
        except Exception as e:
            logger.debug(f"Error getting child node IDs: {e}")  # Changed to debug since this is expected sometimes
            
        return child_ids

    def _update_retrieved_nodes(self, response: Any) -> None:
        """Update the set of retrieved node IDs from the response."""
        if not response:
            return
        
        try:
            # Handle source nodes if present
            if hasattr(response, "source_nodes") and response.source_nodes:
                # For each source node
                for node in response.source_nodes:
                    #logger.error(f"Node ID: {node.node_id}")
                    # Add the current node's ID
                    #self._retrieved_node_ids.update(node.node_id)
                    
                    # Get all child node IDs
                    child_ids = self._get_all_child_node_ids(node)
                    # Print every child ID
                    #for child_id in child_ids:
                    #    logger.error(f"Child ID: {child_id}")
                    # Update the retrieved node IDs
                    self._retrieved_node_ids.update(child_ids)
            
        except Exception as e:
            logger.error(f"Error updating retrieved nodes: {e}")

    def call(self, *args: Any, **kwargs: Any) -> ToolOutput:
        query_str = self._get_query_str(*args, **kwargs)
        self._apply_node_filter()
        logger.debug(f"Applying node filters: {self._query_engine._filters}")
        
        try:
            response = self._query_engine.query(query_str)

            # TODO Make this work at the retreiver level / query to get the right number of tok K results
            # Manually remove the previously retrieved nodes from the response
            if hasattr(response, "source_nodes") and response.source_nodes:
                for node in response.source_nodes:
                    if node.node_id in self._retrieved_node_ids:
                        response.source_nodes.remove(node)

            # Handle empty response
            if response is None:
                return ToolOutput(
                    content="I couldn't find any relevant information about that in my knowledge base.",
                    tool_name=self.metadata.name,
                    raw_input={"input": query_str},
                    raw_output=None,
                )
            
            # Only try to update retrieved nodes if we have source nodes
            if hasattr(response, "source_nodes") and response.source_nodes:
                self._update_retrieved_nodes(response)
                logger.debug(f"Retrieved nodes: {self._retrieved_node_ids}")

            return ToolOutput(
                content=str(response),
                tool_name=self.metadata.name,
                raw_input={"input": query_str},
                raw_output=response,
            )
            
        except Exception as e:
            logger.error(f"Error in query engine: {e}")
            return ToolOutput(
                content="I encountered an error while searching the knowledge base. Please try rephrasing your question.",
                tool_name=self.metadata.name,
                raw_input={"input": query_str},
                raw_output=None,
            )

    async def acall(self, *args: Any, **kwargs: Any) -> ToolOutput:
        query_str = self._get_query_str(*args, **kwargs)
    
        response = await self._query_engine.aquery(query_str)

    
        # TODO Make this work at the retreiver level / query to get the right number of tok K results
        # Manually remove the previously retrieved nodes from the response
        if hasattr(response, "source_nodes") and response.source_nodes:
            for node in response.source_nodes:
                if node.node_id in self._retrieved_node_ids:
                    response.source_nodes.remove(node)

        self._update_retrieved_nodes(response)
        return ToolOutput(
            content=str(response),
            tool_name=self.metadata.name,
            raw_input={"input": query_str},
            raw_output=response,
        ) 