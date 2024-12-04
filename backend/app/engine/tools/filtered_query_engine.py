from typing import List, Any, Optional, Set
from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.core.tools.query_engine import QueryEngineTool
from llama_index.core.tools.types import ToolMetadata, ToolOutput
from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters
import logging

logger = logging.getLogger(__name__)

DEFAULT_NAME = "filtered_query_engine_tool"
DEFAULT_DESCRIPTION = """Useful for running a natural language query against a knowledge base and get back a natural language response.
This tool keeps track of previously retrieved nodes to avoid repetition."""

class FilteredQueryEngineTool(QueryEngineTool):
    """Query engine tool that filters out previously retrieved nodes.

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

    def _apply_node_filter(self) -> None:
        """Apply filter to exclude previously retrieved nodes."""
        if not self._retrieved_node_ids:
            return

        # Create a filter for excluding previously retrieved nodes
        exclude_nodes_filter = MetadataFilter(
            key="node_id",
            value=list(self._retrieved_node_ids),
            operator="nin"
        )

        # Get existing filters if any
        existing_filters = getattr(self._query_engine, "_filters", None)
        
        if existing_filters:
            # Combine with existing filters
            new_filters = MetadataFilters(
                filters=[*existing_filters.filters, exclude_nodes_filter],
                condition="and"
            )
        else:
            new_filters = MetadataFilters(filters=[exclude_nodes_filter])

        # Apply the combined filters to the query engine
        self._query_engine._filters = new_filters

    def _update_retrieved_nodes(self, response: Any) -> None:
        """Update the set of retrieved node IDs from the response."""
        if hasattr(response, "source_nodes"):
            for node in response.source_nodes:
                if isinstance(node, NodeWithScore) and node.node.node_id:
                    self._retrieved_node_ids.add(node.node.node_id)

    def call(self, *args: Any, **kwargs: Any) -> ToolOutput:
        query_str = self._get_query_str(*args, **kwargs)
        self._apply_node_filter()
        logger.error(f"Applying node filters: {self._query_engine._filters}")
        response = self._query_engine.query(query_str)
        self._update_retrieved_nodes(response)
        logger.error(f"Retrieved nodes: {self._retrieved_node_ids}")
        return ToolOutput(
            content=str(response),
            tool_name=self.metadata.name,
            raw_input={"input": query_str},
            raw_output=response,
        )

    async def acall(self, *args: Any, **kwargs: Any) -> ToolOutput:
        query_str = self._get_query_str(*args, **kwargs)
        self._apply_node_filter()
        response = await self._query_engine.aquery(query_str)
        self._update_retrieved_nodes(response)
        return ToolOutput(
            content=str(response),
            tool_name=self.metadata.name,
            raw_input={"input": query_str},
            raw_output=response,
        ) 