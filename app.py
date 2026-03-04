#!/usr/bin/env python3
"""
Nyaya Legal Assistant - FastAPI REST API
Provides HTTP endpoints for legal question answering and case lookup.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging
from agent.agno_agent import NyayaAgent
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

# Initialize agent (singleton)
agent = NyayaAgent(show_debug=False)


# Request/Response models
class QueryRequest(BaseModel):
    question: str
    description: Optional[str] = "Legal question about Sri Lankan law"


class QueryResponse(BaseModel):
    question: str
    answer: str
    status: str


class HealthResponse(BaseModel):
    status: str
    version: str


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
def ask_legal_question(request: QueryRequest) -> QueryResponse:
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
        logger.info(f"Processing query: {question[:100]}")
        answer = agent.ask(question)
        
        return QueryResponse(
            question=question,
            answer=answer,
            status="success"
        )
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing your question: {str(e)[:200]}"
        )


# Batch query endpoint
@app.post("/ask-batch")
def ask_batch(requests: list[QueryRequest]):
    """
    Ask multiple legal questions in one request.
    
    Args:
        requests: List of QueryRequest objects
        
    Returns:
        List of QueryResponse objects
    """
    results = []
    for req in requests:
        try:
            result = ask_legal_question(req)
            results.append(result)
        except HTTPException as e:
            results.append({
                "question": req.question,
                "answer": f"Error: {e.detail}",
                "status": "error"
            })
    
    return results


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
    logger.error(f"Unhandled exception: {exc}")
    return HTTPException(
        status_code=500,
        detail="Internal server error"
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
