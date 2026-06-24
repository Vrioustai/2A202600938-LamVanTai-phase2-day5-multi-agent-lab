"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`."""
        from multi_agent_research_lab.services.llm_client import LLMClient
        from multi_agent_research_lab.services.search_client import SearchClient
        from multi_agent_research_lab.core.schemas import AgentResult

        llm = LLMClient()
        search_client = SearchClient()

        # Step 1: Perform search
        sources = search_client.search(query=state.request.query, max_results=state.request.max_sources)
        state.sources.extend(sources)

        # Step 2: Compile search results
        sources_text = "\n".join(
            [f"- [{i+1}] {s.title}: {s.snippet} (URL: {s.url})" for i, s in enumerate(sources)]
        )

        system_prompt = "Summarize findings briefly."
        user_prompt = f"Q: {state.request.query}\nDocs:\n{sources_text}"

        response = llm.complete(system_prompt, user_prompt)
        state.research_notes = response.content

        state.agent_results.append(
            AgentResult(
                agent=self.name,
                content=response.content,
                metadata={"cost_usd": response.cost_usd, "sources_found": len(sources)},
            )
        )
        state.add_trace_event("researcher_complete", {"cost_usd": response.cost_usd})
        return state
