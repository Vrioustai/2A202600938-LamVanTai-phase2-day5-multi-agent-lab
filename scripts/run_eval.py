import os
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient
from multi_agent_research_lab.core.config import get_settings
import time

def run_baseline_agent(query: str) -> ResearchState:
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    
    search_client = SearchClient()
    sources = search_client.search(query=query, max_results=request.max_sources)
    
    sources_text = "\n".join(
        [f"- [{i+1}] {s.title}: {s.snippet}" for i, s in enumerate(sources)]
    )

    llm = LLMClient()
    system_prompt = "Write a short answer addressing the query using notes."
    user_prompt = f"Q: {query}\nDocs:\n{sources_text}"

    response = llm.complete(system_prompt, user_prompt)

    state.final_answer = response.content
    state.add_trace_event("baseline_complete", {"cost_usd": response.cost_usd})
    return state

def run_multi_agent(query: str) -> ResearchState:
    request = ResearchQuery(query=query)
    state = ResearchState(request=request)
    workflow = MultiAgentWorkflow()
    return workflow.run(state)

def main():
    query = "AI Agent trends in 2026"
    print(f"Running query: {query}")
    
    print("Running Baseline...")
    base_state, base_metrics = run_benchmark("baseline", query, run_baseline_agent)
    
    print("Running Multi-Agent...")
    ma_state, ma_metrics = run_benchmark("multi-agent", query, run_multi_agent)
    
    report_content = f"""# Benchmark Report: Single-Agent vs Multi-Agent

## Query Tested
`{query}`

## Results Comparison

| Metric | Single-Agent Baseline | Multi-Agent Workflow |
|---|---|---|
| **Latency (s)** | {base_metrics.latency_seconds:.2f} | {ma_metrics.latency_seconds:.2f} |
| **Estimated Cost ($)** | {base_metrics.estimated_cost_usd:.4f} | {ma_metrics.estimated_cost_usd:.4f} |
| **Quality Score (0-10)** | {base_metrics.quality_score:.1f} | {ma_metrics.quality_score:.1f} |

## Analysis
- **Latency**: Hệ thống Multi-Agent mất nhiều thời gian hơn do đi qua nhiều bước LLM calls (Researcher -> Analyst -> Writer).
- **Cost**: Chí phí cũng cao hơn tương ứng với số lượng token được xử lý qua từng agent.
- **Quality**: Bù lại, điểm chất lượng của Multi-Agent thường cao hơn vì thông tin được tổng hợp, phân tích các góc độ mâu thuẫn trước khi viết câu trả lời cuối cùng.

## Failure Modes & Fixes
- **Infinite Loop**: Để tránh Supervisor lặp vô hạn giữa Researcher và Analyst mà không vào Writer, đã cấu hình `max_iterations = 6`, nếu vượt quá sẽ ép routing qua `writer`.
- **Context Loss**: Các bước sau như Analyst hay Writer có thể quên câu hỏi gốc. Giải pháp: Luôn inject `state.request.query` vào `user_prompt` của từng agent.
"""
    
    os.makedirs("reports", exist_ok=True)
    with open("reports/benchmark_report.md", "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print("Report generated at reports/benchmark_report.md")

if __name__ == "__main__":
    main()
