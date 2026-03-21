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
from collections import deque
from threading import Lock
from typing import Any, Deque, Dict, Generator, List, Optional

from fastapi import FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, Field

from agent.nyaya_agent import NyayaAgent
from agent.llm import stream_answer
from analytics_store import AnalyticsEvent, analytics_store
from collaboration_store import collaboration_store
from optimizations import is_valid_query

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional API key authentication.
# Set NYAYA_API_KEY in .env to enable. Leave unset for open access (local dev).
_API_KEY = os.getenv("NYAYA_API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_ADMIN_API_KEY = os.getenv("NYAYA_ADMIN_API_KEY", "")
_admin_api_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)


def _require_api_key(key: Optional[str] = Security(_api_key_header)) -> None:
    """FastAPI dependency: enforces X-API-Key when NYAYA_API_KEY is configured."""
    if _API_KEY and key != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


def _require_admin_api_key(key: Optional[str] = Security(_admin_api_key_header)) -> None:
    """FastAPI dependency: enforces X-Admin-Key for sensitive governance endpoints."""
    if _ADMIN_API_KEY and key != _ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing admin API key.")

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


class ChatTurn(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    question: str
    history: List[ChatTurn] = Field(default_factory=list)


class QueryResponse(BaseModel):
    question: str
    answer: str
    status: str
    source_map: List[Dict[str, Any]] = Field(default_factory=list)
    precedent_chain: List[Dict[str, Any]] = Field(default_factory=list)
    groundedness_score: float = 0.0
    reflection_report: Dict[str, Any] = Field(default_factory=dict)
    latency_seconds: float = 0.0
    citation_count: int = 0
    evidence_sufficient: bool = False
    legal_notice: str = "Educational information only; not legal advice."


class HealthResponse(BaseModel):
    status: str
    version: str


class ConversationCreateRequest(BaseModel):
    title: str
    tags: List[str] = Field(default_factory=list)
    matter_id: str = ""
    jurisdiction: str = ""


class ConversationMessageRequest(BaseModel):
    role: str
    content: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_score: float = 0.0


class MessageEditRequest(BaseModel):
    content: str
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_score: Optional[float] = None


class ConversationShareRequest(BaseModel):
    permission: str = "view"
    expires_in_hours: Optional[int] = None
    password: Optional[str] = None


class SharedAccessRequest(BaseModel):
    password: Optional[str] = None


class ConversationCommentRequest(BaseModel):
    content: str
    mentions: List[str] = Field(default_factory=list)
    message_key: Optional[str] = None


class ReviewStatusRequest(BaseModel):
    review_status: str


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


def _validate_question(question: str) -> str:
    cleaned = question.strip()
    if not cleaned:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if not is_valid_query(cleaned):
        raise HTTPException(
            status_code=400,
            detail="Invalid query. Please ask a legal question (not commands or file paths).",
        )
    return cleaned


def _extract_team_id(http_request: Request) -> Optional[str]:
    candidate = (
        http_request.headers.get("X-Team-ID")
        or http_request.headers.get("X-Team-Id")
        or http_request.headers.get("X-Team")
    )
    if not candidate:
        return None
    cleaned = candidate.strip()
    return cleaned[:128] if cleaned else None


def _require_user_id(http_request: Request) -> str:
    user_id = _extract_user_id(http_request)
    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="Missing user identity header. Send X-User-ID.",
        )
    return user_id


_rate_limit_per_minute = max(10, int(os.getenv("NYAYA_RATE_LIMIT_PER_MINUTE", "60")))
_rate_windows: Dict[str, Deque[float]] = {}
_rate_limit_lock = Lock()


def _enforce_rate_limit(http_request: Request, endpoint: str) -> None:
    user_key = _extract_user_id(http_request) or "anonymous"
    team_key = _extract_team_id(http_request) or "public"
    composite = f"{team_key}:{user_key}:{endpoint}"
    now = time.time()
    cutoff = now - 60.0
    with _rate_limit_lock:
        window = _rate_windows.setdefault(composite, deque())
        while window and window[0] < cutoff:
            window.popleft()
        if len(window) >= _rate_limit_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please retry in a minute.",
            )
        window.append(now)


def _build_query_response(question: str, report: Dict[str, Any]) -> QueryResponse:
    answer = report.get("answer", "")
    status = report.get("status", "success")
    return QueryResponse(
        question=question,
        answer=answer if isinstance(answer, str) else str(answer),
        status=status if isinstance(status, str) else "success",
        source_map=_to_list_of_dict(report.get("source_map", [])),
        precedent_chain=_to_list_of_dict(report.get("precedent_chain", [])),
        groundedness_score=_to_float(report.get("groundedness_score", 0.0), 0.0),
        reflection_report=_to_dict(report.get("reflection_report", {})),
        latency_seconds=_to_float(report.get("latency_seconds", 0.0), 0.0),
        citation_count=len(_to_list_of_dict(report.get("source_map", []))),
        evidence_sufficient=_to_float(report.get("groundedness_score", 0.0), 0.0) >= 0.5,
        legal_notice="Educational information only; not legal advice.",
    )


def _record_analytics(endpoint: str, request_id: str, response: QueryResponse) -> None:
    analytics_store.record(
        AnalyticsEvent(
            timestamp=time.time(),
            request_id=request_id,
            endpoint=endpoint,
            status=response.status,
            groundedness_score=response.groundedness_score,
            latency_seconds=response.latency_seconds,
            fallback_used=response.status == "fallback",
            no_context=response.status in {"no_context", "insufficient_evidence"},
        )
    )


def _extract_user_id(http_request: Request) -> Optional[str]:
    """Read frontend user identity from request headers for history tracking."""
    candidate = (
        http_request.headers.get("X-User-ID")
        or http_request.headers.get("X-User-Id")
        or http_request.headers.get("X-User")
    )
    if not candidate:
        return None
    cleaned = candidate.strip()
    if not cleaned:
        return None
    return cleaned[:128]


def _record_user_history(
    *,
    endpoint: str,
    request_id: str,
    user_id: Optional[str],
    question: str,
    answer: str,
    status: str,
) -> None:
    if not user_id:
        return
    analytics_store.record_user_search(
        timestamp=time.time(),
        request_id=request_id,
        user_id=user_id,
        endpoint=endpoint,
        question=question,
        answer_preview=(answer or "")[:280],
        status=status,
    )


def _process_query(
    endpoint: str,
    request_id: str,
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
    user_id: Optional[str] = None,
) -> QueryResponse:
    log_payload: Dict[str, Any] = {
        "request_id": request_id,
        "question_preview": question[:100],
    }
    if history:
        log_payload["history_turns"] = len(history)
    _log_event(f"{endpoint.strip('/').replace('-', '_')}_started", **log_payload)

    report = get_agent().ask_with_report(question, debug_mode=False, history=history)
    response = _build_query_response(question, report)
    _record_analytics(endpoint, request_id, response)
    _record_user_history(
        endpoint=endpoint,
        request_id=request_id,
        user_id=user_id,
        question=question,
        answer=response.answer,
        status=response.status,
    )

    _log_event(
        f"{endpoint.strip('/').replace('-', '_')}_completed",
        request_id=request_id,
        status=response.status,
        groundedness=response.groundedness_score,
        latency_seconds=response.latency_seconds,
    )
    return response


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
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
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
def ask_legal_question(request: QueryRequest, http_request: Request, _auth: None = Security(_require_api_key)) -> QueryResponse:
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
    question = _validate_question(request.question)
    _enforce_rate_limit(http_request, "/ask")
    
    try:
        request_id = getattr(http_request.state, "request_id", "unknown")
        user_id = _extract_user_id(http_request)
        return _process_query("/ask", request_id, question, user_id=user_id)
    except Exception as e:
        request_id = getattr(http_request.state, "request_id", "unknown")
        _log_event("ask_failed", request_id=request_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error processing your question: {str(e)[:200]}"
        )


@app.post("/ask-chat", response_model=QueryResponse)
def ask_chat(request: ChatRequest, http_request: Request, _auth: None = Security(_require_api_key)) -> QueryResponse:
    """
    Multi-turn chat endpoint.
    Pass 'history' as a list of {role, content} turns (last 3 pairs used).
    Returns a full QueryResponse identical to /ask.
    """
    question = _validate_question(request.question)
    _enforce_rate_limit(http_request, "/ask-chat")

    history = [{"role": t.role, "content": t.content} for t in request.history]

    try:
        request_id = getattr(http_request.state, "request_id", "unknown")
        user_id = _extract_user_id(http_request)
        return _process_query("/ask-chat", request_id, question, history=history, user_id=user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:200]}")


@app.post("/ask-stream")
def ask_stream(request: ChatRequest, http_request: Request, _auth: None = Security(_require_api_key)):
    """
    Streaming response endpoint.
    Yields answer tokens as plain text chunks (Server-Sent Events style).
    Pass optional 'history' list of {role, content} for multi-turn context.
    """
    question = _validate_question(request.question)
    _enforce_rate_limit(http_request, "/ask-stream")
    request_id = getattr(http_request.state, "request_id", "unknown")
    user_id = _extract_user_id(http_request)

    # Keep behavior aligned with /ask and /ask-chat by applying the same safety gate.
    agent = get_agent()
    is_safe, safety_reason = agent.safety_filter.check_safety(question)
    if not is_safe:
        refusal = agent.safety_filter.get_refusal_message(safety_reason)
        _record_user_history(
            endpoint="/ask-stream",
            request_id=request_id,
            user_id=user_id,
            question=question,
            answer=refusal,
            status="blocked",
        )
        return StreamingResponse(iter([refusal]), media_type="text/plain")

    history = [{"role": t.role, "content": t.content} for t in request.history]

    # Build the prompt the same way the agent does, but stream the LLM output directly.
    # We reuse the agent's retriever + prompt building by running a lightweight retrieval pass.
    def _generate() -> Generator[str, None, None]:
        collected_chunks: List[str] = []
        try:
            from optimizations import canonicalize_legal_query
            from agent.prompts import SYSTEM_PROMPT
            retrieval_query = canonicalize_legal_query(question)
            chunks = agent.retriever.search(retrieval_query, top_k=3, return_metadata=True)
            context_blocks = []
            for chunk in chunks[:2]:
                if isinstance(chunk, dict):
                    text = chunk.get("text", "")[:1200]
                    pdf = chunk.get("pdf_name", "Unknown")
                    page = chunk.get("page", "?")
                    context_blocks.append(f"TEXT:\n{text}\n\nSOURCE: {pdf}, Page {page}\n---")
            context_text = "\n\n".join(context_blocks)
            prompt = (
                f"{SYSTEM_PROMPT}\n\n**Context:**\n{context_text}\n\n**Question:** {question}\n\nAnswer:"
            )
            for token in stream_answer(prompt, history=history):
                collected_chunks.append(token)
                yield token
            _record_user_history(
                endpoint="/ask-stream",
                request_id=request_id,
                user_id=user_id,
                question=question,
                answer="".join(collected_chunks),
                status="success",
            )
        except Exception as exc:
            _record_user_history(
                endpoint="/ask-stream",
                request_id=request_id,
                user_id=user_id,
                question=question,
                answer=str(exc),
                status="error",
            )
            yield f"\n\n[Error: {str(exc)[:200]}]"

    return StreamingResponse(_generate(), media_type="text/plain")


# Batch query endpoint
@app.post("/ask-batch")
def ask_batch(requests: list[QueryRequest], http_request: Request, _auth: None = Security(_require_api_key)):
    """
    Ask multiple legal questions in one request.
    
    Args:
        requests: List of QueryRequest objects
        
    Returns:
        List of QueryResponse objects
    """
    results = []
    _enforce_rate_limit(http_request, "/ask-batch")
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


@app.get("/history")
def get_history(http_request: Request, limit: int = 50):
    user_id = _require_user_id(http_request)
    return {
        "user_id": user_id,
        "items": analytics_store.get_user_history(user_id, limit=limit),
    }


@app.delete("/history")
def clear_history(http_request: Request):
    user_id = _require_user_id(http_request)
    deleted = analytics_store.clear_user_history(user_id)
    return {"user_id": user_id, "deleted": deleted}


@app.post("/conversations")
def create_conversation(request: ConversationCreateRequest, http_request: Request, _auth: None = Security(_require_api_key)):
    user_id = _require_user_id(http_request)
    created = collaboration_store.create_conversation(
        owner_user_id=user_id,
        title=request.title,
        tags=request.tags,
        matter_id=request.matter_id,
        jurisdiction=request.jurisdiction,
    )
    return created


@app.get("/conversations")
def list_conversations(http_request: Request, limit: int = 50, include_deleted: bool = False, _auth: None = Security(_require_api_key)):
    user_id = _require_user_id(http_request)
    return {
        "items": collaboration_store.list_conversations(
            owner_user_id=user_id,
            include_deleted=include_deleted,
            limit=limit,
        )
    }


@app.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str, http_request: Request, include_history: bool = False, _auth: None = Security(_require_api_key)):
    user_id = _require_user_id(http_request)
    try:
        return collaboration_store.get_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
            include_history=include_history,
            include_deleted=False,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, http_request: Request, _auth: None = Security(_require_api_key)):
    user_id = _require_user_id(http_request)
    try:
        collaboration_store.soft_delete_conversation(user_id=user_id, conversation_id=conversation_id)
        return {"conversation_id": conversation_id, "deleted": True}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/conversations/{conversation_id}/messages")
def add_conversation_message(
    conversation_id: str,
    request: ConversationMessageRequest,
    http_request: Request,
    _auth: None = Security(_require_api_key),
):
    user_id = _require_user_id(http_request)
    try:
        return collaboration_store.add_message(
            user_id=user_id,
            conversation_id=conversation_id,
            role=request.role,
            content=request.content,
            citations=request.citations,
            evidence_score=request.evidence_score,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.patch("/conversations/{conversation_id}/messages/{message_key}")
def edit_conversation_message(
    conversation_id: str,
    message_key: str,
    request: MessageEditRequest,
    http_request: Request,
    _auth: None = Security(_require_api_key),
):
    user_id = _require_user_id(http_request)
    try:
        return collaboration_store.edit_message(
            user_id=user_id,
            conversation_id=conversation_id,
            message_key=message_key,
            content=request.content,
            citations=request.citations,
            evidence_score=request.evidence_score,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/conversations/{conversation_id}/share")
def create_share_link(
    conversation_id: str,
    request: ConversationShareRequest,
    http_request: Request,
    _auth: None = Security(_require_api_key),
):
    user_id = _require_user_id(http_request)
    try:
        return collaboration_store.create_share_link(
            user_id=user_id,
            conversation_id=conversation_id,
            permission=request.permission,
            expires_in_hours=request.expires_in_hours,
            password=request.password,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/shares/{share_token}/access")
def access_shared_conversation(
    share_token: str,
    request: SharedAccessRequest,
    http_request: Request,
    _auth: None = Security(_require_api_key),
):
    accessor = _extract_user_id(http_request) or "share-access-user"
    try:
        return collaboration_store.access_shared_conversation(
            accessor_user_id=accessor,
            share_token=share_token,
            password=request.password,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/conversations/{conversation_id}/share/{share_token}/revoke")
def revoke_share_link(
    conversation_id: str,
    share_token: str,
    http_request: Request,
    _auth: None = Security(_require_api_key),
):
    user_id = _require_user_id(http_request)
    try:
        return collaboration_store.revoke_share(
            user_id=user_id,
            conversation_id=conversation_id,
            share_token=share_token,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.get("/conversations/{conversation_id}/export")
def export_conversation(conversation_id: str, http_request: Request, include_history: bool = False, _auth: None = Security(_require_api_key)):
    user_id = _require_user_id(http_request)
    try:
        return collaboration_store.export_conversation(
            user_id=user_id,
            conversation_id=conversation_id,
            include_history=include_history,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.post("/conversations/{conversation_id}/comments")
def add_conversation_comment(
    conversation_id: str,
    request: ConversationCommentRequest,
    http_request: Request,
    _auth: None = Security(_require_api_key),
):
    user_id = _require_user_id(http_request)
    try:
        return collaboration_store.add_comment(
            user_id=user_id,
            conversation_id=conversation_id,
            content=request.content,
            mentions=request.mentions,
            message_key=request.message_key,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@app.patch("/conversations/{conversation_id}/review-status")
def update_review_status(
    conversation_id: str,
    request: ReviewStatusRequest,
    http_request: Request,
    _auth: None = Security(_require_api_key),
):
    user_id = _require_user_id(http_request)
    try:
        return collaboration_store.set_review_status(
            user_id=user_id,
            conversation_id=conversation_id,
            review_status=request.review_status,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/collaboration/audit")
def collaboration_audit(
    http_request: Request,
    limit: int = 100,
    _auth: None = Security(_require_api_key),
    _admin_auth: None = Security(_require_admin_api_key),
):
    user_id = _require_user_id(http_request)
    return {"items": collaboration_store.get_audit_events(user_id=user_id, limit=limit)}


@app.post("/governance/purge")
def governance_purge(
    http_request: Request,
    deleted_older_than_days: int = 30,
    expired_share_older_than_days: int = 7,
    _auth: None = Security(_require_api_key),
    _admin_auth: None = Security(_require_admin_api_key),
):
    user_id = _require_user_id(http_request)
    return collaboration_store.purge_data(
        user_id=user_id,
        deleted_older_than_days=deleted_older_than_days,
        expired_share_older_than_days=expired_share_older_than_days,
    )


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
            "ask_chat": "POST /ask-chat (multi-turn, pass history[])",
            "ask_stream": "POST /ask-stream (token streaming)",
            "batch": "POST /ask-batch",
            "conversations": "POST/GET /conversations",
            "conversation_detail": "GET/DELETE /conversations/{conversation_id}",
            "conversation_messages": "POST /conversations/{conversation_id}/messages",
            "conversation_message_edit": "PATCH /conversations/{conversation_id}/messages/{message_key}",
            "conversation_share": "POST /conversations/{conversation_id}/share",
            "share_access": "POST /shares/{share_token}/access",
            "share_revoke": "POST /conversations/{conversation_id}/share/{share_token}/revoke",
            "conversation_export": "GET /conversations/{conversation_id}/export",
            "conversation_comments": "POST /conversations/{conversation_id}/comments",
            "review_status": "PATCH /conversations/{conversation_id}/review-status",
            "collaboration_audit": "GET /collaboration/audit",
            "governance_purge": "POST /governance/purge",
            "info": "GET /info",
            "docs": "GET /docs"
        },
        "features": [
            "Hybrid retrieval (semantic 60% + BM25 40%)",
            "Cross-encoder re-ranking (set NYAYA_RERANKER=1)",
            "Citation network analysis via Neo4j",
            "Azure OpenAI (gpt-5-nano) for answers with Gemini fallback",
            "Multi-turn chat history via /ask-chat",
            "Token streaming via /ask-stream",
            "Optional API key auth (set NYAYA_API_KEY)",
            "Query validation and fallback handling",
            "SQLite-backed analytics persistence",
            "Conversation sharing (view/comment/edit) with expiry/revoke",
            "Message versioning and review workflow states",
            "Conversation comments with mentions",
            "Conversation export for handoff/audit",
            "Collaboration audit log and retention purge endpoint",
            "Per-user/team endpoint rate limiting",
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
