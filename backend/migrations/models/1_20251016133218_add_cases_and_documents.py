from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS "cases" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "name" VARCHAR(255) NOT NULL,
    "description" TEXT
);
COMMENT ON TABLE "cases" IS 'Case model representing a legal case.';
        CREATE TABLE IF NOT EXISTS "documents" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "filename" VARCHAR(255) NOT NULL,
    "file_type" VARCHAR(7) NOT NULL,
    "file_size" BIGINT NOT NULL,
    "minio_bucket" VARCHAR(100) NOT NULL,
    "minio_key" VARCHAR(500) NOT NULL,
    "status" VARCHAR(17) NOT NULL  DEFAULT 'uploaded',
    "processing_error" TEXT,
    "classification" VARCHAR(50),
    "content_category" VARCHAR(50),
    "filter_confidence" DOUBLE PRECISION,
    "filter_reasoning" TEXT,
    "has_summary" BOOL NOT NULL  DEFAULT False,
    "summarized_at" TIMESTAMPTZ,
    "case_id" INT NOT NULL REFERENCES "cases" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "documents"."file_type" IS 'PDF: pdf\nDOCX: docx\nDOC: doc\nTXT: txt\nHTML: html\nUNKNOWN: unknown';
COMMENT ON COLUMN "documents"."status" IS 'UPLOADED: uploaded\nDETECTING_TYPE: detecting_type\nEXTRACTING_BLOCKS: extracting_blocks\nCLASSIFYING: classifying\nANALYZING_CONTENT: analyzing_content\nFILTERED_OUT: filtered_out\nCHUNKING: chunking\nSUMMARIZING: summarizing\nCOMPLETED: completed\nFAILED: failed';
COMMENT ON TABLE "documents" IS 'Document model representing an uploaded legal document.';"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS "cases";
        DROP TABLE IF EXISTS "documents";"""
