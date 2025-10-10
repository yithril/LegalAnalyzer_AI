"""Application configuration using Pydantic Settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Application
    app_name: str
    debug: bool
    
    # Database (PostgreSQL + Tortoise ORM)
    database_url: str
    
    # MinIO (S3-compatible storage)
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_secure: bool
    
    # Pinecone (Vector Database)
    pinecone_api_key: str = ""  # Empty string means Pinecone not configured
    pinecone_index_name: str = "law-analysis"  # Default index name
    pinecone_region: str = "us-east-1"  # For ServerlessSpec when creating new indexes
    
    # AI Models (Local - Ollama)
    ollama_base_url: str = "http://localhost:11434"  # Ollama API endpoint
    ollama_model: str = "llama3.1:70b"  # LLM for summarization/analysis
    embedding_model: str = "all-MiniLM-L6-v2"  # Sentence transformer for embeddings (for later)


# Singleton instance
settings = Settings()

