"""PDF extraction using PyMuPDF with native OCR support."""
import hashlib
import os
from pathlib import Path
import fitz  # PyMuPDF
import pytesseract
from services.models import DocumentType, ExtractedDocument, Page, TextBlock, FontInfo, ImageMetadata
from services.text_extraction.base_extractor import BaseTextExtractor


# Configure Tesseract path for Windows so PyMuPDF can find it
if os.name == 'nt':  # Windows
    possible_paths = [
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    ]
    for path in possible_paths:
        if Path(path).exists():
            pytesseract.pytesseract.tesseract_cmd = path
            # Also set environment variable for PyMuPDF
            os.environ['TESSDATA_PREFIX'] = str(Path(path).parent / 'tessdata')
            break


class PDFExtractor(BaseTextExtractor):
    """Extract text and metadata from PDF files.
    
    Features:
    - Detects if pages have text layer or need OCR
    - Extracts text blocks with layout information (bbox, font)
    - Records image metadata without extracting pixels
    - Flags scanned pages for later OCR processing
    """
    
    # Simple detection: trust PyMuPDF, use Tesseract as fallback
    MIN_CHAR_COUNT = 50  # If page has < 50 chars, run OCR
    
    def can_handle(self, doc_type: DocumentType) -> bool:
        """Handle TEXT_EXTRACTABLE documents."""
        return doc_type == DocumentType.TEXT_EXTRACTABLE
    
    async def extract(self, file_data: bytes, filename: str, document_id: int) -> ExtractedDocument:
        """
        Extract text and structure from PDF with OCR detection.
        
        Args:
            file_data: Raw PDF bytes
            filename: Original filename
            document_id: Database ID of the document
            
        Returns:
            ExtractedDocument with pages, blocks, and OCR flags
        """
        # Open PDF with PyMuPDF
        doc = fitz.open(stream=file_data, filetype="pdf")
        
        pages = []
        total_blocks = 0
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
            # Extract page
            extracted_page = await self._extract_page(page, page_num, document_id)
            pages.append(extracted_page)
            total_blocks += extracted_page.block_count
        
        doc.close()
        
        # Build extraction result
        extracted = ExtractedDocument(
            model="page_blocks.v1",
            version="extraction.v1",
            document_id=document_id,
            file_type="pdf",
            original_filename=filename,
            page_count=len(pages),
            total_blocks=total_blocks,
            pages=pages,
            extraction_metadata={
                "pdf_version": doc.metadata.get("format", "unknown"),
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "pages_needing_ocr": sum(1 for p in pages if p.needs_ocr)
            }
        )
        
        return extracted
    
    async def _extract_page(self, page: fitz.Page, page_num: int, document_id: int) -> Page:
        """Extract text and metadata from a single PDF page."""
        
        # Get page dimensions
        rect = page.rect
        width_pts = rect.width
        height_pts = rect.height
        rotation = page.rotation
        
        # Try to extract text with PyMuPDF
        text = page.get_text()
        char_count = len(text.strip())
        
        # Get images
        images = page.get_images()
        image_count = len(images)
        page_area = width_pts * height_pts
        
        # Simple decision: Trust PyMuPDF
        if char_count >= self.MIN_CHAR_COUNT:
            # PyMuPDF found text - use it!
            blocks = self._extract_text_blocks(page, page_num, document_id)
            needs_ocr = False
            has_text_layer = True
            page_kind = "normal"
        else:
            # PyMuPDF found nothing - OCR it!
            blocks = await self._ocr_page_with_pymupdf(page, page_num, document_id)
            needs_ocr = True
            has_text_layer = False
            page_kind = "scan_candidate"
        
        # Add image blocks
        image_blocks = self._extract_image_blocks(page, page_num, document_id, images, page_area)
        blocks.extend(image_blocks)
        
        # Calculate page hash
        page_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]
        
        # Create Page object
        return Page(
            page_index=page_num,
            width=width_pts,
            height=height_pts,
            rotation=rotation,
            char_count=char_count,
            has_text_layer=has_text_layer,
            needs_ocr=needs_ocr,
            page_kind=page_kind,
            image_count=image_count,
            token_estimate=self._estimate_tokens(text),
            block_count=len(blocks),
            hash=page_hash,
            blocks=blocks
        )
    
    async def _ocr_page_with_pymupdf(self, page: fitz.Page, page_num: int, document_id: int) -> list[TextBlock]:
        """Run PyMuPDF's native OCR on a page that has no text layer.
        
        Args:
            page: PyMuPDF page object
            page_num: Page index
            document_id: Document ID
            
        Returns:
            List of TextBlocks with OCR'd text
        """
        print(f"  [OCR] Page {page_num}: Running PyMuPDF OCR...")
        
        try:
            # Use PyMuPDF's native OCR - returns a TextPage object
            # dpi=300 for good quality, language="eng" for English
            textpage = page.get_textpage_ocr(dpi=300, language="eng")
            
            # Extract structured blocks just like we do for normal PDFs
            text_dict = textpage.extractDICT()
            
            # Use the same extraction logic as normal PDF text
            blocks = []
            block_index = 0
            
            for block in text_dict.get("blocks", []):
                # Skip image blocks
                if block.get("type") != 0:  # 0 = text block
                    continue
                
                # Extract text from lines
                lines = []
                for line in block.get("lines", []):
                    line_text = ""
                    for span in line.get("spans", []):
                        line_text += span.get("text", "")
                    if line_text.strip():
                        lines.append(line_text)
                
                if not lines:
                    continue
                
                block_text = "\n".join(lines).strip()
                if not block_text:
                    continue
                
                # Get bbox
                bbox = block.get("bbox", [0, 0, 0, 0])
                
                # Get font info from first span (if available)
                font_info = None
                if block.get("lines") and block["lines"][0].get("spans"):
                    first_span = block["lines"][0]["spans"][0]
                    font_info = FontInfo(
                        size=first_span.get("size"),
                        bold="Bold" in first_span.get("font", ""),
                        italic="Italic" in first_span.get("font", ""),
                        font_name=first_span.get("font")
                    )
                
                # Detect block kind
                kind = self._detect_block_kind(block_text, bbox, page.rect)
                
                # Create block
                text_block = TextBlock(
                    block_index=block_index,
                    block_id=f"doc{document_id}_p{page_num}_b{block_index}",
                    text=block_text,
                    kind=kind,
                    bbox=list(bbox),
                    font=font_info,
                    token_estimate=self._estimate_tokens(block_text),
                    lines=len(lines)
                )
                
                blocks.append(text_block)
                block_index += 1
            
            # If OCR found nothing, add placeholder
            if not blocks:
                blocks.append(TextBlock(
                    block_index=0,
                    block_id=f"doc{document_id}_p{page_num}_b0",
                    text="[OCR found no text]",
                    kind="ocr_no_text",
                    bbox=[0, 0, page.rect.width, page.rect.height],
                    token_estimate=0,
                    lines=1
                ))
            
            print(f"  [OCR] Page {page_num}: Extracted {len(blocks)} blocks")
            return blocks
            
        except Exception as e:
            # If OCR fails, return error block
            print(f"  [OCR] Page {page_num}: OCR failed - {str(e)}")
            return [TextBlock(
                block_index=0,
                block_id=f"doc{document_id}_p{page_num}_b0",
                text=f"[OCR failed: {str(e)}]",
                kind="ocr_error",
                bbox=[0, 0, page.rect.width, page.rect.height],
                token_estimate=0,
                lines=1
            )]
    
    def _extract_text_blocks(self, page: fitz.Page, page_num: int, document_id: int) -> list[TextBlock]:
        """Extract text blocks with layout information from page."""
        blocks = []
        
        # Get text blocks with layout info
        text_dict = page.get_text("dict")
        
        block_index = 0
        for block in text_dict.get("blocks", []):
            # Skip image blocks (handled separately)
            if block.get("type") != 0:  # 0 = text block
                continue
            
            # Extract text from lines
            lines = []
            for line in block.get("lines", []):
                line_text = ""
                for span in line.get("spans", []):
                    line_text += span.get("text", "")
                if line_text.strip():
                    lines.append(line_text)
            
            if not lines:
                continue
            
            block_text = "\n".join(lines).strip()
            if not block_text:
                continue
            
            # Get bbox
            bbox = block.get("bbox", [0, 0, 0, 0])
            
            # Get font info from first span
            font_info = None
            if block.get("lines") and block["lines"][0].get("spans"):
                first_span = block["lines"][0]["spans"][0]
                font_info = FontInfo(
                    size=first_span.get("size"),
                    bold="Bold" in first_span.get("font", ""),
                    italic="Italic" in first_span.get("font", ""),
                    font_name=first_span.get("font")
                )
            
            # Detect block kind (simple heuristics)
            kind = self._detect_block_kind(block_text, bbox, page.rect)
            
            # Create block
            text_block = TextBlock(
                block_index=block_index,
                block_id=f"doc{document_id}_p{page_num}_b{block_index}",
                text=block_text,
                kind=kind,
                bbox=list(bbox),
                font=font_info,
                token_estimate=self._estimate_tokens(block_text),
                lines=len(lines)
            )
            
            blocks.append(text_block)
            block_index += 1
        
        return blocks
    
    
    def _extract_image_blocks(
        self, 
        page: fitz.Page, 
        page_num: int, 
        document_id: int, 
        images: list,
        page_area: float
    ) -> list[TextBlock]:
        """Extract image metadata blocks (without actual pixel data)."""
        image_blocks = []
        
        for img_index, img_info in enumerate(images):
            xref = img_info[0]
            
            try:
                # Get image rectangles (positions)
                img_rects = page.get_image_rects(xref)
                
                if not img_rects:
                    continue
                
                # Use first rectangle (images can appear multiple times)
                rect = img_rects[0]
                
                # Get image properties
                img_dict = page.parent.extract_image(xref)
                width_px = img_dict.get("width", 0)
                height_px = img_dict.get("height", 0)
                
                # Calculate coverage
                img_area = rect.width * rect.height
                coverage = img_area / page_area if page_area > 0 else 0
                
                # Create image metadata
                metadata = ImageMetadata(
                    image_index=img_index,
                    width_px=width_px,
                    height_px=height_px,
                    page_coverage=coverage,
                    image_id=f"doc{document_id}_p{page_num}_img{img_index}"
                )
                
                # Create image block
                image_block = TextBlock(
                    block_index=len(image_blocks),  # Will be offset by caller
                    block_id=f"doc{document_id}_p{page_num}_img{img_index}",
                    text="",  # Images have no text
                    kind="image",
                    bbox=[rect.x0, rect.y0, rect.x1, rect.y1],
                    image_metadata=metadata,
                    token_estimate=0,
                    lines=0
                )
                
                image_blocks.append(image_block)
                
            except Exception:
                # Skip images we can't process
                continue
        
        return image_blocks
    
    def _detect_block_kind(self, text: str, bbox: list, page_rect: fitz.Rect) -> str:
        """Detect block type from text and position."""
        # Simple heuristics for legal documents
        
        # Check if in header/footer region (top 10% or bottom 10%)
        y0, y1 = bbox[1], bbox[3]
        page_height = page_rect.height
        
        if y0 < page_height * 0.1:
            return "header"
        elif y1 > page_height * 0.9:
            return "footer"
        
        # Check if all caps and short (likely heading)
        if len(text) < 100 and text.isupper():
            return "heading"
        
        # Default to paragraph
        return "paragraph"
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate (~chars / 4)."""
        return max(1, round(len(text) / 4))

