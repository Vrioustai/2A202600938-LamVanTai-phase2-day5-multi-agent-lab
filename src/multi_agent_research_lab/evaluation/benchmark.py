"""Benchmark skeleton for single-agent vs multi-agent."""

from time import perf_counter
from typing import Callable

from multi_agent_research_lab.core.schemas import BenchmarkMetrics
from multi_agent_research_lab.core.state import ResearchState


Runner = Callable[[str], ResearchState]


def run_benchmark(run_name: str, query: str, runner: Runner) -> tuple[ResearchState, BenchmarkMetrics]:
    """Measure latency and return a placeholder metric object."""
    from multi_agent_research_lab.services.llm_client import LLMClient
    
    started = perf_counter()
    state = runner(query)
    latency = perf_counter() - started
    
    # Calculate total cost from trace
    total_cost = 0.0
    if state.trace:
        for event in state.trace:
            cost = event.get("payload", {}).get("cost_usd", 0)
            if cost is not None:
                total_cost += cost

    # Calculate mock quality score using LLM
    llm = LLMClient()
    system_prompt = "Rate 0-10. Output number only."
    user_prompt = f"Q: {query}\nA: {state.final_answer}"
    try:
        response = llm.complete(system_prompt, user_prompt, max_tokens=2)
        quality_score = float(response.content.strip())
    except Exception:
        quality_score = 0.0

    metrics = BenchmarkMetrics(
        run_name=run_name, 
        latency_seconds=latency,
        estimated_cost_usd=total_cost,
        quality_score=quality_score,
        notes="Automated benchmark run."
    )
    return state, metrics
