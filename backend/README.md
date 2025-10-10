# AI Legal Analysis App - Project Plan

## Overview
Desktop app for AI-powered legal document analysis. Each org gets **completely isolated infrastructure** (no shared resources).

**Scale**: 100k+ documents per case  
**Architecture**: Vertical Slice (one business function = one file)  
**Deployment**: Desktop app + Backend API (cloud or on-prem, decided later)

## Project Structure
```
backend/
  infrastructure/     ← DB, Pinecone, File Storage clients
  core/              ← Configuration
  features/          ← Business functions (one per file)
  main.py
```

---

## Tech Stack
- **FastAPI** + **Uvicorn** + **Poetry**
- **Tortoise ORM** + **Aerich** (migrations)
- **PostgreSQL** (or SQLite for dev)
- **Pinecone** - Vector DB
- **MinIO** - S3-compatible object storage (Docker with volumes)
- **PyMuPDF**, **python-docx**, **openpyxl** - Document parsing
- **sentence-transformers** - Embeddings
- AI models handled per-agent (no shared client)

---

## Infrastructure (Build First)

**3 core clients** that features depend on:

### 1. Database (`infrastructure/database.py`)
- Tortoise ORM setup
- Connection management
- Initialize on startup, close on shutdown

### 2. Pinecone Client (`infrastructure/pinecone_client.py`)
- **Methods**: `upsert_vectors()`, `query()`, `delete()`
- Each org has their own Pinecone index (isolated)
- Store document chunks with metadata

### 3. Storage Client (`infrastructure/storage.py`)
- **MinIO** (S3-compatible, runs in Docker)
- **Methods**: `upload()`, `download()`, `delete()`, `get_url()`
- Docker setup with persistent volumes (files survive restarts)

**Note**: AI models/prompts are feature-specific (each agent configures their own)

---

## Document Processing Pipeline

### Upload Flow
```
Upload → Validate → Store in MinIO → Classify Document Type
                                            ↓
                    ┌───────────────────────┼───────────────────────┐
                    ↓                       ↓                       ↓
              OCR Branch            Structure Branch          Pure Text Branch
          (handwritten/scanned)   (visual, charts, forms)    (Word, clean PDFs)
                    ↓                       ↓                       ↓
              Tesseract/Azure         Multimodal LLM          PyMuPDF/docx
                    ↓                       ↓                       ↓
                    └───────────────────────┼───────────────────────┘
                                            ↓
                    Extracted Text + Metadata (confidence, layout)
                                            ↓
                    Summarize (LLM) → Extract Entities (spaCy NER)
                                            ↓
                    Score Relevancy → Chunk → Embed → Store in Pinecone
```

### Processing Branches

**1. Pure Text Branch** (Start here for MVP)
- File types: `.docx`, `.txt`, clean PDFs with extractable text
- Tools: `python-docx`, `PyMuPDF`
- Fast, reliable, no AI needed for extraction
- **Build this first**

**2. OCR Branch** (Phase 2)
- File types: `.jpg`, `.png`, `.tiff`, scanned PDFs
- Tools: `pytesseract` (basic) or Azure Document Intelligence (better)
- Outputs: text + confidence scores
- Flag low-confidence sections for review

**3. Structure Branch** (Phase 3)
- File types: Complex PDFs, Excel, PPT, visual documents
- Tools: Multimodal LLM (GPT-4 Vision, Claude 3.5 with images)
- Preserve layout semantics: "Chart shows X declining, table compares Y vs Z"
- Most complex, defer until core working

### Model Selection

**Summarization**: 
- MVP: Llama 3.1 70B (local via Ollama) or Claude 3.5 Sonnet (API)
- Prompting matters more than model specialization
- Each agent can use different models/prompts

**Entity Extraction**:
- Use spaCy with legal NER model: `en_legal_ner_trf`
- Extracts: PERSON, ORG, DATE, COURT, LAW, etc.
- Fast, accurate, runs locally

**Classification** (which branch?):
- Simple rule-based first (check file type + has_text_layer)
- Later: Small classifier model if needed

## Features Roadmap

### Phase 1: MVP (Pure Text Only)

**Authentication & Authorization:**
- `features/auth/register.py` - User registration
- `features/auth/login.py` - JWT authentication
- `features/users/create_user.py` - User management (admin only)
- `features/groups/create_group.py` - Group management
- `features/groups/assign_user.py` - Add users to groups

**Case Management:**
- `features/cases/create_case.py` - Create case with context, assign groups
- `features/cases/list_cases.py` - List cases (filtered by user's group access)
- `features/cases/get_case.py` - Get case details (with permission check)
- `features/cases/assign_group.py` - Assign group to case

**Document Processing:**
- `features/documents/upload_document.py` - Upload to MinIO, track uploader
- `features/documents/extract_text.py` - Extract from Word/PDF (pure text only)
- `features/documents/chunk_document.py` - Smart chunking (tiered approach)
- `features/documents/summarize.py` - LLM summarization
- `features/documents/extract_entities.py` - spaCy NER extraction
- `features/documents/score_relevancy.py` - Score against case context
- `features/documents/index_document.py` - Generate embeddings, store in Pinecone

**Timeline & Personages:**
- `features/personages/create_personage.py` - Add notable person/org to case
- `features/personages/link_document.py` - Link document mentions to personages
- `features/timeline/create_event.py` - Add timeline event
- `features/timeline/extract_events.py` - Auto-extract events from documents

**Analysis:**
- `features/analysis/ask_question.py` - RAG query (with access control)

### Phase 2: OCR & Advanced Processing
- OCR branch for scanned documents
- Bulk upload (1000s of documents)
- Background job queue (Celery)
- Timeline construction from events
- Entity relationship graph

### Phase 3: Visual/Structured Documents
- Structure branch with multimodal LLM
- Complex document analysis
- Advanced entity linking

---

## Data Models

### Core Entities

**User**
- id, email, password_hash, full_name
- role: enum('analyst', 'user', 'admin', 'super_admin')
- is_active, created_at, updated_at

**Group**
- id, name, description
- created_at, updated_at

**UserGroup** (many-to-many join table)
- user_id, group_id
- joined_at

### Cases & Authorization

**Case**
- id, name, description
- key_issues (JSON), key_parties (JSON), key_dates (JSON)
- status: enum('active', 'closed', 'archived')
- created_by (user_id), created_at, updated_at

**CaseGroup** (assigns groups to cases)
- case_id, group_id
- assigned_at
- *(Future: permission_overrides JSON - case-specific role permissions)*

**CaseTimeline**
- id, case_id
- event_date, event_description
- source_document_ids (JSON) - which docs mention this event
- entity_ids (JSON) - which people/orgs involved
- created_at

**CasePersonage** (notable people in case)
- id, case_id
- name, entity_type: enum('person', 'organization', 'court', 'other')
- role (e.g., 'plaintiff', 'defendant', 'witness', 'judge')
- mentions_count - how many docs mention them
- metadata (JSON) - additional info extracted
- created_at, updated_at

### Documents & Processing

**Document**
- id, case_id, uploaded_by (user_id)
- filename, minio_key, file_type, file_size
- processing_branch: enum('pure_text', 'ocr', 'structure')
- status: enum('uploaded', 'processing', 'completed', 'failed')
- created_at, updated_at

**DocumentProcessing**
- id, document_id
- extracted_text, extraction_confidence (nullable)
- summary, relevancy_score, relevancy_reasoning
- entities (JSON) - extracted entities
- processing_metadata (JSON) - branch-specific data
- completed_at, created_at

**DocumentChunk**
- id, document_id
- chunk_index, text, page_number (nullable)
- pinecone_id - ID in vector database
- chunk_method: enum('structural', 'semantic', 'llm')
- section_type (nullable) - e.g., 'obligations', 'definitions'
- word_count, confidence
- created_at

**DocumentPersonage** (links documents to people mentioned)
- document_id, personage_id
- mention_count, context_snippets (JSON)

### Query & Analysis

**Query**
- id, case_id, user_id
- question, answer
- sources (JSON) - document chunks used
- model_used, tokens_used
- created_at

---

## Authorization Model

### How Access Control Works

**Group-Based Access:**
```
User → belongs to → Groups → assigned to → Cases
```

**Access Check:**
```python
async def user_can_access_case(user_id: int, case_id: int) -> bool:
    """
    User can access case if they belong to any group assigned to that case.
    """
    user_groups = await get_user_groups(user_id)
    case_groups = await get_case_groups(case_id)
    
    return bool(user_groups & case_groups)  # Set intersection
```

**Permission Levels:**

| Role | Permissions |
|------|-------------|
| **Analyst** | View cases, documents, query RAG, view timeline/personages |
| **User** | Same as Analyst + upload documents, create queries |
| **Admin** | Same as User + create cases, assign groups, manage case metadata |
| **Super Admin** | All permissions + user management, group management |

### Case-Specific Permissions (Future Phase)

Allow overriding role permissions per case:

```python
# Example: CaseGroup.permission_overrides
{
    "analyst": {
        "can_download": false,  # Analysts can't download originals for this sensitive case
        "can_export": false
    },
    "user": {
        "can_upload": true,  # Users can upload for this case
        "max_queries_per_day": 50
    }
}
```

This allows fine-grained control for sensitive cases without creating new roles.

### Implementation Notes

**Phase 1 (MVP):**
- Implement basic group-based access (User → Group → Case)
- Role-based permissions are global (not case-specific)
- Simple: "Does user's group have access to this case?"

**Phase 2:**
- Add case-specific permission overrides
- Audit logging (who accessed what, when)
- Document-level permissions (mark documents as restricted)

**Phase 3:**
- Time-based access (access expires after date)
- Approval workflows (request access to case)
- Data room features (external party access with restrictions)

---

## Development Stages

### Stage 1: Foundation
- [ ] Poetry dependencies
- [ ] Docker Compose (MinIO, PostgreSQL)
- [ ] 3 infrastructure clients (DB, Pinecone, Storage)
- [ ] Config setup (`.env`)

### Stage 2: Core Features
- [ ] User authentication (register, login, JWT tokens)
- [ ] User & Group management (CRUD operations)
- [ ] Create/list cases with group assignment
- [ ] Case access control (check user → group → case)
- [ ] Upload document (to MinIO) with user tracking
- [ ] Process document (extract text, chunk, embed, store in Pinecone)
- [ ] RAG query endpoint with permission checks

### Stage 3: Timeline & Entity Features
- [ ] Entity extraction from documents (spaCy NER)
- [ ] Personage management (create, merge duplicates)
- [ ] Timeline construction from document events
- [ ] Link documents to personages and timeline events
- [ ] Bulk operations for document upload
- [ ] Background job queue (Celery)

### Stage 4: Frontend
- [ ] Desktop app (Electron/Tauri)
- [ ] UI for upload, query, results

### Stage 5: Deployment
- [ ] Packaging & installer
- [ ] Org-specific configuration

---

## MinIO Docker Setup (Persistent Storage)

```yaml
# docker-compose.yml
version: '3.8'
services:
  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - ./data/minio:/data  # ← Files persist here
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
  
  postgres:
    image: postgres:16
    ports:
      - "5432:5432"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: legal_ai
      POSTGRES_PASSWORD: password
      POSTGRES_DB: legal_ai_db
```

**Key**: Use volumes (`./data/minio:/data`) so files survive container restarts

---

## Dependencies (Poetry)

**Core**: `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `python-multipart`  
**Database**: `tortoise-orm`, `aerich`, `asyncpg`  
**Authentication**: `python-jose[cryptography]` (JWT), `passlib[bcrypt]` (password hashing), `python-multipart` (form data)  
**Storage**: `minio`, `aioboto3`  
**Vector DB**: `pinecone-client`  
**Document Processing**: `PyMuPDF`, `python-docx`, `openpyxl`, `aiofiles`, `pytesseract` (OCR, phase 2)  
**AI/NLP**: `sentence-transformers` (embeddings + semantic chunking), `spacy` (NER), `ollama` (local LLM client), `numpy` (cosine similarity)  
**Utilities**: `python-dotenv`, `loguru`, `httpx` (if using API-based LLMs)  
**Dev**: `pytest`, `pytest-asyncio`, `black`, `ruff`

**Post-install**: 
- `python -m spacy download en_legal_ner_trf` (legal NER model)
- Install Ollama separately: https://ollama.ai
- Pull model: `ollama pull llama3.1:70b`

---

## Implementation Strategy for Processing Branches

### Phase 1: Pure Text Only (MVP)
Focus on Word docs and clean PDFs. This handles ~60-70% of legal documents and validates the entire pipeline.

```python
# features/documents/extract_text.py

async def extract_text(document_id: int) -> ExtractedText:
    doc = await Document.get(id=document_id)
    
    if doc.file_type == "pdf":
        text = extract_from_pdf(doc.minio_key)
    elif doc.file_type == "docx":
        text = extract_from_word(doc.minio_key)
    elif doc.file_type == "txt":
        text = extract_from_txt(doc.minio_key)
    else:
        raise UnsupportedFileType(f"{doc.file_type} not supported yet")
    
    # Update document
    doc.processing_branch = "pure_text"
    doc.status = "text_extracted"
    await doc.save()
    
    return ExtractedText(text=text, confidence=1.0)
```

**Test this thoroughly before adding other branches.**

### Phase 2: Add OCR Branch
Once pure text works, add scanned document support.

```python
# Add to extract_text.py

async def extract_text(document_id: int) -> ExtractedText:
    doc = await Document.get(id=document_id)
    
    # Classify first
    branch = classify_document(doc)
    
    if branch == "pure_text":
        text = extract_from_pdf(doc.minio_key)
        confidence = 1.0
    elif branch == "ocr":
        text, confidence = extract_with_ocr(doc.minio_key)  # Returns confidence
    
    doc.processing_branch = branch
    await doc.save()
    
    return ExtractedText(text=text, confidence=confidence)
```

### Phase 3: Add Structure Branch
Last, because it's most complex.

**Key Insight**: All branches produce the same output format (`ExtractedText`), so downstream processing (summarize, extract entities, etc.) doesn't care which branch was used.

---

## Chunking Strategy (Critical for RAG Quality)

### The Problem with Naive Chunking

Legal documents require **semantic-aware chunking**. Context at boundaries is crucial:

```
❌ BAD (split at N characters):
Chunk 1: "...the Seller agrees to deliver"
Chunk 2: "the goods by December 31, 2024..."
Problem: Query "When must seller deliver?" misses the date!

✅ GOOD (semantic boundaries):
Chunk 1: "...the Seller agrees to deliver the goods by December 31, 2024."
Complete clause with full context preserved.
```

### Chunking Approaches

**Important**: Pinecone doesn't chunk for you - you must chunk before storing!

#### 1. Structural Chunking (Fast, Free)
Split by legal document structure:
- Section headers (SECTION X, ARTICLE X)
- Numbered clauses (1., 2., 3.)
- WHEREAS clauses
- Lettered subsections (a), (b), (c)

**When**: Well-formatted legal documents with clear structure  
**Speed**: ⚡⚡⚡ Very fast  
**Accuracy**: 😐 Decent for structured docs

#### 2. Semantic Similarity Chunking (Recommended Default)
Use embeddings to detect topic shifts:

```python
from sentence_transformers import SentenceTransformer
import numpy as np

def semantic_chunking(text: str, similarity_threshold: float = 0.7):
    """Chunk when consecutive sentences are semantically dissimilar."""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    sentences = split_sentences(text)
    embeddings = model.encode(sentences)
    
    chunks = []
    current_chunk = [sentences[0]]
    
    for i in range(1, len(sentences)):
        similarity = cosine_similarity(embeddings[i-1], embeddings[i])
        
        if similarity < similarity_threshold:
            # Topic shift detected → new chunk
            chunks.append(' '.join(current_chunk))
            current_chunk = [sentences[i]]
        else:
            current_chunk.append(sentences[i])
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks
```

**When**: Most documents  
**Speed**: ⚡⚡ Medium (needs to embed sentences)  
**Accuracy**: 😊 Good - understands semantic boundaries

#### 3. LLM-Assisted Chunking (High Quality)
Ask LLM to identify section boundaries:

```python
async def llm_chunking(text: str):
    """LLM identifies semantic sections and boundaries."""
    prompt = f"""Identify distinct semantic sections in this legal document.
For each section provide: start marker, end marker, section type.

Document: {text}

Return JSON: [{{"start": "...", "end": "...", "type": "..."}}]"""
    
    response = await ollama.chat(
        model='llama3.1:70b',
        messages=[{'role': 'user', 'content': prompt}],
        format='json'
    )
    
    sections = json.loads(response['message']['content'])
    return extract_chunks_by_markers(text, sections)
```

**When**: High-value documents where accuracy is critical  
**Speed**: 🐌 Slow (1 LLM call per document)  
**Accuracy**: 😍 Excellent - understands legal context

#### 4. Tiered Hybrid Approach (MVP Recommendation)

Combine strategies for best speed/accuracy tradeoff:

```python
async def smart_chunking(document_id: int, text: str, max_chunk_size: int = 1000):
    """
    Three-tier chunking strategy:
    1. Try structural (fast, free)
    2. Fall back to semantic similarity (medium speed)
    3. LLM validation only for problematic chunks
    """
    
    # Tier 1: Structural chunking for well-formatted docs
    if has_clear_structure(text):
        chunks = structural_chunking(text)
        if validate_chunks(chunks, max_chunk_size):
            return add_metadata(chunks, method="structural")
    
    # Tier 2: Semantic similarity chunking
    chunks = semantic_chunking(text, similarity_threshold=0.7)
    
    # Tier 3: LLM validation only for problematic chunks
    validated = []
    for chunk in chunks:
        if is_problematic(chunk, max_chunk_size):
            # Too large or bad boundaries → ask LLM to refine
            refined = await llm_refine_chunk(chunk, max_chunk_size)
            validated.extend(refined)
        else:
            validated.append(chunk)
    
    return validated

def is_problematic(chunk: str, max_size: int) -> bool:
    """Detect chunks that need LLM refinement."""
    # Too large?
    if len(chunk) > max_size:
        return True
    
    # Incomplete sentence at boundary?
    if not chunk.rstrip().endswith(('.', '!', '?', ';')):
        return True
    
    # Mid-clause indicators?
    boundary_keywords = ['provided that', 'subject to', 'notwithstanding']
    if any(keyword in chunk[-100:] for keyword in boundary_keywords):
        return True
    
    return False
```

### Performance Comparison

| Method | Speed | Accuracy | Cost | Use Case |
|--------|-------|----------|------|----------|
| Structural | ⚡⚡⚡ | 😐 OK | Free | Formatted docs |
| Semantic | ⚡⚡ | 😊 Good | Free | Default choice |
| LLM-Based | 🐌 | 😍 Excellent | $$$ | High-value only |
| **Tiered Hybrid** | **⚡⚡** | **😊 Good** | **$** | **Recommended** |

### Implementation Plan

**Phase 1 (MVP)**: 
- Implement structural chunking + semantic similarity
- Use tiered approach (fast path for most docs)

**Phase 2**: 
- Add LLM validation for complex documents
- Fine-tune similarity thresholds based on testing

**Phase 3**:
- Experiment with proposition-based chunking
- A/B test different strategies on real legal documents

### Chunk Metadata

Store metadata with each chunk for better retrieval:

```python
{
    "id": "doc123_chunk5",
    "document_id": 123,
    "chunk_index": 5,
    "text": "The Seller agrees to...",
    "page_number": 3,
    "section_type": "obligations",  # From structural analysis
    "chunk_method": "semantic",     # How it was chunked
    "confidence": 0.85,             # Semantic similarity score
    "word_count": 234,
    "overlaps_with": ["doc123_chunk4", "doc123_chunk6"]  # For context
}
```

This metadata helps during RAG retrieval to provide better context.

---

## Notes & Decisions

- **Date**: 2025-10-09
- **Architecture**: Vertical Slice (decided)
- **ORM**: Tortoise ORM (decided)
- **Storage**: MinIO with Docker volumes (persists data)
- **Vector DB**: Pinecone (isolated per org)
- **Authentication**: JWT tokens with role-based access control
- **Authorization**: Group-based (User → Group → Case) with roles (analyst, user, admin, super_admin)
- **AI Models**: No shared client - each agent/feature configures their own model/prompts
- **LLM for MVP**: Llama 3.1 70B (local via Ollama) or Claude 3.5 Sonnet (API)
- **NER**: spaCy with en_legal_ner_trf model for entity extraction
- **Chunking**: Tiered hybrid (structural → semantic similarity → LLM validation)
- **No LangChain**: Use ollama-python directly for simpler, more controlled implementation
- **Data Scale**: 100k+ documents per case
- **Case Features**: Timeline construction and personage tracking from extracted entities
- **SOC 2 Compliance**: Deferred until after MVP, but building with security best practices

---

## Next Steps

1. Add dependencies to `pyproject.toml`
2. Create `docker-compose.yml` (MinIO + PostgreSQL)
3. Build 3 infrastructure clients
4. Create first feature: Create Case