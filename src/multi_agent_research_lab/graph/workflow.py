"""LangGraph workflow skeleton."""

from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.state import ResearchState


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def build(self) -> object:
        """Fallback empty build as we use pure python loop."""
        return None

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the workflow loop in pure Python to avoid LangChain Python 3.14 incompatibility."""
        from multi_agent_research_lab.agents.supervisor import SupervisorAgent
        from multi_agent_research_lab.agents.researcher import ResearcherAgent
        from multi_agent_research_lab.agents.analyst import AnalystAgent
        from multi_agent_research_lab.agents.writer import WriterAgent

        supervisor = SupervisorAgent()
        agents = {
            "researcher": ResearcherAgent(),
            "analyst": AnalystAgent(),
            "writer": WriterAgent(),
        }

        current_node = "supervisor"
        
        while True:
            if current_node == "supervisor":
                state = supervisor.run(state)
                if not state.route_history:
                    break
                next_node = state.route_history[-1]
                if next_node == "done":
                    break
                current_node = next_node
            elif current_node in agents:
                state = agents[current_node].run(state)
                # After worker finishes, always route back to supervisor
                current_node = "supervisor"
            else:
                break
                
        return state
