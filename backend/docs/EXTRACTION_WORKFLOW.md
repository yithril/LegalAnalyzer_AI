# Document Extraction Workflow

## Overview

This document explains how uploaded files flow through the extraction pipeline, what gets saved where, and why we structure data the way we do.

---

## The Complete Pipeline

```
1. User uploads file
   ↓
2. File saved to MinIO (original)
   ↓
3. Text extraction → Blocks structure
   ↓
4. Blocks saved to MinIO (JSON)
   ↓
5. LLM metadata extraction
   ↓
6. Metadata saved to PostgreSQL
   ↓
7. Semantic chunking
   ↓
8. Chunks saved to MinIO (JSON)
   ↓
9. Generate embeddings
   ↓
10. Vectors saved to Pinecone
```

---

## Storage Strategy

### MinIO (Object Storage - Cheap & Scalable)

```
documents/
  doc_123/
    original.pdf              ← Original uploaded file (50MB)
    extraction/
      blocks.json             ← Extracted pages/blocks WITH text (5-10MB)
    processing/
      body_text.txt           ← Optional: clean body text after metadata stripped
    chunks.json               ← Final semantic chunks for RAG (4MB)
```

**Why MinIO?**
- Cheap storage (~$0.02/GB/month)
- Can handle large files
- S3-compatible (easy to migrate later)
- Files persist across service restarts

### PostgreSQL (Structured Metadata)

```sql
documents table:
- id, case_id, filename, file_type, file_size
- minio_bucket, minio_key (pointer to original)
- status (uploaded → extracting → chunked → completed)
- created_at, updated_at

document_chunks table (later):
- id, document_id, chunk_index
- minio_path (pointer to chunks.json)
- summary, section_type
- pinecone_id (pointer to vector)
```

**Why PostgreSQL?**
- Fast queries for metadata
- Relational integrity (documents → cases)
- Small structured data

### Pinecone (Vector Database)

```python
{
  "id": "doc123_chunk5",
  "values": [0.123, 0.456, ...],  # 384-dim vector
  "metadata": {
    "document_id": 123,
    "chunk_index": 5,
    "summary": "This section discusses..."
  }
}
```

**Why Pinecone?**
- Semantic similarity search
- Fast vector queries
- Scalable

---

## The Blocks Structure

### Why Do We Extract to Blocks?

Instead of saving raw text:
```
UNITED STATES DISTRICT COURT Case No. 23-cv-12345 Plaintiff moves...
```

We save **structured blocks with context**:

```json
{
  "pages": [
    {
      "page_index": 0,
      "width": 612,
      "height": 792,
      "blocks": [
        {
          "block_index": 0,
          "text": "UNITED STATES DISTRICT COURT",
          "bbox": [216, 50, 396, 80],
          "font": {"size": 14, "bold": true},
          "kind_hint": "header"
        },
        {
          "block_index": 1,
          "text": "Case No. 23-cv-12345",
          "bbox": [72, 120, 540, 150],
          "font": {"size": 12, "bold": false},
          "kind_hint": "paragraph"
        }
      ]
    }
  ]
}
```

### Benefits of Blocks Structure

**1. Text + Context Together**
- Not just "what" the text says
- But "where" it is (bbox coordinates)
- And "what type" it is (kind_hint)
- And "how it looks" (font information)

**2. Easy to Filter**
```python
# Skip headers and footers
body_blocks = [b for b in blocks if b.kind_hint not in ["header", "footer"]]
body_text = "\n\n".join(b.text for b in body_blocks)
```

**3. Helps LLM Understand Structure**
```python
prompt = f"""
Here are blocks from a legal document:

Block 0 (header, bold 14pt): {blocks[0].text}
Block 1 (paragraph, 12pt): {blocks[1].text}

Which blocks are document metadata vs actual content?
"""
```

**4. Reusable for Multiple Steps**
- LLM metadata extraction reads blocks
- Semantic chunking reads blocks
- No need to re-extract from original file

**5. Debugging**
- Can see exactly what was extracted
- Inspect bbox to understand layout issues
- Compare font sizes to understand document structure

---

## File Type Support

### MVP: Text Documents with Linear Reading Flow

| File Type | Extractor | Pages | Blocks | bbox | Font | Notes |
|-----------|-----------|-------|--------|------|------|-------|
| **PDF** | PyMuPDF | ✅ Real | ✅ Layout-based | ✅ Yes | ✅ Yes | Perfect fit |
| **DOCX** | python-docx | 🔶 Virtual | ✅ Paragraph-based | ❌ null | ✅ Yes | Single "page 0" |
| **TXT** | Simple split | 🔶 Virtual | ✅ Paragraph-based | ❌ null | ❌ null | Split on `\n\n` |

**All three use the same `page_blocks.v1` model** → same downstream processing!

### Future: Additional Formats

**Easy Additions:**
- **PPTX** - Slides = pages, text boxes = blocks (fits model perfectly)
- **RTF, ODT** - Similar to DOCX

**Different Structure Needed:**
- **XLSX/CSV** - Grid data, needs `tabular.v1` model (separate structure)
- **Images** - OCR in Phase 2, adds `confidence` field to blocks

### The "Model Type" Field

Add this to extraction output:

```json
{
  "model": "page_blocks.v1",
  "version": "extraction.v1",
  "document_id": 123,
  "pages": [...]
}
```

Downstream code can branch on model type:
```python
if extracted.model == "page_blocks.v1":
    # Process pages/blocks (PDF, DOCX, TXT)
    process_blocks(extracted.pages)
elif extracted.model == "tabular.v1":
    # Process sheets/cells (Excel, CSV)
    process_tables(extracted.sheets)
```

---

## Detailed Processing Steps

### Step 1: Upload & Store Original

```python
# User uploads file
POST /documents/upload?case_id=1

# Service validates and saves
document = await Document.create(
    case_id=1,
    filename="contract.pdf",
    file_type="pdf",
    file_size=5242880,
    minio_bucket="legal-documents",
    minio_key="documents/doc_123/original.pdf",
    status="uploaded"  # ← Starting status
)
```

**Storage:**
- MinIO: `legal-documents/documents/doc_123/original.pdf`
- PostgreSQL: Document record with status="uploaded"

### Step 2: Extract to Blocks

```python
# Read original from MinIO
original_bytes = await storage.download("documents/doc_123/original.pdf")

# Run appropriate extractor
if document.file_type == "pdf":
    extractor = PDFExtractor()
elif document.file_type == "docx":
    extractor = DocxExtractor()
else:
    extractor = TxtExtractor()

# Extract to blocks structure
extracted: ExtractedDocument = await extractor.extract(original_bytes)

# Save blocks to MinIO
await storage.upload(
    "documents/doc_123/extraction/blocks.json",
    extracted.model_dump_json(indent=2)
)

# Update status
await document.update(status="blocks_extracted")
```

**Storage:**
- MinIO: `documents/doc_123/extraction/blocks.json` (5-10MB)
- PostgreSQL: Document status="blocks_extracted"

### Step 3: LLM Metadata Extraction

```python
# Read blocks from MinIO
blocks_json = await storage.download("documents/doc_123/extraction/blocks.json")
extracted = ExtractedDocument.model_validate_json(blocks_json)

# Analyze first few blocks (headers usually at top)
header_blocks = extracted.pages[0].blocks[:10]
header_text = "\n\n".join(b.text for b in header_blocks)

# Ask LLM to identify metadata
metadata = await llm_extract_metadata(header_text)
# Returns: {
#   "court": "US District Court",
#   "case_number": "23-cv-12345",
#   "judge": "Hon. Jane Smith",
#   "document_type": "Motion for Summary Judgment"
# }

# Save to PostgreSQL
await document.update(
    court_name=metadata.get("court"),
    case_number=metadata.get("case_number"),
    # ... etc
    status="metadata_extracted"
)
```

**Storage:**
- PostgreSQL: Metadata fields populated

### Step 4: Semantic Chunking

```python
# Read blocks from MinIO
blocks_json = await storage.download("documents/doc_123/extraction/blocks.json")
extracted = ExtractedDocument.model_validate_json(blocks_json)

# Filter out headers/footers using kind_hint
body_blocks = [
    b for page in extracted.pages 
    for b in page.blocks 
    if b.kind_hint not in ["header", "footer"]
]

# Semantic chunking (using embeddings or LLM)
chunks = await semantic_chunking(body_blocks)

# Save chunks to MinIO
await storage.upload(
    "documents/doc_123/chunks.json",
    json.dumps(chunks, indent=2)
)

# Save chunk metadata to PostgreSQL
for i, chunk in enumerate(chunks):
    await DocumentChunk.create(
        document_id=document.id,
        chunk_index=i,
        minio_path="documents/doc_123/chunks.json",
        summary=chunk.get("summary"),
        word_count=len(chunk["text"].split())
    )

await document.update(status="chunked")
```

**Storage:**
- MinIO: `documents/doc_123/chunks.json`
- PostgreSQL: DocumentChunk records (metadata only)

### Step 5: Generate Embeddings

```python
# Read chunks from MinIO
chunks_json = await storage.download("documents/doc_123/chunks.json")
chunks = json.loads(chunks_json)

# Generate embeddings in batches
BATCH_SIZE = 50
for i in range(0, len(chunks), BATCH_SIZE):
    batch = chunks[i:i+BATCH_SIZE]
    
    # Generate vectors
    embeddings = generate_embeddings([c["text"] for c in batch])
    
    # Upload to Pinecone
    vectors = []
    for j, (chunk, embedding) in enumerate(zip(batch, embeddings)):
        chunk_idx = i + j
        vectors.append({
            "id": f"doc{document.id}_chunk{chunk_idx}",
            "values": embedding,
            "metadata": {
                "document_id": document.id,
                "chunk_index": chunk_idx,
                "summary": chunk.get("summary", "")[:1000]
            }
        })
    
    await pinecone_client.upsert(vectors)
    
    # Update PostgreSQL with Pinecone IDs
    for j in range(len(batch)):
        chunk_idx = i + j
        chunk_record = await DocumentChunk.get(
            document_id=document.id, 
            chunk_index=chunk_idx
        )
        await chunk_record.update(
            pinecone_id=f"doc{document.id}_chunk{chunk_idx}"
        )

await document.update(status="completed")
```

**Storage:**
- Pinecone: Vector embeddings
- PostgreSQL: DocumentChunk records with pinecone_id

---

## Memory Management

### Key Principle: Never Hold Everything in Memory

**Bad (will crash with large files):**
```python
# Load all 100k documents
all_docs = await Document.all()
for doc in all_docs:
    data = await process(doc)  # All in memory!
```

**Good (process one at a time):**
```python
# Process documents one by one
document_ids = await Document.all().values_list("id", flat=True)
for doc_id in document_ids:
    await process_single_document(doc_id)
    # Only one document in memory at a time
```

### Checkpointing

Each step saves its output before moving to the next:

```python
# If processing fails at step 3, we don't re-run steps 1-2
if document.status == "uploaded":
    await extract_blocks(document)
elif document.status == "blocks_extracted":
    await extract_metadata(document)
elif document.status == "metadata_extracted":
    await chunk_document(document)
# ... etc
```

Can resume from any point!

---

## Why Not Just Save Plain Text?

### Comparison

**Plain text approach:**
```
documents/doc_123/extracted_text.txt  (1-2MB)

Content: "UNITED STATES DISTRICT COURT Case No. 23-cv-12345 Plaintiff moves..."
```

**Problems:**
- ❌ Don't know which part is header vs body
- ❌ Don't know spatial layout
- ❌ Don't know font information
- ❌ Can't easily filter headers/footers
- ❌ Harder for LLM to understand structure
- ❌ Must re-extract if we change metadata detection logic

**Blocks approach:**
```
documents/doc_123/extraction/blocks.json  (5-10MB)
```

**Benefits:**
- ✅ Text + structure + context preserved
- ✅ Easy to filter by kind_hint
- ✅ LLM gets helpful hints (font, position)
- ✅ Can re-process without re-extracting
- ✅ Debugging information preserved

**Trade-off:** ~3-5x larger files, but MinIO storage is cheap (~$0.02/GB/month)

---

## Status Progression

Document status field tracks pipeline progress:

```
uploaded                 ← File in MinIO, nothing processed yet
    ↓
extracting_blocks        ← Running extractor
    ↓
blocks_extracted         ← blocks.json saved to MinIO
    ↓
extracting_metadata      ← LLM analyzing headers
    ↓
metadata_extracted       ← Metadata saved to PostgreSQL
    ↓
chunking                 ← Creating semantic chunks
    ↓
chunked                  ← chunks.json saved to MinIO
    ↓
embedding                ← Generating vectors
    ↓
completed                ← Vectors in Pinecone, fully searchable
    ↓
failed                   ← Processing error (check processing_error field)
```

---

## Edge Cases & Error Handling

### Large Files

- Process in streaming fashion (don't load entire file)
- Batch embeddings (50 chunks at a time)
- Save intermediate results frequently

### Processing Failures

- Check `document.processing_error` field
- Status shows where it failed
- Can retry from last successful step

### Duplicate Detection

- Use `text_hash` field in blocks
- Identify repeated headers/footers
- Filter before chunking

### Multi-Language Documents

- Use `lang` field in blocks
- Route to appropriate language model
- Or use multilingual embeddings

---

## Future Enhancements

### Phase 2: OCR Support

Add `confidence` field to blocks:
```json
{
  "text": "Scanned text here",
  "confidence": 0.87,  // OCR confidence
  "kind_hint": "paragraph"
}
```

Flag low-confidence blocks for human review.

### Phase 3: Table Extraction

For complex tables, add optional `table_data`:
```json
{
  "kind_hint": "table",
  "text": "Header1 | Header2\nRow1Col1 | Row1Col2",
  "table_data": {
    "headers": ["Header1", "Header2"],
    "rows": [["Row1Col1", "Row1Col2"]]
  }
}
```

### Phase 4: Multi-Agent System

Different agents can read the same blocks.json:
- Document analysis agent
- Case law citation agent
- Timeline extraction agent

All use the same structured input.

---

## Summary

**Key Decisions:**

1. **Use blocks structure** - Not plain text, preserve context
2. **Save to MinIO** - Cheap object storage for large files
3. **Checkpoint at each step** - Can resume from failures
4. **Process one document at a time** - Control memory usage
5. **Unified model** - PDF, DOCX, TXT all use same structure

**Result:** Flexible, scalable, debuggable extraction pipeline that works across document types.

