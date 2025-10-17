from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "documents" ADD "relevance_score" INT;
        ALTER TABLE "documents" ADD "relevance_reasoning" TEXT;
        ALTER TABLE "documents" ADD "relevance_scored_at" TIMESTAMPTZ;
        ALTER TABLE "documents" ADD "relevance_manual_override" BOOL NOT NULL  DEFAULT False;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "documents" DROP COLUMN "relevance_score";
        ALTER TABLE "documents" DROP COLUMN "relevance_reasoning";
        ALTER TABLE "documents" DROP COLUMN "relevance_scored_at";
        ALTER TABLE "documents" DROP COLUMN "relevance_manual_override";"""
