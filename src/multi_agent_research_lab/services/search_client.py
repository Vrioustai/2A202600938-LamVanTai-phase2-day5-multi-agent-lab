"""Search client abstraction for ResearcherAgent."""

from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client skeleton."""

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        Implementing a local mock for testing purposes.
        """
        import uuid
        
        # Mock some search results based on the query words
        results = []
        for i in range(max_results):
            results.append(
                SourceDocument(
                    title=f"Mock result {i+1} for {query[:20]}...",
                    url=f"https://mock-search.com/doc_{uuid.uuid4().hex[:8]}",
                    snippet=f"Mock fact {i+1} for {query}.",
                    metadata={"source": "mock_search", "score": 0.9 - (i * 0.1)}
                )
            )
        
        return results
