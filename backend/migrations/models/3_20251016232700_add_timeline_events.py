from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "documents" ALTER COLUMN "file_type" TYPE VARCHAR(4) USING "file_type"::VARCHAR(4);
        ALTER TABLE "documents" ALTER COLUMN "status" TYPE VARCHAR(17) USING "status"::VARCHAR(17);
        CREATE TABLE IF NOT EXISTS "timeline_events" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "actors" JSONB,
    "action" VARCHAR(500) NOT NULL,
    "object_affected" TEXT,
    "event_date" DATE,
    "event_date_end" DATE,
    "date_precision" VARCHAR(20) NOT NULL  DEFAULT 'unknown',
    "date_original_text" VARCHAR(200),
    "legal_significance_score" INT NOT NULL,
    "state_changes" JSONB NOT NULL,
    "legal_reasoning" TEXT NOT NULL,
    "key_factors" JSONB NOT NULL,
    "extracted_text" TEXT NOT NULL,
    "extraction_confidence" INT NOT NULL  DEFAULT 50,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "case_id" INT NOT NULL REFERENCES "cases" ("id") ON DELETE CASCADE,
    "document_id" INT NOT NULL REFERENCES "documents" ("id") ON DELETE CASCADE
);
COMMENT ON TABLE "timeline_events" IS 'A legally significant event extracted from a document.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "documents" ALTER COLUMN "file_type" TYPE VARCHAR(7) USING "file_type"::VARCHAR(7);
        ALTER TABLE "documents" ALTER COLUMN "status" TYPE VARCHAR(17) USING "status"::VARCHAR(17);
        DROP TABLE IF EXISTS "timeline_events";"""
