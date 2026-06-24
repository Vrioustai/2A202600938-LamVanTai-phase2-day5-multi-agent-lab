"""Command-line entrypoint for the lab starter."""

from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.observability.logging import configure_logging

app = typer.Typer(help="Multi-Agent Research Lab starter CLI")
console = Console()


def _init() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)


@app.command()
def baseline(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run a single-agent baseline."""

    _init()
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    
    from multi_agent_research_lab.services.llm_client import LLMClient
    from multi_agent_research_lab.services.search_client import SearchClient
    import time

    start_time = time.time()

    # Simple single-agent flow
    search_client = SearchClient()
    sources = search_client.search(query=query, max_results=request.max_sources)
    
    sources_text = "\n".join(
        [f"- [{i+1}] {s.title}: {s.snippet}" for i, s in enumerate(sources)]
    )

    llm = LLMClient()
    system_prompt = "Write a short answer addressing the query using notes."
    user_prompt = f"Q: {query}\nDocs:\n{sources_text}"

    response = llm.complete(system_prompt, user_prompt)
    latency = time.time() - start_time

    state.final_answer = response.content
    state.add_trace_event("baseline_complete", {"latency": latency, "cost_usd": response.cost_usd})
    
    console.print(Panel.fit(
        f"Answer:\n{state.final_answer}\n\nLatency: {latency:.2f}s\nCost: ${response.cost_usd or 0:.4f}",
        title="Single-Agent Baseline"
    ))


@app.command("multi-agent")
def multi_agent(
    query: Annotated[str, typer.Option("--query", "-q", help="Research query")],
) -> None:
    """Run the multi-agent workflow skeleton."""

    _init()
    state = ResearchState(request=ResearchQuery(query=query))
    workflow = MultiAgentWorkflow()
    try:
        result = workflow.run(state)
    except StudentTodoError as exc:
        console.print(Panel.fit(str(exc), title="Expected TODO", style="yellow"))
        raise typer.Exit(code=2) from exc
    console.print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    app()
