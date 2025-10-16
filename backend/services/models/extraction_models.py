"""Pydantic models for document extraction results.

These models define the structure for extracted text with layout information.
All document types (PDF, DOCX, TXT) are normalized into this common format.

Based on the page_blocks.v1 model specification.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class FontInfo(BaseModel):
    """Font information for a text block.
    
    Helps understand document structure (headers vs body text).
    """
    size: Optional[float] = Field(None, description="Font size in points")
    bold: Optional[bool] = Field(None, description="Whether text is bold")
    italic: Optional[bool] = Field(None, description="Whether text is italic")
    font_name: Optional[str] = Field(None, description="Font family name")


class ImageMetadata(BaseModel):
    """Metadata about an embedded image (without the actual image data).
    
    For PDF images, we record position and size but don't embed pixels in JSON.
    Actual image extraction can happen later if needed.
    """
    image_index: int = Field(..., description="Index of this image on the page (0-based)")
    width_px: int = Field(..., description="Image width in pixels")
    height_px: int = Field(..., description="Image height in pixels")
    page_coverage: float = Field(..., description="Fraction of page covered by image (0.0-1.0)")
    image_id: str = Field(..., description="Unique identifier like 'doc123_p2_img0'")


class TextBlock(BaseModel):
    """A single block of text with layout information.
    
    A block is typically a paragraph, heading, list item, or other logical text unit.
    """
    block_index: int = Field(..., description="Index of this block within the page (0-based)")
    block_id: Optional[str] = Field(None, description="Unique identifier for this block (e.g., 'doc123_p0_b5')")
    text: str = Field(..., description="The actual text content")
    kind: str = Field(
        default="paragraph",
        description="Block type: 'paragraph', 'list_item', 'heading', 'code_block', 'line', 'header', 'footer', 'table'"
    )
    
    # Position information (for TXT/HTML - absolute document positions)
    char_start: Optional[int] = Field(None, description="Character offset start in document (absolute, 0-based)")
    char_end: Optional[int] = Field(None, description="Character offset end in document (absolute, exclusive)")
    byte_start: Optional[int] = Field(None, description="Byte offset start in document")
    byte_end: Optional[int] = Field(None, description="Byte offset end in document")
    
    # Layout information (for PDF - page-relative positions)
    bbox: Optional[list[float]] = Field(
        None, 
        description="Bounding box [x0, y0, x1, y1] in page coordinates. None for formats without layout."
    )
    font: Optional[FontInfo] = Field(None, description="Font information if available")
    
    # Metrics
    token_estimate: Optional[int] = Field(None, description="Rough token count (~chars / 4)")
    lines: Optional[int] = Field(None, description="Number of lines in this block")
    
    # Image metadata (only present when kind="image")
    image_metadata: Optional[ImageMetadata] = Field(None, description="Image metadata if this is an image block")
    
    # Legacy field for backward compatibility
    kind_hint: Optional[str] = Field(None, description="DEPRECATED: Use 'kind' instead")
    
    class Config:
        json_schema_extra = {
            "example": {
                "block_index": 0,
                "block_id": "doc123_p0_b0",
                "text": "This is a paragraph.",
                "kind": "paragraph",
                "char_start": 0,
                "char_end": 21,
                "token_estimate": 5,
                "lines": 1
            }
        }


class Page(BaseModel):
    """A single page containing multiple text blocks.
    
    For formats without real pages (DOCX, TXT), this represents a logical page.
    """
    page_index: int = Field(..., description="Page number (0-based)")
    
    # Physical dimensions (for PDFs, images)
    width: Optional[float] = Field(None, description="Page width in points. None for non-layout formats.")
    height: Optional[float] = Field(None, description="Page height in points. None for non-layout formats.")
    
    # Position information (for TXT/HTML logical pages)
    byte_start: Optional[int] = Field(None, description="Byte offset start in document")
    byte_end: Optional[int] = Field(None, description="Byte offset end in document (exclusive)")
    char_start: Optional[int] = Field(None, description="Character offset start after UTF-8 decode (inclusive)")
    char_end: Optional[int] = Field(None, description="Character offset end after UTF-8 decode (exclusive)")
    
    # Metrics
    token_estimate: Optional[int] = Field(None, description="Rough token count for this page (~chars / 4)")
    block_count: int = Field(default=0, description="Number of blocks on this page")
    overlap_prev_chars: Optional[int] = Field(None, description="Number of overlapping chars with previous page")
    char_count: Optional[int] = Field(None, description="Character count on this page (for debugging/OCR detection)")
    
    # PDF-specific fields
    rotation: Optional[int] = Field(None, description="Page rotation in degrees (0, 90, 180, 270)")
    has_text_layer: Optional[bool] = Field(None, description="Does page have extractable text?")
    needs_ocr: Optional[bool] = Field(None, description="Should this page be OCR'd?")
    page_kind: Optional[str] = Field(None, description="Page classification: 'normal', 'scan_candidate', 'blank'")
    image_count: Optional[int] = Field(None, description="Number of images on this page")
    
    # Integrity & debugging
    hash: Optional[str] = Field(None, description="Stable hash of the page text for idempotency (e.g., SHA-256)")
    notes: Optional[str] = Field(None, description="Extraction hints (e.g., 'hard_cut', 'synthesized page')")
    
    # Content
    blocks: list[TextBlock] = Field(default_factory=list, description="Text blocks on this page")
    
    class Config:
        json_schema_extra = {
            "example": {
                "page_index": 0,
                "char_start": 0,
                "char_end": 5000,
                "token_estimate": 1250,
                "block_count": 12,
                "blocks": []
            }
        }


class ExtractedDocument(BaseModel):
    """Complete extraction result for a document.
    
    This is the top-level structure saved to MinIO as blocks.json.
    Contains all pages, blocks, and metadata about the extraction.
    """
    model: Literal["page_blocks.v1"] = Field(
        default="page_blocks.v1",
        description="Data model version for extraction format"
    )
    version: str = Field(
        default="extraction.v1",
        description="Extraction pipeline version"
    )
    document_id: int = Field(..., description="ID of the document in the database")
    file_type: str = Field(..., description="Original file type (pdf, docx, txt)")
    original_filename: str = Field(..., description="Original filename as uploaded (e.g., 'enron1992.pdf')")
    page_count: int = Field(..., description="Total number of pages")
    total_blocks: int = Field(..., description="Total number of text blocks across all pages")
    pages: list[Page] = Field(default_factory=list, description="All pages with their blocks")
    
    # Optional extraction metadata
    extraction_metadata: Optional[dict] = Field(
        None,
        description="Additional metadata from extraction (e.g., PDF metadata, word count)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "page_blocks.v1",
                "version": "extraction.v1",
                "document_id": 123,
                "file_type": "pdf",
                "page_count": 5,
                "total_blocks": 47,
                "pages": [
                    {
                        "page_index": 0,
                        "width": 612.0,
                        "height": 792.0,
                        "blocks": []
                    }
                ]
            }
        }
    
    def get_all_text(self, include_kinds: Optional[list[str]] = None, exclude_kinds: Optional[list[str]] = None) -> str:
        """Get all text from document, optionally filtering by block kind.
        
        Args:
            include_kinds: Only include blocks with these kinds. None = include all.
            exclude_kinds: Exclude blocks with these kinds.
            
        Returns:
            Combined text from all matching blocks
            
        Examples:
            # Get only body text (skip headers/footers)
            body_text = doc.get_all_text(exclude_kinds=["header", "footer"])
            
            # Get only headers
            headers = doc.get_all_text(include_kinds=["header"])
        """
        texts = []
        for page in self.pages:
            for block in page.blocks:
                # Apply filters
                kind = block.kind or block.kind_hint or "paragraph"
                if include_kinds and kind not in include_kinds:
                    continue
                if exclude_kinds and kind in exclude_kinds:
                    continue
                texts.append(block.text)
        
        return "\n\n".join(texts)
    
    def get_page_text(self, page_index: int, exclude_kinds: Optional[list[str]] = None) -> str:
        """Get all text from a specific page.
        
        Args:
            page_index: Index of page to extract (0-based)
            exclude_kinds: Exclude blocks with these kinds
            
        Returns:
            Combined text from page
        """
        if page_index >= len(self.pages):
            return ""
        
        page = self.pages[page_index]
        texts = []
        for block in page.blocks:
            kind = block.kind or block.kind_hint or "paragraph"
            if exclude_kinds and kind in exclude_kinds:
                continue
            texts.append(block.text)
        
        return "\n\n".join(texts)
    
    def get_blocks_by_kind(self, kind: str) -> list[TextBlock]:
        """Get all blocks matching a specific kind.
        
        Args:
            kind: The kind to match (e.g., "header", "paragraph", "list_item")
            
        Returns:
            List of matching blocks across all pages
        """
        blocks = []
        for page in self.pages:
            for block in page.blocks:
                block_kind = block.kind or block.kind_hint or "paragraph"
                if block_kind == kind:
                    blocks.append(block)
        return blocks

