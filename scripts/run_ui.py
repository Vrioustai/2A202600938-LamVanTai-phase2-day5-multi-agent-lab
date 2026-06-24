import os
import sys
import time
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

# Thêm src vào sys.path để import các module của bài lab
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow

app = FastAPI(title="Multi-Agent UI")

class QueryRequest(BaseModel):
    query: str

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    ui_path = os.path.join(os.path.dirname(__file__), "..", "ui", "index.html")
    if not os.path.exists(ui_path):
        return "UI file not found. Please create ui/index.html."
    with open(ui_path, "r", encoding="utf-8") as f:
        return f.read()

@app.post("/api/research")
async def research(req: QueryRequest):
    try:
        start = time.perf_counter()
        
        request = ResearchQuery(query=req.query, max_sources=2)
        state = ResearchState(request=request)
        workflow = MultiAgentWorkflow()
        final_state = workflow.run(state)
        
        latency = time.perf_counter() - start
        
        # Calculate cost
        total_cost = 0.0
        if final_state.trace:
            for event in final_state.trace:
                cost = event.get("payload", {}).get("cost_usd", 0)
                if cost is not None:
                    total_cost += cost

        return {
            "sources": [s.model_dump() for s in final_state.sources],
            "research_notes": final_state.research_notes,
            "analysis_notes": final_state.analysis_notes,
            "final_answer": final_state.final_answer,
            "latency": latency,
            "cost": total_cost
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Khởi chạy Web UI tại http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
