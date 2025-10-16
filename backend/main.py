"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from infrastructure.database import db_provider
from infrastructure.pinecone_client import pinecone_client
from infrastructure.storage import storage_client
from infrastructure.elasticsearch_client import elasticsearch_client
from controllers.case_controller import router as case_router
from controllers.document_controller import router as document_router
from controllers.auth_controller import router as auth_router


app = FastAPI(title="LegalDocs AI Backend", version="0.1.0")

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,  # Important for cookies (NextAuth session)
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)  # No auth required for login
app.include_router(case_router)
app.include_router(document_router)


@app.on_event("startup")
async def startup():
    """Initialize infrastructure providers on app startup."""
    await db_provider.init()
    print("Database provider initialized")
    
    await pinecone_client.init()
    print("Pinecone client initialized")
    
    await storage_client.init()
    print("Storage client initialized")
    
    await elasticsearch_client.init()
    print("Elasticsearch client initialized")


@app.on_event("shutdown")
async def shutdown():
    """Close infrastructure providers on app shutdown."""
    await db_provider.close()
    print("Database provider closed")
    
    await elasticsearch_client.close()
    print("Elasticsearch client closed")


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "LegalDocs AI Backend", "status": "running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    db_healthy = await db_provider.health_check()
    pinecone_healthy = await pinecone_client.health_check()
    storage_healthy = await storage_client.health_check()
    
    all_healthy = db_healthy and storage_healthy
    # Pinecone is optional (requires API key)
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "storage": "connected" if storage_healthy else "disconnected",
        "pinecone": "connected" if pinecone_healthy else "not configured"
    }

