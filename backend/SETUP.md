# LegalDocs AI - Setup Guide

Complete setup instructions for running the LegalDocs AI backend on any machine.

---

## Prerequisites

### Required Software
- **Python 3.12+** - https://www.python.org/downloads/
- **Poetry** - https://python-poetry.org/docs/#installation
- **Docker Desktop** - https://www.docker.com/products/docker-desktop/
- **Ollama** - https://ollama.ai/download

### Hardware Requirements

**Minimum (for testing):**
- CPU: 8-core
- RAM: 16GB
- Storage: 20GB free space

**Recommended (for production):**
- CPU: 12+ cores
- RAM: 32GB+ (64GB ideal for Llama 70B)
- GPU: NVIDIA RTX 3060+ with 12GB VRAM (optional but faster)
- Storage: 50GB+ free space (for models and documents)

---

## Installation Steps

### 1. Clone the Repository

```bash
cd C:\Coding\LegalDocs_AI\backend
```

### 2. Install Python Dependencies

```bash
# Install all Python packages
poetry install

# Verify installation
poetry run python --version
```

### 3. Setup Docker Services

**Start Docker Desktop** (make sure it's running)

```bash
# Start PostgreSQL and MinIO
docker-compose up -d postgres minio

# Wait for services to be healthy (10-15 seconds)
timeout /t 10

# Verify services are running
docker ps
```

You should see:
- `legaldocs_postgres` - Database
- `legaldocs_minio` - Object storage

**Access MinIO Console:**
- URL: http://localhost:9001
- Username: `minioadmin`
- Password: `minioadmin`

### 4. Setup Configuration

Create a `.env` file in the backend directory:

```env
# Application
APP_NAME=LegalDocs AI
DEBUG=true

# Database
DATABASE_URL=postgres://postgres:postgres@localhost:5433/legal_ai_db

# MinIO Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false

# Pinecone Vector Database (Optional - leave empty if not using)
PINECONE_API_KEY=
PINECONE_INDEX_NAME=law-analysis
PINECONE_REGION=us-east-1

# AI Models (Local via Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
EMBEDDING_MODEL=all-MiniLM-L6-v2
NER_MODEL=en_legal_ner_trf
```

### 5. Initialize Database

**Important:** If you have local PostgreSQL running on port 5432, stop it temporarily:
```bash
net stop postgresql-x64-16
```

**Run migrations:**
```bash
# Delete old migrations if they exist
rmdir /s /q migrations

# Initialize Aerich
poetry run aerich init -t core.tortoise_config.TORTOISE_ORM

# Create initial database schema
poetry run aerich init-db
```

**Restart local PostgreSQL if needed:**
```bash
net start postgresql-x64-16
```

### 6. Install Ollama

**Download and Install:**
1. Go to https://ollama.ai/download
2. Download the Windows installer
3. Run the installer
4. Ollama will start automatically as a service

**Verify Ollama is running:**
```bash
ollama --version
```

### 7. Download AI Models

**Option A: Quick Setup (8B model - faster, less RAM)**
```bash
# Download Llama 3.1 8B (~5GB)
ollama pull llama3.1:8b

# Test it works
ollama run llama3.1:8b "Hello, how are you?"
```

**Option B: Full Setup (70B model - better quality, needs more RAM)**
```bash
# Download Llama 3.1 70B (~40GB - will take a while)
ollama pull llama3.1:70b

# Update .env to use 70B model
# Change: OLLAMA_MODEL=llama3.1:70b
```

**Download spaCy Legal NER Model:**
```bash
poetry run python -m spacy download en_legal_ner_trf
```

### 8. Test AI Models

**Test LLM:**
```bash
poetry run python -c "from core.ml_utils import call_llm; import asyncio; print(asyncio.run(call_llm('What is 2+2? Answer in one sentence.')))"
```

**Test Embeddings:**
```bash
poetry run python -c "from core.ml_utils import generate_embeddings; print(f'Generated {len(generate_embeddings([\"test\"])[0])} dimensions')"
```

**Test Entity Extraction:**
```bash
poetry run python -c "from core.ml_utils import extract_entities; print(extract_entities('Apple Inc. filed a lawsuit in California.'))"
```

---

## Running the Application

### Start All Services

```bash
# Start infrastructure (PostgreSQL + MinIO)
docker-compose up -d postgres minio

# Start the API
poetry run uvicorn main:app --reload
```

### Access Points

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **MinIO Console**: http://localhost:9001

### Stop All Services

```bash
# Stop Docker services
docker-compose down

# Stop Ollama (if needed)
# Ollama runs as a Windows service, so it stays running
```

---

## Model Storage Locations

Downloaded models are stored locally:

**Ollama Models:**
- Windows: `C:\Users\<YourUser>\.ollama\models`
- Size: 5GB (8B) or 40GB (70B)

**Sentence Transformers:**
- Windows: `C:\Users\<YourUser>\.cache\torch\sentence_transformers`
- Size: ~100MB

**spaCy Models:**
- Inside Poetry virtualenv: `.venv\Lib\site-packages\en_legal_ner_trf`
- Size: ~400MB

---

## Upgrading Models

### Switch from 8B to 70B

```bash
# Download the 70B model
ollama pull llama3.1:70b

# Update .env
# Change: OLLAMA_MODEL=llama3.1:70b

# Restart the API
```

### Update to Latest Llama Version

```bash
# Check for updates
ollama list

# Pull latest version
ollama pull llama3.1:70b
```

---

## Troubleshooting

### "Could not connect to database"
- Make sure Docker Desktop is running
- Check if PostgreSQL container is healthy: `docker ps`
- Verify port 5433 is not in use: `netstat -an | findstr 5433`

### "Ollama connection refused"
- Check if Ollama is running: `ollama list`
- Restart Ollama service if needed
- Verify URL in .env: `OLLAMA_BASE_URL=http://localhost:11434`

### "Model not found"
- List downloaded models: `ollama list`
- Download missing model: `ollama pull llama3.1:8b`
- Check model name matches .env: `OLLAMA_MODEL=llama3.1:8b`

### "Out of memory when running 70B model"
- Switch to 8B model instead
- Close other applications
- Consider using quantized version: `ollama pull llama3.1:70b-q4_0`

### Migration errors
- Stop local PostgreSQL: `net stop postgresql-x64-16`
- Delete migrations folder: `rmdir /s /q migrations`
- Re-run migration commands
- Restart local PostgreSQL: `net start postgresql-x64-16`

---

## Development Workflow

```bash
# 1. Start infrastructure
docker-compose up -d postgres minio

# 2. Run migrations (if schema changed)
poetry run aerich migrate --name "your_change_description"
poetry run aerich upgrade

# 3. Start API with hot reload
poetry run uvicorn main:app --reload

# 4. Make changes, API auto-reloads

# 5. Test endpoints
# Visit: http://localhost:8000/docs
```

---

## Data Privacy & Security

✅ **All AI processing happens locally** - No data sent to external APIs  
✅ **Document storage is local** - MinIO runs on your machine  
✅ **Vector embeddings only** - Pinecone stores embeddings, not documents  
✅ **Offline capable** - Works without internet (except Pinecone queries)  
✅ **Full data control** - You own all the infrastructure  

Perfect for handling sensitive legal documents! 🔒

---

## Quick Reference

**Start everything:**
```bash
docker-compose up -d postgres minio
poetry run uvicorn main:app --reload
```

**Stop everything:**
```bash
docker-compose down
# Press Ctrl+C in the API terminal
```

**Reset database:**
```bash
docker-compose down -v
docker-compose up -d postgres
poetry run aerich init -t core.tortoise_config.TORTOISE_ORM
poetry run aerich init-db
```

**Check service status:**
```bash
docker ps                    # Docker services
ollama list                  # Downloaded AI models
poetry run python -c "from core.config import settings; print(settings.ollama_model)"  # Current config
```

---

## Next Steps

Once everything is running:
1. Check the health endpoint: http://localhost:8000/health
2. Explore the API docs: http://localhost:8000/docs
3. Start building features in `features/`

Happy coding! 🚀

