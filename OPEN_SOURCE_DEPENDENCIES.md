# 📚 Open Source Technologies Used in Nyaya Legal Assistant

This project leverages the following open source frameworks, libraries, and tools:

---

## 🧠 **AI & Machine Learning Frameworks**

### **1. Sentence Transformers** (v3.0+)
- **Purpose**: Generate semantic embeddings for legal documents
- **Model Used**: `all-MiniLM-L6-v2` (384-dimensional embeddings)
- **License**: Apache 2.0
- **Link**: https://github.com/UKPLab/sentence-transformers
- **Use Case**: Converting legal text to vectors for semantic search

### **2. PyTorch** (v2.3+)
- **Purpose**: Deep learning backend for sentence-transformers
- **License**: BSD-style
- **Link**: https://pytorch.org/
- **Use Case**: Neural network computations for embeddings

### **3. Transformers (Hugging Face)** (v4.44+)
- **Purpose**: NLP model architectures and tokenizers
- **License**: Apache 2.0
- **Link**: https://github.com/huggingface/transformers
- **Use Case**: Underlying transformer models for embeddings

---

## 🗄️ **Database & Search Technologies**

### **4. Qdrant** (v1.10+)
- **Purpose**: Vector database for semantic search
- **Features**: Cloud-hosted, similarity search, hybrid filtering
- **License**: Apache 2.0
- **Link**: https://qdrant.tech/
- **Use Case**: Storing and retrieving 384-dim document embeddings

### **5. Neo4j** (v5.23+)
- **Purpose**: Graph database for citation network analysis
- **Features**: Cypher query language, relationship traversal
- **License**: GPL v3 (Community Edition)
- **Link**: https://neo4j.com/
- **Use Case**: Mapping case citations and legal precedent relationships

### **6. BM25 (rank-bm25)** (v0.2+)
- **Purpose**: Traditional keyword-based search (TF-IDF variant)
- **License**: Apache 2.0
- **Link**: https://github.com/dorianbrown/rank_bm25
- **Use Case**: Lexical search for exact keyword matching (40% weight in hybrid)

---

## 🤖 **Large Language Model APIs**

### **7. OpenAI Python SDK** (v1.30+)
- **Purpose**: Azure OpenAI integration (GPT-5-nano)
- **License**: Apache 2.0
- **Link**: https://github.com/openai/openai-python
- **Use Case**: Generating natural language answers from legal context

### **8. Google Generative AI** (v0.7+)
- **Purpose**: Gemini API fallback (free tier)
- **License**: Apache 2.0
- **Link**: https://github.com/google/generative-ai-python
- **Use Case**: Backup LLM when Azure unavailable

---

## 📄 **Document Processing**

### **9. PyMuPDF (fitz)** (v1.24+)
- **Purpose**: PDF text extraction and parsing
- **License**: GNU AGPL v3
- **Link**: https://pymupdf.readthedocs.io/
- **Use Case**: Extracting text from Sri Lankan legal case PDFs

---

## 🌐 **Web Framework & API**

### **10. FastAPI** (v0.115+)
- **Purpose**: REST API framework for HTTP endpoints
- **License**: MIT
- **Link**: https://fastapi.tiangolo.com/
- **Use Case**: Exposing `/ask`, `/health`, `/batch` endpoints

### **11. Uvicorn** (v0.30+)
- **Purpose**: ASGI web server for FastAPI
- **License**: BSD
- **Link**: https://www.uvicorn.org/
- **Use Case**: Running production HTTP server

### **12. Pydantic** (v2.0+)
- **Purpose**: Data validation and serialization
- **License**: MIT
- **Link**: https://docs.pydantic.dev/
- **Use Case**: Request/response models with type checking

---

## 🛠️ **Utilities & Infrastructure**

### **13. python-dotenv** (v1.0+)
- **Purpose**: Environment variable management from `.env` files
- **License**: BSD
- **Link**: https://github.com/theskumar/python-dotenv
- **Use Case**: Loading API keys, database credentials securely

### **14. NumPy** (v1.26+)
- **Purpose**: Numerical computations and array operations
- **License**: BSD
- **Link**: https://numpy.org/
- **Use Case**: Vector operations for embeddings and similarity scores

### **15. Hugging Face Hub** (v0.24+)
- **Purpose**: Model downloading and caching
- **License**: Apache 2.0
- **Link**: https://github.com/huggingface/huggingface_hub
- **Use Case**: Downloading sentence-transformer models offline

---

##  **System Architecture Summary**

```
┌─────────────────────────────────────────────────────────┐
│  USER QUERY                                             │
└────────────────┬────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────┐
│  FastAPI (REST API)                                     │
│  - Uvicorn (ASGI Server)                                │
│  - Pydantic (Type Validation)                           │
└────────────────┬────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────┐
│  NYAYA AGENT (Query Orchestration)                      │
│  - Safety Guardrails                                    │
│  - Query Validation                                     │
│  - Citation Extraction                                  │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        v                 v
┌───────────────┐  ┌──────────────────┐
│  RETRIEVAL    │  │  GRAPH ANALYSIS  │
│  (Hybrid)     │  │  (Neo4j)         │
├───────────────┤  ├──────────────────┤
│ • Vector      │  │ • Citation       │
│   (Qdrant     │  │   Networks       │
│   60%)        │  │ • Case           │
│ • BM25        │  │   Relationships  │
│   (Lexical    │  │ • Precedent      │
│   40%)        │  │   Ranking        │
└───────┬───────┘  └────────┬─────────┘
        │                   │
        └────────┬──────────┘
                 v
┌─────────────────────────────────────────────────────────┐
│  LLM GENERATION                                         │
│  - Azure OpenAI (GPT-5-nano) [Primary]                  │
│  - Google Gemini [Fallback]                             │
└────────────────┬────────────────────────────────────────┘
                 │
                 v
┌─────────────────────────────────────────────────────────┐
│  RESPONSE + CITATIONS                                   │
└─────────────────────────────────────────────────────────┘
```

---

## 🏆 **Key Advantages of This Stack**

✅ **Cost-Effective**: Most components have free/open-source tiers  
✅ **Scalable**: Cloud-native databases (Qdrant, Neo4j)  
✅ **State-of-the-Art**: Modern transformer models + hybrid search  
✅ **Flexible**: Multi-LLM support (Azure/Gemini) with fallback  
✅ **Production-Ready**: FastAPI + type safety + error handling  
✅ **Legally Optimized**: Graph-based citation analysis unique to legal domain  

---

## 📝 **License Compliance Notes**

- **AGPL Components**: PyMuPDF (consider alternatives like `pypdf` if AGPL problematic)
- **GPL Components**: Neo4j Community Edition (commercial license needed for enterprise)
- **Apache/MIT/BSD**: All other components are permissively licensed

---

## 🔗 **Related Resources**

- **Project Documentation**: See `README.md`
- **API Endpoints**: http://localhost:8000/docs (when running)
- **Test Questions**: `TEST_QUESTIONS.md`
- **Configuration**: `.env.example` (copy to `.env`)

---

**Last Updated**: March 10, 2026  
**Project**: Nyaya Legal Citation System  
**Total Open Source Dependencies**: 15 core libraries (production only)
