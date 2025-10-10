"""
Tortoise ORM configuration for Aerich migrations.

This is separate from core.config to avoid circular dependencies
and .env loading issues during migration operations.
"""

TORTOISE_ORM = {
    "connections": {
        "default": "postgres://postgres:postgres@localhost:5433/legal_ai_db"
    },
    "apps": {
        "models": {
            "models": ["core.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
