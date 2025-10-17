# Integration Tests

End-to-end integration tests that use **real services** (not mocks).

## What These Tests Do

These tests verify the complete document processing pipeline from upload to storage:

1. **Upload** → MinIO storage
2. **Extract** → Text extraction (already plain text for .txt files)
3. **Classify** → Document classification (email, contract, etc.)
4. **Chunk** → Semantic chunking with Legal-BERT
5. **Embed** → Generate and store embeddings in Pinecone
6. **Summarize** → Generate summary with Ollama LLM
7. **Store** → Save summary in Elasticsearch

## Prerequisites

### Required Services Running

All services must be running before running integration tests:

```bash
# 1. Start Docker services
cd backend
docker-compose up -d

# Services:
# - PostgreSQL (port 5433)
# - MinIO (port 9000, 9001)
# - Elasticsearch (port 9200)
```

### Environment Variables

Create/update `backend/.env`:

```bash
# Database
DATABASE_URL=postgres://postgres:postgres@localhost:5433/legal_ai_db

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

# Pinecone (REQUIRED for integration tests)
PINECONE_API_KEY=your_api_key_here
PINECONE_INDEX_NAME=legal-docs-dev
PINECONE_REGION=us-east-1

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_INDEX_SUMMARIES=document_summaries

# Ollama (for summarization)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

### Ollama Setup

Install and start Ollama for LLM summarization:

```bash
# Install Ollama: https://ollama.ai/
# Pull the model
ollama pull llama3.1:8b

# Ollama runs automatically on http://localhost:11434
```

## Running Tests

### Run All Integration Tests

```bash
cd backend
poetry run pytest tests/integration/ -v -s
```

### Run Specific Test

```bash
poetry run pytest tests/integration/test_full_pipeline.py::test_enron_email_full_pipeline -v -s
```

### Skip Integration Tests (Fast Unit Tests Only)

```bash
poetry run pytest -m "not integration" -v
```

## Test Data

- **Case ID**: 999 (isolated from production data)
- **Test File**: `tests/helpers/sample_files/text/43.txt` (Enron email about power contracts)
- **Cleanup**: All test data is deleted after verification

## What Gets Verified

✅ **PostgreSQL**
- Case record created
- Document record with correct status
- Classification stored
- Summary flag set

✅ **MinIO**
- Original file uploaded
- Extraction blocks saved
- Chunks backup saved

✅ **Pinecone**
- Embeddings stored
- Metadata includes `case_id=999`
- Multiple chunks created
- Case filtering works

✅ **Elasticsearch**
- Summary document indexed
- Summary contains business terms
- Can retrieve by document ID

## Test Output

```
=== STEP 1: Upload to MinIO ===
✓ Uploaded to MinIO: cases/999/documents/test_upload/43.txt

=== STEP 2: Create Document Record ===
✓ Created document: 123

=== STEP 3: Process Document (Orchestrator) ===
✓ Document processing completed

=== STEP 4: Verify PostgreSQL ===
✓ Document status: completed
✓ Classification: email
✓ Has summary: True

=== STEP 5: Verify MinIO ===
✓ Original file exists
✓ Extraction blocks exist
✓ Chunks backup exists

=== STEP 6: Verify Pinecone ===
✓ Found 8 embeddings in Pinecone
✓ Metadata correct: case_id=999, document_id=123
✓ Document chunked into 8 semantic chunks

=== STEP 7: Verify Elasticsearch ===
✓ Summary found in Elasticsearch
✓ Summary length: 450 characters
✓ Summary preview: This email confirms modifications...

=== STEP 8: Test Case Isolation ===
✓ Case isolation working: all 8 results have case_id=999

=== CLEANUP: Deleting Test Data ===
✓ Deleted 8 embeddings from Pinecone
✓ Deleted summary from Elasticsearch
✓ Deleted all files from MinIO
✓ Deleted document from PostgreSQL

✅ ALL TESTS PASSED - Pipeline working end-to-end!
```

## Troubleshooting

### Pinecone Connection Error
- Check `PINECONE_API_KEY` is set
- Verify index exists: `legal-docs-dev`
- Check index dimension is 768 (Legal-BERT)

### Ollama Timeout
- Make sure Ollama is running: `ollama list`
- Model downloaded: `ollama pull llama3.1:8b`
- Check Ollama is accessible: `curl http://localhost:11434`

### MinIO Connection Error
- Verify docker-compose is running: `docker ps`
- Check MinIO console: http://localhost:9001
- Login: minioadmin / minioadmin

### Database Connection Error
- Check PostgreSQL is running: `docker ps | grep postgres`
- Port 5433 is exposed (not 5432 to avoid conflicts)

## For Presentation Demo

To keep test data for inspection (don't run cleanup):

1. Comment out the cleanup section in the test
2. Run the test
3. Inspect results:
   - Pinecone: Query with `case_id=999` filter
   - Elasticsearch: GET `/document_summaries/_doc/{document_id}`
   - MinIO: Browse http://localhost:9001
   - PostgreSQL: Query `SELECT * FROM documents WHERE case_id = 999`

Then manually cleanup when done:

```python
# Delete from Pinecone
index.delete(filter={"case_id": 999})

# Delete from database
await Document.filter(case_id=999).delete()
await Case.filter(id=999).delete()
```

