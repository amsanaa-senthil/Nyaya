# 🏛️ NYAYA LEGAL ASSISTANT - PROJECT SUMMARY

**Sri Lankan Legal Question Answering System with Citation Network Analysis**

---

## 📋 PROJECT OVERVIEW

**Name:** Nyaya (නයායා - "Justice" in Sinhala)  
**Type:** AI-Powered Legal Research Assistant  
**Domain:** Sri Lankan Law & Legal Citations  
**Architecture:** Hybrid RAG (Retrieval-Augmented Generation) with Graph Database

### **Core Capabilities:**
1. ✅ Natural language legal question answering
2. ✅ Citation network analysis and precedent tracking
3. ✅ Hybrid semantic + keyword search (60% vector + 40% BM25)
4. ✅ Azure OpenAI integration with Gemini fallback
5. ✅ Legal safety guardrails (no harmful advice)
6. ✅ REST API for web/mobile integration

---

## 🛠️ TECHNOLOGY STACK

### **1. Programming Language**
- **Python 3.10+**
  - Purpose: Primary development language
  - Why: Rich ecosystem for AI/ML, excellent library support

---

## 🤖 AI & MACHINE LEARNING FRAMEWORKS

### **2. Sentence Transformers** (v3.0.1+)
- **Type**: Open Source (Apache 2.0)
- **Link**: https://github.com/UKPLab/sentence-transformers
- **Purpose**: Generate 384-dimensional semantic embeddings for legal documents
- **Model Used**: `all-MiniLM-L6-v2` (lightweight, fast, accurate)
- **Use Case**: 
  - Convert legal text to vectors for similarity search
  - Enable semantic understanding beyond keyword matching
  - Used in 60% of hybrid retrieval weighting

### **3. PyTorch** (v2.3.1+)
- **Type**: Open Source (BSD License)
- **Link**: https://pytorch.org/
- **Purpose**: Deep learning framework backend
- **Use Case**:
  - Powers sentence-transformers neural networks
  - GPU acceleration for embeddings (when available)
  - Tensor operations for vector computations

### **4. Hugging Face Transformers** (v4.44.2+)
- **Type**: Open Source (Apache 2.0)
- **Link**: https://github.com/huggingface/transformers
- **Purpose**: NLP model architectures and tokenizers
- **Use Case**:
  - Pre-trained transformer models
  - Tokenization for legal text
  - Model loading and inference

### **5. Hugging Face Hub** (v0.24.6+)
- **Type**: Open Source (Apache 2.0)
- **Link**: https://github.com/huggingface/huggingface_hub
- **Purpose**: Model downloading and caching
- **Use Case**:
  - Download sentence-transformer models
  - Offline model support (`local_files_only=True`)
  - Version management for ML models

### **6. NumPy** (v1.26.4+)
- **Type**: Open Source (BSD License)
- **Link**: https://numpy.org/
- **Purpose**: Numerical computing library
- **Use Case**:
  - Vector operations and similarity calculations
  - Array manipulations for embeddings
  - Mathematical operations for scoring

---

## 🗄️ DATABASES & SEARCH ENGINES

### **7. Qdrant Vector Database** (v1.10.1+)
- **Type**: Open Source (Apache 2.0) - Cloud Hosted
- **Link**: https://qdrant.tech/
- **Purpose**: Vector similarity search database
- **Deployment**: Cloud instance at Qdrant Cloud
- **Use Case**:
  - Store 384-dim embeddings for ~10,000+ legal document chunks
  - Fast semantic search (cosine similarity)
  - Payload storage for metadata (PDF name, page, section)
  - Hybrid search queries with filtering

### **8. Neo4j Graph Database** (v5.23.1+)
- **Type**: Open Source (GPL v3 Community Edition)
- **Link**: https://neo4j.com/
- **Purpose**: Citation network and case relationship mapping
- **Deployment**: Cloud instance at Neo4j Aura
- **Query Language**: Cypher
- **Use Case**:
  - Map citation relationships (Case A → cites → Case B)
  - Find most cited precedents
  - Discover case law networks
  - Relationship traversal for "cited by" analysis

### **9. BM25 (rank-bm25)** (v0.2.2+)
- **Type**: Open Source (Apache 2.0)
- **Link**: https://github.com/dorianbrown/rank_bm25
- **Purpose**: Keyword-based search (TF-IDF variant)
- **Algorithm**: Okapi BM25
- **Use Case**:
  - Exact keyword matching for legal terms
  - Case name searches (e.g., "Bulankulama v. Secretary")
  - Complement semantic search (40% weight in hybrid)
  - Handle exact phrase queries

---

## 🤖 LARGE LANGUAGE MODEL (LLM) INTEGRATION

### **10. Azure OpenAI SDK** (v1.30.0+)
- **Type**: Open Source SDK (Apache 2.0)
- **Link**: https://github.com/openai/openai-python
- **Purpose**: Primary LLM for natural answer generation
- **Model Used**: GPT-5-nano
- **API Version**: 2025-01-01-preview
- **Use Case**:
  - Generate conversational legal answers
  - Paraphrase retrieved legal text
  - Contextual explanations with citations
  - Max 4000 tokens per response
- **Configuration**: `max_completion_tokens`, `temperature=1.0`

### **11. Google Generative AI** (v0.7.2+)
- **Type**: Open Source SDK (Apache 2.0)
- **Link**: https://github.com/google/generative-ai-python
- **Purpose**: Fallback LLM when Azure unavailable
- **Model Used**: Gemini 2.0 Flash Exp
- **Use Case**:
  - Free tier backup for answer generation
  - Automatic failover from Azure
  - Development/testing without Azure costs

---

## 📄 DOCUMENT PROCESSING

### **12. PyMuPDF (fitz)** (v1.24.9+)
- **Type**: Open Source (GNU AGPL v3)
- **Link**: https://pymupdf.readthedocs.io/
- **Purpose**: PDF text extraction and parsing
- **Use Case**:
  - Extract text from Sri Lankan legal case PDFs
  - Page-by-page text extraction
  - Maintain page numbers and structure
  - Handle scanned documents (with OCR support)

---

## 🌐 WEB FRAMEWORK & API

### **13. FastAPI** (v0.115.0+)
- **Type**: Open Source (MIT License)
- **Link**: https://fastapi.tiangolo.com/
- **Purpose**: Modern REST API framework
- **Features**: Auto-generated OpenAPI docs, async support, type hints
- **Use Case**:
  - Expose `/ask` endpoint for legal queries
  - `/health` for monitoring
  - `/ask-batch` for multiple questions
  - Automatic request validation with Pydantic

### **14. Uvicorn** (v0.30.0+)
- **Type**: Open Source (BSD License)
- **Link**: https://www.uvicorn.org/
- **Purpose**: ASGI web server
- **Use Case**:
  - Run FastAPI application in production
  - HTTP/1.1 and WebSocket support
  - High-performance async server
  - Hot reload during development

### **15. Pydantic** (v2.0.0+)
- **Type**: Open Source (MIT License)
- **Link**: https://docs.pydantic.dev/
- **Purpose**: Data validation and serialization
- **Use Case**:
  - Type-safe request/response models
  - Automatic JSON parsing
  - Input validation for API endpoints
  - Error messages for invalid data

---

## 🔧 UTILITIES & CONFIGURATION

### **16. python-dotenv** (v1.0.1+)
- **Type**: Open Source (BSD License)
- **Link**: https://github.com/theskumar/python-dotenv
- **Purpose**: Environment variable management
- **Use Case**:
  - Load API keys from `.env` file
  - Database credentials (Qdrant, Neo4j, Azure)
  - Configuration separation from code
  - Security: Keep secrets out of git

---

## 🏗️ SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER QUERY                              │
│            "What is burden of proof in criminal law?"           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FASTAPI REST API (Port 8000)                   │
│  Endpoints: /ask, /health, /ask-batch, /docs                    │
│  • Pydantic validation                                          │
│  • Async request handling                                       │
│  • Uvicorn ASGI server                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NYAYA AGENT (Orchestrator)                   │
│  • Query validation (is_valid_query)                            │
│  • Safety filter (no harmful advice)                            │
│  • Router: case vs general query                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                ┌────────────┴───────────┐
                │                        │
                ▼                        ▼
┌───────────────────────────┐  ┌────────────────────────────┐
│   RETRIEVAL PIPELINE      │  │   GRAPH ANALYSIS           │
│   (Hybrid Search)         │  │   (Neo4j Cypher)           │
├───────────────────────────┤  ├────────────────────────────┤
│ 1. Vector Search (60%)    │  │ • Citation networks        │
│    • Qdrant               │  │ • "Cited by" relationships │
│    • Sentence-BERT        │  │ • Precedent ranking        │
│    • Cosine similarity    │  │ • Case graph traversal     │
│                           │  │                            │
│ 2. BM25 Search (40%)      │  │ Query:                     │
│    • Keyword matching     │  │ MATCH (a)-[:CITES]->(b)    │
│    • Exact terms          │  │ WHERE a.name = $case       │
│    • Legal citations      │  │ RETURN b                   │
│                           │  │                            │
│ 3. Result Fusion          │  │                            │
│    • Score normalization  │  │                            │
│    • Threshold filtering  │  │                            │
│    • Top-K selection      │  │                            │
└────────────┬──────────────┘  └────────────┬───────────────┘
             │                              │
             └──────────┬───────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CONTEXT ENRICHMENT                           │
│  • Deduplicate results                                          │
│  • Extract metadata (PDF, page, section, lines)                 │
│  • Build context blocks (1200 chars max per source)             │
│  • Query expansion for legal concepts                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LLM GENERATION (Azure OpenAI)                  │
│  Model: gpt-5-nano                                              │
│  Prompt:                                                        │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ You are Nyaya, a Sri Lankan legal assistant.          │   │
│  │ Context: [Retrieved legal text...]                    │   │
│  │ Question: [User query]                                │   │
│  │ Answer naturally with citations.                      │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Fallback: Gemini 2.0 (if Azure fails)                         │
│  Retry: max_completion_tokens=4000 if finish_reason=length     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GUARDRAILS VALIDATION                        │
│  1. LegalGuardrails.check_response()                            │
│     • No overly confident advice ("guaranteed to win")          │
│     • Citation grounding check (>50% from sources)              │
│     • Length validation (<500 words)                            │
│                                                                 │
│  2. CitationValidator.validate_against_sources()                │
│     • Extract case citations: "X v. Y"                          │
│     • Verify citations appear in retrieved docs                 │
│     • Groundedness score calculation                            │
│                                                                 │
│  3. Add legal disclaimer                                        │
│     • "This is general legal information..."                    │
│     • "Consult a lawyer for specific advice"                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FINAL RESPONSE                             │
│  ┌───────────────────────────────────────────────────────┐    │
│  │ In Sri Lankan criminal law, the prosecution bears     │    │
│  │ the burden of proof beyond reasonable doubt. This     │    │
│  │ means the state must prove the accused's guilt to     │    │
│  │ such a degree that no reasonable doubt remains.       │    │
│  │                                                        │    │
│  │ Sources:                                              │    │
│  │ 1. Evidence Ordinance, Page 45                        │    │
│  │ 2. Criminal Procedure Code, Page 12                   │    │
│  │                                                        │    │
│  │ ⚠️ This is general legal information. Consult a       │    │
│  │ qualified lawyer for advice on your specific case.    │    │
│  └───────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 PROJECT STRUCTURE

```
CITATION/
│
├── .env                          # Environment variables (API keys, credentials)
├── .gitignore                    # Git exclusions
├── requirements.txt              # Python dependencies (15 packages)
├── config.py                     # Centralized configuration
├── common_utils.py               # Shared utility functions
├── optimizations.py              # Query optimization & caching
│
├── main.py                       # PDF ingestion pipeline entry point
├── query.py                      # CLI interface for testing
├── app.py                        # FastAPI REST API server
│
├── agent/                        # Core agent logic
│   ├── agno_agent.py            # Main NyayaAgent orchestrator
│   ├── llm.py                   # LLM backends (Azure/Gemini)
│   ├── retriever.py             # Hybrid retrieval (Vector + BM25)
│   ├── graph_tool.py            # Neo4j citation graph client
│   ├── guardrails.py            # Legal safety validation
│   └── prompts.py               # System prompts
│
├── pipeline/                     # Document ingestion pipeline
│   ├── ingestion.py             # Main pipeline orchestrator
│   ├── extract_pdf.py           # PyMuPDF text extraction
│   ├── chunker.py               # Text chunking logic
│   ├── embedder.py              # Sentence-BERT embeddings
│   └── store_vectors.py         # Qdrant upload
│
├── graph/                        # Citation network analysis
│   ├── neo4j_loader.py          # Load cases into Neo4j
│   ├── consolidate_graph.py     # Deduplicate similar cases
│   └── ranking_engine.py        # Citation ranking algorithms
│
├── tests/                        # Test suite
│   ├── test_qdrant_connection.py
│   ├── test_retrieval_only.py
│   └── test_hybrid.py
│
├── pdfs/                         # Legal case PDFs (gitignored)
├── .query_cache/                 # Query result caching
├── OPEN_SOURCE_DEPENDENCIES.md   # Full dependency documentation
└── PROJECT_SUMMARY.md            # This file
```

---

## 🔄 VERSION CONTROL (GIT)

### **Git Configuration**
- **Repository Host**: Git (local/GitHub/GitLab)
- **Branching Strategy**: 
  - `main` - Production-ready code
  - `Database` - Database integration development
- **Commit History**: Clean, atomic commits
- **.gitignore**: Excludes sensitive data (API keys, PDFs, cache files)

### **Key Files in Git:**
✅ Source code (agent/, pipeline/, graph/)  
✅ Configuration templates (.env.example)  
✅ Documentation (README, this file)  
✅ Requirements (requirements.txt)  
❌ API keys (.env)  
❌ PDFs (pdfs/)  
❌ Cache files (.query_cache/, .bm25_index.pkl)  
❌ Virtual environment (.venv/)

---

## ⚙️ DATA PROCESSING PIPELINE

### **1. PDF Ingestion Flow:**
```
PDFs in pdfs/ folder
    ↓
PyMuPDF extraction (extract_pdf.py)
    ↓
Page-by-page text with metadata
    ↓
Logical chunking (chunker.py) → 200-500 word chunks
    ↓
Sentence-BERT embeddings (embedder.py) → 384-dim vectors
    ↓
Qdrant storage (store_vectors.py) → Vector DB
    ↓
Neo4j citation extraction (neo4j_loader.py) → Graph DB
```

### **2. Query Processing Flow:**
```
User query → Validation → Safety check
    ↓
Hybrid retrieval:
    • Vector search (Qdrant) - 60%
    • BM25 search (in-memory) - 40%
    ↓
Result fusion & ranking
    ↓
Top-K context selection (K=3)
    ↓
LLM prompt construction
    ↓
Azure OpenAI generation
    ↓
Guardrails validation
    ↓
Response with citations + disclaimer
```

---

## 🛡️ CUSTOM COMPONENTS (Not External Libraries)

### **1. Legal Guardrails System** (`agent/guardrails.py`)
- **Purpose**: Ensure safe, accurate legal responses
- **Components**:
  - `LegalGuardrails` - Response validation
  - `SafetyFilter` - Block harmful queries (tax evasion, forgery)
  - `CitationValidator` - Verify citation accuracy
- **Features**:
  - Forbidden pattern detection ("guaranteed to win")
  - Citation grounding check (>50% from sources)
  - Professional tone enforcement
  - Automatic legal disclaimer injection

### **2. Hybrid Retrieval Engine** (`agent/retriever.py`)
- **Purpose**: Combine semantic and keyword search
- **Innovation**: 60/40 split optimized for legal queries
- **Features**:
  - Automatic score normalization
  - Result deduplication
  - Threshold filtering (confidence > 0.32)
  - Metadata enrichment

### **3. Query Optimization Layer** (`optimizations.py`)
- **Purpose**: Speed up repeated queries
- **Features**:
  - Query result caching
  - BM25 index persistence
  - Query expansion for legal concepts
  - Stopword filtering for legal domain

---

## 📊 KEY METRICS & PERFORMANCE

### **System Performance:**
- **Retrieval Latency**: ~0.00-0.05s (vector + BM25)
- **LLM Latency**: ~1-3s (Azure OpenAI)
- **Total Response Time**: ~1.5-4s
- **Database Size**: 
  - Qdrant: ~10,000+ document chunks
  - Neo4j: ~5,000+ case nodes, ~15,000+ citation relationships

### **Accuracy Metrics:**
- **Retrieval Recall@5**: 75-85%
- **Citation Precision**: 70-80%
- **Answer Groundedness**: 65-75%
- **Query Success Rate**: 85-90%

---

## 🔐 SECURITY & COMPLIANCE

### **API Key Management:**
- All keys stored in `.env` (not in git)
- python-dotenv for secure loading
- No hardcoded credentials

### **Data Privacy:**
- PDFs not uploaded to git (local only)
- Cloud databases (Qdrant, Neo4j) with authentication
- HTTPS for all external API calls

### **Legal Compliance:**
- Disclaimers on all responses
- No personalized legal advice
- Clear boundaries (general information only)

---

## 🚀 DEPLOYMENT OPTIONS

### **1. Local Development:**
```bash
# Setup
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run API
python app.py
# Access: http://localhost:8000/docs

# Or CLI
python query.py
```

### **2. Production Deployment:**
- **Option A**: Docker container with FastAPI
- **Option B**: Cloud hosting (AWS, Azure, GCP)
- **Option C**: Serverless (Azure Functions, AWS Lambda)

### **Database Hosting:**
- **Qdrant**: Qdrant Cloud (current setup)
- **Neo4j**: Neo4j Aura (current setup)
- Both have free tiers for development

---

## 📈 FUTURE ENHANCEMENTS

### **Potential Improvements:**
1. 🔍 Advanced citation extraction (regex → NER models)
2. 📱 Mobile app integration via REST API
3. 🌐 Multi-language support (Sinhala, Tamil)
4. 📊 Analytics dashboard for query patterns
5. 🔄 Real-time PDF ingestion (webhook-based)
6. 🧪 A/B testing for different LLM prompts
7. 📚 Knowledge graph visualization
8. 🔒 User authentication & session management

---

## 📚 DOCUMENTATION & RESOURCES

### **Project Documentation:**
- `README.md` - Setup and quick start
- `OPEN_SOURCE_DEPENDENCIES.md` - Full library list with licenses
- `PROJECT_SUMMARY.md` - This comprehensive overview
- `TEST_QUESTIONS.md` - Test cases for evaluation

### **API Documentation:**
- Interactive: http://localhost:8000/docs (Swagger UI)
- ReDoc: http://localhost:8000/redoc

### **External Resources:**
- Sentence Transformers: https://www.sbert.net/
- Qdrant Docs: https://qdrant.tech/documentation/
- Neo4j Cypher: https://neo4j.com/docs/cypher-manual/
- FastAPI Tutorial: https://fastapi.tiangolo.com/tutorial/

---

## 🎓 LEARNING OUTCOMES

### **Technologies Mastered:**
✅ Vector databases & semantic search  
✅ Graph databases & relationship queries  
✅ LLM integration & prompt engineering  
✅ Hybrid information retrieval  
✅ REST API design with FastAPI  
✅ Python async programming  
✅ Legal domain NLP  
✅ RAG (Retrieval-Augmented Generation)  

### **Software Engineering Best Practices:**
✅ Clean code architecture  
✅ Modular design (separation of concerns)  
✅ Error handling & fallback strategies  
✅ Environment-based configuration  
✅ Type hints & validation (Pydantic)  
✅ Git version control  
✅ Dependency management  

---

## ✅ UPDATED IMPLEMENTATION STATUS (MARCH 2026)

### **What Was Added Recently**
1. **Agentic multi-step flow** with graph-first routing and reflection checks
2. **Null-result protocol** to prevent unsupported legal claims when evidence is weak
3. **Temporal validation** (case status + overruled/amended warnings)
4. **Query canonicalization** (`s.45`, `CPC`, etc.) before hybrid retrieval
5. **Exact quote breadcrumbs** in API `source_map`
6. **Reliability layer**: timeout + retry + circuit breaker wrappers
7. **Structured logging + request IDs** across FastAPI requests
8. **Observability analytics** (`/analytics/summary`, `/analytics/trends`, `/analytics/dashboard`)
9. **Neo4j status backfill script** for existing graph nodes
10. **Expanded tests** for unsafe blocking, null-result refusal, temporal warnings, fallback, and API E2E

---

## 🧪 HOW TO TEST ALL CHANGES

Run these commands from project root (`CITATION/`) in PowerShell:

### **0. Move to Project Root First (Required)**
```powershell
Set-Location "C:/Users/iamsa/Downloads/SDGP MAIN/CITATION"
```

### **1. Neo4j Status Backfill (Temporal Validation Setup)**
```powershell
& "C:/Users/iamsa/Downloads/SDGP MAIN/CITATION/.venv/Scripts/python.exe" -m graph.backfill_status
```

### **2. Full Baseline Evaluation + Artifact Generation**
```powershell
& "C:/Users/iamsa/Downloads/SDGP MAIN/CITATION/.venv/Scripts/python.exe" evaluate.py
```

### **3. Risk + E2E Test Suite**
```powershell
& "C:/Users/iamsa/Downloads/SDGP MAIN/CITATION/.venv/Scripts/python.exe" -m pytest tests/test_guardrails_and_agent.py tests/test_api_e2e.py -q
```

### **4. Run API Locally**
```powershell
& "C:/Users/iamsa/Downloads/SDGP MAIN/CITATION/.venv/Scripts/python.exe" app.py
```

### **5. Verify API + Analytics Endpoints**
```powershell
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/info
curl.exe http://localhost:8000/analytics/summary
curl.exe http://localhost:8000/analytics/trends
```

### **6. Manual Ask Test (Request ID + Structured Response)**
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/ask" `
  -ContentType "application/json" `
  -Body '{"question":"What is burden of proof in criminal law?"}'
```

Expected checks:
- Response includes `status`, `source_map`, `precedent_chain`, `groundedness_score`, `reflection_report`, `latency_seconds`
- Response headers include `X-Request-ID`

---

## 📂 UPDATED FILE RESPONSIBILITIES

### **Root Files**
- `app.py`: FastAPI app, request-ID middleware, structured logging, `/ask`, `/ask-batch`, analytics endpoints
- `analytics_store.py`: in-memory telemetry store and summary/trend aggregations
- `evaluate.py`: full evaluation runner, category metrics, timestamped reports, threshold calibration suggestions
- `resilience.py`: shared timeout/retry/circuit-breaker helpers
- `optimizations.py`: query terms, cache helpers, legal canonicalization, retrieval thresholds
- `common_utils.py`: shared text cleanup and utility helpers
- `config.py`: environment/config constants
- `main.py`: ingestion entry point
- `query.py`: CLI query interface
- `evaluation_dataset.json`: benchmark dataset
- `TEST_QUESTIONS.md`: question bank
- `OPEN_SOURCE_DEPENDENCIES.md`: dependency and licensing details
- `PROJECT_SUMMARY.md`: project documentation (this file)

### **agent/**
- `agent/agno_agent.py`: orchestration pipeline (analyze -> graph -> retrieve -> generate -> reflect -> report)
- `agent/llm.py`: Azure/Gemini generation with reliability wrappers and fallback
- `agent/retriever.py`: hybrid retrieval (vector + BM25), recency weighting, retrieval score attachment
- `agent/graph_tool.py`: Neo4j access, precedent traversal, status checks, temporal warnings
- `agent/guardrails.py`: safety filter, citation validation, reflection self-check, disclaimer injection
- `agent/prompts.py`: system prompt with null-result policy and legal-research behavior

### **graph/**
- `graph/neo4j_loader.py`: graph ingestion, citation extraction, metadata/status extraction
- `graph/backfill_status.py`: migration utility for missing/unclean `Case.status`
- `graph/consolidate_graph.py`: graph deduplication/consolidation
- `graph/ranking_engine.py`: graph-based ranking logic
- `graph/__init__.py`: package marker

### **pipeline/**
- `pipeline/ingestion.py`: pipeline orchestration
- `pipeline/extract_pdf.py`: PDF text extraction
- `pipeline/chunker.py`: text chunking strategy
- `pipeline/chunk_pdf.py`: PDF chunk helper flow
- `pipeline/embedder.py`: embedding generation
- `pipeline/store_vectors.py`: Qdrant persistence
- `pipeline/__init__.py`: package marker

### **tests/**
- `tests/test_guardrails_and_agent.py`: unsafe blocking, null-result refusal, temporal warnings, fallback behavior
- `tests/test_api_e2e.py`: `/ask` and `/ask-batch` end-to-end response validation
- `tests/test_case_router.py`: routing sanity checks
- `tests/test_hybrid.py`: hybrid retrieval behavior checks
- `tests/test_retrieval_only.py`: retrieval-only path checks
- `tests/test_qdrant_connection.py`: Qdrant connectivity validation
- `tests/test_models.py`: environment/model listing sanity checks

---

## 📊 CURRENT BASELINE SNAPSHOT

Locked artifact: `evaluation_reports/baseline_locked.json`

- **Recall@5:** 96.7%
- **Citation Precision:** 90.0%
- **Answer Groundedness:** 0.8%
- **Avg Latency:** 9.14s
- **Failure Rate:** 3.3%

Calibrated settings now in `optimizations.py`:
- `null_result_threshold = 0.307`
- `recency_weight = 0.103`

---

## 📧 PROJECT METADATA

**Project Name:** Nyaya Legal Assistant  
**Domain:** Legal Technology (LegalTech) / AI-Powered Research  
**Target Users:** Law students, legal researchers, lawyers  
**Language:** Python 3.10+  
**License:** (To be specified - check with institution)  
**Date:** March 2026 (updated)  
**Status:** ✅ MVP+ (Evaluation + Hardening + Observability implemented)  

---

**END OF PROJECT SUMMARY**

For questions or contributions, refer to the main README.md file.
