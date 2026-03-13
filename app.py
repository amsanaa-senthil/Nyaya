#!/usr/bin/env python3
"""
Nyaya Legal Assistant - FastAPI REST API
Provides HTTP endpoints for legal question answering and case lookup.
"""

import json
import logging
import os
import time
import uuid
from threading import Lock
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from agent.agno_agent import NyayaAgent
from analytics_store import AnalyticsEvent, analytics_store
from optimizations import is_valid_query

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Nyaya Legal Assistant API",
    description="Sri Lankan Legal Question Answering System",
    version="1.0.0"
)

# CORS — set CORS_ORIGINS in .env as a comma-separated list of allowed frontend
# URLs (e.g. https://your-app.vercel.app,http://localhost:3000).
# Defaults to "*" only when the env var is absent (local dev).
_raw_cors = os.getenv("CORS_ORIGINS", "")
_cors_origins: list[str] = (
    [o.strip() for o in _raw_cors.split(",") if o.strip()]
    if _raw_cors.strip()
    else ["*"]
)
# allow_credentials must be False when origins includes "*" (browser restriction)
_allow_credentials = "*" not in _cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

_agent_lock = Lock()
_agent_instance: Optional[NyayaAgent] = None


def get_agent() -> NyayaAgent:
    global _agent_instance
    if _agent_instance is not None:
        return _agent_instance

    with _agent_lock:
        if _agent_instance is None:
            _agent_instance = NyayaAgent(show_debug=False)
    return _agent_instance


# Request/Response models
class QueryRequest(BaseModel):
    question: str
    description: Optional[str] = "Legal question about Sri Lankan law"


class QueryResponse(BaseModel):
    question: str
    answer: str
    status: str
    source_map: List[Dict[str, Any]] = Field(default_factory=list)
    precedent_chain: List[Dict[str, Any]] = Field(default_factory=list)
    groundedness_score: float = 0.0
    reflection_report: Dict[str, Any] = Field(default_factory=dict)
    latency_seconds: float = 0.0


class HealthResponse(BaseModel):
    status: str
    version: str


def _to_float(value: Any, default: float = 0.0) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return default


def _to_list_of_dict(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _to_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _log_event(event_name: str, **payload: Any) -> None:
    event = {"event": event_name, **payload}
    logger.info(json.dumps(event, default=str))


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.time()

    try:
        response = await call_next(request)
    except Exception as exc:
        _log_event(
            "request_error",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            error=str(exc),
            latency_seconds=round(time.time() - start, 4),
        )
        raise

    response.headers["X-Request-ID"] = request_id
    _log_event(
        "request_complete",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        latency_seconds=round(time.time() - start, 4),
    )
    return response


# Health check endpoint
@app.get("/health", response_model=HealthResponse)
def health_check():
    """Check API health and status"""
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


# Main query endpoint
@app.post("/ask", response_model=QueryResponse)
def ask_legal_question(request: QueryRequest, http_request: Request) -> QueryResponse:
    """
    Ask a legal question about Sri Lankan law.
    
    Args:
        request: QueryRequest with 'question' field
        
    Returns:
        QueryResponse with answer from NyayaAgent
        
    Raises:
        HTTPException 400: Invalid or empty question
        HTTPException 500: LLM or retrieval error
    """
    question = request.question.strip()
    
    # Validate query
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty"
        )
    
    if not is_valid_query(question):
        raise HTTPException(
            status_code=400,
            detail="Invalid query. Please ask a legal question (not commands or file paths)."
        )
    
    try:
        request_id = getattr(http_request.state, "request_id", "unknown")
        _log_event("ask_started", request_id=request_id, question_preview=question[:100])

        report = get_agent().ask_with_report(question, debug_mode=False)

        answer = report.get("answer", "")
        status = report.get("status", "success")
        
        response = QueryResponse(
            question=question,
            answer=answer if isinstance(answer, str) else str(answer),
            status=status if isinstance(status, str) else "success",
            source_map=_to_list_of_dict(report.get("source_map", [])),
            precedent_chain=_to_list_of_dict(report.get("precedent_chain", [])),
            groundedness_score=_to_float(report.get("groundedness_score", 0.0), 0.0),
            reflection_report=_to_dict(report.get("reflection_report", {})),
            latency_seconds=_to_float(report.get("latency_seconds", 0.0), 0.0),
        )

        analytics_store.record(
            AnalyticsEvent(
                timestamp=time.time(),
                request_id=request_id,
                endpoint="/ask",
                status=response.status,
                groundedness_score=response.groundedness_score,
                latency_seconds=response.latency_seconds,
                fallback_used=response.status == "fallback",
                no_context=response.status in {"no_context", "insufficient_evidence"},
            )
        )
        _log_event(
            "ask_completed",
            request_id=request_id,
            status=response.status,
            groundedness=response.groundedness_score,
            latency_seconds=response.latency_seconds,
        )
        return response
    except Exception as e:
        request_id = getattr(http_request.state, "request_id", "unknown")
        _log_event("ask_failed", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error processing your question: {str(e)[:200]}"
        )


# Batch query endpoint
@app.post("/ask-batch")
def ask_batch(requests: list[QueryRequest], http_request: Request):
    """
    Ask multiple legal questions in one request.
    
    Args:
        requests: List of QueryRequest objects
        
    Returns:
        List of QueryResponse objects
    """
    results = []
    request_id = getattr(http_request.state, "request_id", "unknown")
    for req in requests:
        try:
            result = ask_legal_question(req, http_request)
            results.append(result)
        except HTTPException as e:
            results.append({
                "question": req.question,
                "answer": f"Error: {e.detail}",
                "status": "error"
            })

    _log_event("ask_batch_completed", request_id=request_id, batch_size=len(requests), result_size=len(results))
    
    return results


@app.get("/analytics/summary")
def analytics_summary():
    return analytics_store.summary()


@app.get("/analytics/trends")
def analytics_trends(limit: int = 100):
    return analytics_store.trends(limit=limit)


@app.get("/analytics/dashboard", response_class=HTMLResponse)
def analytics_dashboard():
    summary = analytics_store.summary()
    html = f"""
        <html>
            <head>
                <title>Nyaya Analytics Dashboard</title>
                <style>
                    body {{ font-family: 'Segoe UI', sans-serif; margin: 24px; background: #f4f7f8; color: #1d2a30; }}
                    .grid {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(220px,1fr)); gap: 12px; }}
                    .card {{ background: white; border-radius: 10px; padding: 16px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); }}
                    .label {{ font-size: 12px; color: #5b6b73; text-transform: uppercase; }}
                    .value {{ font-size: 28px; font-weight: 700; margin-top: 8px; }}
                </style>
            </head>
            <body>
                <h1>Nyaya Analytics</h1>
                <div class='grid'>
                    <div class='card'><div class='label'>Total Requests</div><div class='value'>{summary.get('total_requests', 0)}</div></div>
                    <div class='card'><div class='label'>Hit Rate</div><div class='value'>{summary.get('hit_rate', 0.0)}</div></div>
                    <div class='card'><div class='label'>Fallback Rate</div><div class='value'>{summary.get('fallback_rate', 0.0)}</div></div>
                    <div class='card'><div class='label'>Avg Groundedness</div><div class='value'>{summary.get('avg_groundedness', 0.0)}</div></div>
                    <div class='card'><div class='label'>Avg Latency (s)</div><div class='value'>{summary.get('avg_latency_seconds', 0.0)}</div></div>
                </div>
                <p style='margin-top:20px;color:#5b6b73;'>Refresh to see latest values from in-memory telemetry.</p>
            </body>
        </html>
    """
    return HTMLResponse(content=html)


# Info endpoint
@app.get("/info")
def get_info():
    """Get system information"""
    return {
        "name": "Nyaya Legal Assistant",
        "description": "Sri Lankan legal question answering system",
        "version": "1.0.0",
        "endpoints": {
            "health": "GET /health",
            "ask": "POST /ask",
            "batch": "POST /ask-batch",
            "info": "GET /info",
            "docs": "GET /docs"
        },
        "features": [
            "Hybrid retrieval (semantic 60% + BM25 40%)",
            "Citation network analysis via Neo4j",
            "Azure OpenAI (gpt-5-nano) for answers",
            "Query validation and fallback handling"
        ]
    }


# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected errors"""
    request_id = getattr(request.state, "request_id", "unknown")
    _log_event("unhandled_exception", request_id=request_id, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "request_id": request_id},
    )


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🚀 Nyaya Legal Assistant API Starting")
    print("=" * 70)
    print("\nAPI Documentation available at:")
    print("  Interactive Docs: http://localhost:8000/docs")
    print("  ReDoc: http://localhost:8000/redoc")
    print("\nExample request:")
    print('  curl -X POST "http://localhost:8000/ask" \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"question": "What is res judicata in Sri Lankan law?"}\'')
    print("\n" + "=" * 70)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
