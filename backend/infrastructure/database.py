"""Database provider for Tortoise ORM lifecycle management."""
from typing import Optional
from tortoise import Tortoise, connections
from core.config import settings


class DatabaseProvider:
    """Manages Tortoise ORM connections and lifecycle.
    
    Designed to support single database for MVP with easy path to multi-tenancy later.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize the database provider.
        
        Args:
            database_url: Optional database URL override. Uses settings if not provided.
        """
        self.database_url = database_url or settings.database_url
        self.initialized = False
    
    async def init(self) -> None:
        """Initialize Tortoise ORM.
        
        Call this on application startup. Uses Aerich for migrations,
        so we don't auto-generate schemas.
        """
        if self.initialized:
            return
        
        await Tortoise.init(
            db_url=self.database_url,
            modules={"models": ["core.models", "aerich.models"]}
        )
        self.initialized = True
    
    async def close(self) -> None:
        """Close all database connections.
        
        Call this on application shutdown.
        """
        if not self.initialized:
            return
        
        await connections.close_all()
        self.initialized = False
    
    async def health_check(self) -> bool:
        """Check if database is reachable.
        
        Returns:
            True if database connection is healthy, False otherwise.
        """
        if not self.initialized:
            return False
        
        try:
            conn = connections.get("default")
            await conn.execute_query("SELECT 1")
            return True
        except Exception:
            return False


# Singleton instance for FastAPI dependency injection
db_provider = DatabaseProvider()

