"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route."""
        from multi_agent_research_lab.core.config import get_settings
        
        settings = get_settings()
        
        # Enforce max iterations
        if state.iteration >= settings.max_iterations:
            if not state.final_answer:
                state.record_route("writer")
            else:
                state.record_route("done")
            return state

        # Routing policy based on missing fields
        if not state.research_notes:
            next_agent = "researcher"
        elif not state.analysis_notes:
            next_agent = "analyst"
        elif not state.final_answer:
            next_agent = "writer"
        else:
            next_agent = "done"

        state.record_route(next_agent)
        state.add_trace_event("supervisor_decision", {"next": next_agent, "iteration": state.iteration})
        return state
