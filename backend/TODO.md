# TODO - Future Improvements

## Recently Completed (MVP Phase 1)

### ✅ Text Extraction
**Status:** COMPLETE

**Implemented:**
- PDF extraction with PyMuPDF (native text + OCR fallback)
- TXT extraction  
- Block-based structure (pages, blocks, metadata)
- ExtractionService wrapper for S3 storage

**Files:**
- `services/text_extraction/` - Extractors
- `services/extraction_service.py` - Service wrapper
- Tests in `tests/extractor_tests/`

---

### ✅ Document Classification
**Status:** COMPLETE

**Implemented:**
- Structure-aware classifier (uses extracted blocks, not raw bytes)
- Smart sampling (skips cover pages, filters noise)
- Multi-section sampling for long documents
- LLM-based classification (Llama 3.1 8B)

**Files:**
- `services/content_analysis/content_classifier.py`
- `prompts/content_analysis/content_classification.py`
- Tests in `tests/services/test_document_classifier_service.py`

---

### ✅ Content Analysis (Spam Filtering)
**Status:** COMPLETE

**Implemented:**
- EmailAnalyzer for spam detection
- DefaultAnalyzer for junk filtering
- ContentAnalysisService to route to analyzers
- FILTERED_OUT status for unwanted documents

**Files:**
- `services/content_analysis/` - Analyzers
- `services/content_analysis_service.py` - Service orchestration
- Tests in `tests/services/test_content_analysis_service.py`

---

### ✅ Semantic Chunking
**Status:** COMPLETE

**Implemented:**
- Legal-BERT embeddings for semantic boundaries
- Topic-aware chunking (cosine similarity)
- ChunkingService (saves to S3 + Pinecone)
- Metadata tracking (page numbers, block IDs)

**Files:**
- `services/chunking/semantic_chunker.py` - Core logic
- `services/chunking/chunking_service.py` - Service wrapper
- `services/chunking/models.py` - Data models
- Tests in `tests/services/chunking/`

---

### ✅ Document Summarization
**Status:** COMPLETE

**Implemented:**
- Hierarchical summarization (map-reduce pattern)
- LlamaClient via Ollama (fast, optimized)
- SaulClient via Transformers (alternative, legal-specialized)
- Search-optimized prompts
- Elasticsearch storage

**Files:**
- `services/summarization/llama_client.py` - Llama via Ollama
- `services/summarization/saul_client.py` - Saul-Instruct (optional)
- `services/summarization/summarization_service.py` - Hierarchical logic
- `prompts/summarization/legal_summarization.py` - Prompts
- Tests in `tests/services/summarization/`

---

### ✅ Document Processing Orchestrator
**Status:** COMPLETE

**Implemented:**
- Full pipeline orchestration (extract → classify → analyze → chunk → summarize)
- Proper status tracking through pipeline
- Error handling with structured failures
- Stop points (FILTERED_OUT for spam)
- Service-based DI (no direct infrastructure dependencies)

**Files:**
- `orchestrators/document_processor.py` - Main orchestrator
- `orchestrators/__init__.py` - DI factory
- Tests in `tests/orchestrators/`

---

### ✅ Infrastructure
**Status:** COMPLETE

**Implemented:**
- StorageClient (MinIO/S3)
- PineconeClient (vector search)
- ElasticsearchClient (full-text search)
- Mock helpers for testing

**Files:**
- `infrastructure/storage.py`
- `infrastructure/pinecone_client.py`
- `infrastructure/elasticsearch_client.py`
- `tests/helpers/mock_*.py`

---

## Current Work in Progress

### RAG Query System (Critical for Demo)
**Status:** NEEDS DESIGN & IMPLEMENTATION

**Purpose:** Answer legal questions using hybrid search + LLM reasoning

**Example Query:** "Find documents that show executives knew their losses were being hidden from shareholders"

**Architecture:**

**Step 1: Query Understanding**
- Use LLM to analyze question
- Extract key concepts, entities, search terms
- Determine document type preferences

**Step 2: Hybrid Search**
```python
# Parallel search
elasticsearch_results = search_summaries(question)  # Keyword-based
pinecone_results = search_chunks(question)          # Semantic-based

# Merge and rank
# Prioritize documents in BOTH results (high confidence)
```

**Step 3: Chunk Retrieval**
- Get relevant chunks from prioritized documents
- Sort by relevance score
- Limit to fit LLM context window (~6000 tokens)

**Step 4: Answer Generation**
- Build context from top chunks
- LLM generates answer with citations
- Extract source references

**Step 5: Citation Formatting**
```python
{
    "answer": "Several documents show awareness...",
    "citations": [
        {
            "document_id": 123,
            "filename": "email.txt",
            "page_numbers": [2, 3],
            "chunk_text": "Preview...",
            "relevance_score": 0.94,
            "view_url": "/documents/123/view?pages=2-3"
        }
    ],
    "metadata": {
        "documents_searched": 1500,
        "relevant_found": 12,
        "chunks_used": 8
    }
}
```

**Components Needed:**
1. `services/query/query_service.py` - Main orchestrator
2. `services/query/search_orchestrator.py` - Hybrid search logic
3. `services/query/context_builder.py` - Build LLM context
4. `services/query/citation_extractor.py` - Parse citations from answer
5. `prompts/query/answer_generation.py` - RAG prompts
6. Controller endpoint: `POST /query`

**Data Sources Used:**
- Elasticsearch: Summary search (narrow to relevant docs)
- Pinecone: Chunk-level semantic search (find specific evidence)
- S3 blocks.json: For precise page/block citations
- PostgreSQL: Document metadata

**Estimated Time:** 3-4 hours

---

### Document Viewer
**Status:** NEEDS IMPLEMENTATION

**Purpose:** Display documents with highlighted citations

**Requirements:**
- Serve original PDF from S3
- Highlight specific pages/chunks
- iframe integration for frontend

**Options:**
1. **PDF.js viewer** (frontend library)
2. **Simple iframe** with page parameter
3. **Convert to HTML** for better highlighting (complex)

**Endpoint:**
```python
@app.get("/documents/{id}/view")
async def view_document(id: int, pages: str = None):
    # Load PDF from S3
    # Return with content-type: application/pdf
    # Frontend uses PDF.js to highlight pages
```

**Estimated Time:** 1 hour

---

### Document Queue/Status View
**Status:** NEEDS IMPLEMENTATION

**Purpose:** Show processing status to user

**Endpoints:**
```python
GET /cases/{case_id}/documents/queue
# Returns: {processing: 5, filtered: 2, failed: 1, completed: 142}

GET /cases/{case_id}/documents?status=processing
# Returns: List of documents being processed

GET /cases/{case_id}/documents?status=completed&limit=100
# Returns: Completed documents (with summaries for preview)
```

**UI Display:**
- Processing queue count (don't show individual docs)
- Failed documents (user can review/retry later)
- Completed count
- Simple status indicator

**Estimated Time:** 1 hour

---

### API Integration
**Status:** IN PROGRESS

**Next Steps:**
- Wire orchestrator into document upload endpoint
- Add background task processing
- Create status polling endpoint

**Estimated Time:** 30 minutes

---

### Retry Functionality (Future)

**Status:** Tabled for post-MVP

**Purpose:** Allow manual or automatic retry of failed documents.

**Features:**
- Parse processing_error to identify failed step
- Resume pipeline from failed step (skip completed steps)
- Track retry_count to prevent infinite loops
- Expose endpoint: `POST /documents/{id}/retry`

**Fields Needed:**
- `Document.retry_count` (IntField, default=0)
- `Document.last_retry_at` (DatetimeField, null=True)

**Estimated Time:** 1 hour

---

## Post-MVP Enhancements

### High Priority

#### 1. Swarm Classification Strategy
**Current State:** Single agent classifies document based on intelligent sampling from extracted blocks.

**Future Enhancement:** Implement multi-agent swarm classification for better accuracy:
- Split document into sections (beginning, middle, end)
- Run 3+ agents in parallel (no cost with local Ollama)
- Confidence-weighted voting to aggregate results
- Optional supervisor agent for close calls
- Consider LangGraph for workflow orchestration

**Benefits:**
- Covers entire document, not just sampled sections
- Handles documents that change character (e.g., contract with informal appendix)
- Better accuracy on edge cases
- Catches false positives from misleading cover pages

**Estimated Time:** 2-4 hours

---

#### 2. Chunking Strategy Implementation
**Current State:** Block extraction complete, but no chunking layer yet.

**Next Steps:**
- Implement block-merging chunker (merge blocks until ~800-1000 tokens)
- Respect block boundaries (don't split paragraphs)
- Keep headers with their content
- Add overlap between chunks (last block of chunk N = first block of chunk N+1)
- Use block metadata (kind, page numbers) for smart boundaries

**For Later:**
- LLM-assisted semantic chunking (identify topic boundaries)
- Document-type-specific chunking strategies

---

#### 3. DOCX Extractor
**Current State:** Only PDF and TXT extraction working.

**Implementation:**
- Use existing `python-docx` dependency
- Extract paragraphs and tables
- Map to block structure (same as PDF/TXT)
- Handle document structure (headings, lists)

**Skip:** Old .doc format support (tell users to convert)

**Estimated Time:** 1-2 hours

---

### Medium Priority

#### 4. Embedding Pipeline
**Next Phase:** After chunking is implemented
- Generate embeddings for chunks (sentence-transformers already installed)
- Store in Pinecone with metadata
- Implement hybrid search (semantic + keyword)

---

#### 5. Summarization Service
**Hierarchical Summarization:**
- Chunk-level summaries
- Document-level summaries
- Case-level summaries

---

#### 6. RAG Query System
**After embeddings working:**
- Semantic search for relevant chunks
- Context window management
- Citation tracking (link back to blocks/pages)

---

### Low Priority / Nice to Have

#### 7. OCR Quality Improvements
**Current State:** PyMuPDF native OCR working but quality varies

**Options to explore:**
- Azure Document Intelligence (better quality, costs money)
- EasyOCR (neural network based, no Tesseract dependency)
- Preprocessing improvements (deskew, denoise)

---

#### 8. Email Analyzer Integration
**Current State:** Email analyzer exists but not integrated with main classifier

**Todo:** Decide if email detection should be:
- Pre-classification step (detect email headers first)
- Post-classification filter (classify as email, then check if spam/substantive)
- Separate workflow entirely

---

#### 9. Performance Optimizations
**For scale (100k+ documents):**
- Batch processing for embeddings
- Parallel document processing
- Caching strategies for repeated classifications
- Database query optimization

---

#### 10. Testing & Validation
**Expand test coverage:**
- More diverse document samples
- Edge cases (corrupted files, mixed content)
- Performance benchmarks
- Accuracy metrics for classification

---

## Architecture Decisions to Revisit

### 1. Storage Paths
**Current:** `{case_id}/documents/{doc_id}/extraction/blocks.json`
**Consider:** Whether this scales well, S3 costs vs structure

### 2. Classification Categories
**Current:** Open-ended (LLM decides)
**Consider:** Fixed taxonomy vs dynamic categories

### 3. Block Granularity
**Current:** Using PyMuPDF's native block detection
**Question:** Is this too granular or not granular enough for different use cases?

---

## Technical Debt

1. Fix Pydantic deprecation warnings (use ConfigDict)
2. Remove deleted file from git tracking (`case_pdf_1/documents/doc_1001/extraction/blocks.json`)
3. Standardize error handling across services
4. Add proper logging (replace print statements)
5. Document S3 bucket structure and conventions

---

## Notes

- Prioritize working features over perfection
- Test with real legal documents before presentation
- Document assumptions and limitations clearly
- Keep presentation demo simple and reliable

