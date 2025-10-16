"""Text extraction strategy for plain text files (.txt)."""
import re
import hashlib
import unicodedata
from services.models import DocumentType, ExtractedDocument, Page, TextBlock
from services.text_extraction.base_extractor import BaseTextExtractor


class TextExtractor(BaseTextExtractor):
    """Extract text from plain text files (TXT ONLY).
    
    Creates logical pages (~5KB target, 10KB max) with overlap.
    Detects block types: paragraphs, list_items, headings, code_blocks.
    
    Note: This extractor ONLY handles .txt files. PDF and DOCX have separate extractors.
    """
    
    # Page sizing (in characters after UTF-8 decode)
    TARGET_PAGE_SIZE = 5000  # ~1,250 tokens
    MAX_PAGE_SIZE = 10000    # ~2,500 tokens hard cap
    MIN_PAGE_SIZE = 1500     # soft floor
    OVERLAP_RATIO = 0.10     # 10% overlap
    
    def can_handle(self, doc_type: DocumentType) -> bool:
        """Handle TEXT_EXTRACTABLE documents."""
        return doc_type == DocumentType.TEXT_EXTRACTABLE
    
    async def extract(self, file_data: bytes, filename: str, document_id: int) -> ExtractedDocument:
        """Extract text from plain TXT file with logical pages and block detection.
        
        Strategy:
        1. Decode bytes to UTF-8 text
        2. Normalize text (NFKC)
        3. Split into logical pages (~5KB each)
        4. Split each page into blocks (paragraphs)
        5. Detect block types (list_item, heading, code_block, paragraph)
        6. Calculate offsets, metrics, and hashes
        """
        # Step 1: Decode bytes to text
        try:
            text = file_data.decode('utf-8')
        except UnicodeDecodeError:
            # Fallback to latin-1 which accepts all byte values
            text = file_data.decode('latin-1', errors='replace')
        
        # Step 2: Normalize text (NFKC for consistent representation)
        text = unicodedata.normalize('NFKC', text)
        
        # Step 3: Split into logical pages
        pages = self._split_into_pages(text, document_id)
        
        # Build the extraction result
        total_blocks = sum(page.block_count for page in pages)
        
        extracted = ExtractedDocument(
            model="page_blocks.v1",
            version="extraction.v1",
            document_id=document_id,
            file_type="txt",
            original_filename=filename,
            page_count=len(pages),
            total_blocks=total_blocks,
            pages=pages,
            extraction_metadata={
                "original_size_bytes": len(file_data),
                "char_count": len(text),
                "encoding": "utf-8",
                "normalized": "NFKC"
            }
        )
        
        return extracted
    
    def _split_into_pages(self, text: str, document_id: int) -> list[Page]:
        """Split text into logical pages with overlap."""
        pages = []
        text_len = len(text)
        page_index = 0
        char_pos = 0
        
        while char_pos < text_len:
            # Calculate overlap from previous page
            overlap_chars = 0
            if page_index > 0:
                overlap_chars = int(self.TARGET_PAGE_SIZE * self.OVERLAP_RATIO)
                char_pos = max(0, char_pos - overlap_chars)
            
            # Determine page end position
            page_start = char_pos
            target_end = min(char_pos + self.TARGET_PAGE_SIZE, text_len)
            max_end = min(char_pos + self.MAX_PAGE_SIZE, text_len)
            
            # Find good boundary
            page_end, notes = self._find_page_boundary(
                text, page_start, target_end, max_end, text_len
            )
            
            # Extract page text
            page_text = text[page_start:page_end]
            
            # Create blocks for this page
            blocks = self._create_blocks(page_text, page_start, document_id, page_index)
            
            # Calculate page hash
            page_hash = hashlib.sha256(page_text.encode('utf-8')).hexdigest()[:16]
            
            # Create page
            page = Page(
                page_index=page_index,
                char_start=page_start,
                char_end=page_end,
                token_estimate=self._estimate_tokens(page_text),
                block_count=len(blocks),
                overlap_prev_chars=overlap_chars if page_index > 0 else None,
                hash=page_hash,
                notes=notes,
                blocks=blocks
            )
            
            pages.append(page)
            page_index += 1
            char_pos = page_end
        
        return pages
    
    def _find_page_boundary(
        self, 
        text: str, 
        start: int, 
        target_end: int, 
        max_end: int, 
        text_len: int
    ) -> tuple[int, str | None]:
        """Find optimal page boundary.
        
        Preference order:
        1. Paragraph boundary (\n\n)
        2. Sentence boundary (. ? !)
        3. Hard cut at max (mark with note)
        
        Returns:
            (end_position, notes)
        """
        # If we're at the end of document, just return
        if target_end >= text_len:
            return text_len, None
        
        # Try to find paragraph boundary near target
        # Look from target backward to start, and forward to max
        search_window = text[start:max_end]
        target_offset = target_end - start
        
        # Look for paragraph breaks (\n\n) near target
        # Search backward first (prefer slightly shorter pages)
        para_pattern = r'\n\n+'
        
        # Search backward from target (up to MIN_PAGE_SIZE)
        if target_offset > self.MIN_PAGE_SIZE:
            backward_start = max(self.MIN_PAGE_SIZE, target_offset - 1000)
            backward_text = search_window[backward_start:target_offset]
            matches = list(re.finditer(para_pattern, backward_text))
            if matches:
                # Take the last match (closest to target)
                last_match = matches[-1]
                boundary_offset = backward_start + last_match.end()
                return start + boundary_offset, None
        
        # Search forward from target (up to max)
        forward_text = search_window[target_offset:max_end - start]
        match = re.search(para_pattern, forward_text)
        if match:
            boundary_offset = target_offset + match.end()
            return start + boundary_offset, None
        
        # No paragraph boundary found, try sentence boundary
        sentence_pattern = r'[.!?]\s+'
        
        # Search backward
        if target_offset > self.MIN_PAGE_SIZE:
            backward_start = max(self.MIN_PAGE_SIZE, target_offset - 500)
            backward_text = search_window[backward_start:target_offset]
            matches = list(re.finditer(sentence_pattern, backward_text))
            if matches:
                last_match = matches[-1]
                boundary_offset = backward_start + last_match.end()
                return start + boundary_offset, None
        
        # Search forward
        forward_text = search_window[target_offset:max_end - start]
        match = re.search(sentence_pattern, forward_text)
        if match:
            boundary_offset = target_offset + match.end()
            return start + boundary_offset, None
        
        # No good boundary found - hard cut at max
        return start + (max_end - start), "hard_cut"
    
    def _create_blocks(
        self, 
        page_text: str, 
        page_start_offset: int, 
        document_id: int, 
        page_index: int
    ) -> list[TextBlock]:
        """Create blocks from page text with type detection."""
        blocks = []
        
        # Split on paragraph boundaries (blank lines)
        paragraphs = re.split(r'\n\n+', page_text)
        
        char_offset = 0
        block_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Calculate absolute char positions
            char_start = page_start_offset + char_offset
            char_end = char_start + len(para)
            
            # Detect block type
            block_kind = self._detect_block_kind(para)
            
            # Create block
            block = TextBlock(
                block_index=block_index,
                block_id=f"doc{document_id}_p{page_index}_b{block_index}",
                text=para,
                kind=block_kind,
                char_start=char_start,
                char_end=char_end,
                token_estimate=self._estimate_tokens(para),
                lines=para.count('\n') + 1
            )
            
            blocks.append(block)
            block_index += 1
            
            # Update offset (account for the paragraph + the separator we removed)
            # Find where this paragraph actually ends in the original text
            para_end_in_page = page_text.find(para, char_offset) + len(para)
            # Skip past any trailing whitespace including the \n\n
            while para_end_in_page < len(page_text) and page_text[para_end_in_page] in '\n\r\t ':
                para_end_in_page += 1
            char_offset = para_end_in_page
        
        return blocks
    
    def _detect_block_kind(self, text: str) -> str:
        """Detect block type from text content.
        
        Detection order:
        1. list_item: starts with -, *, or digit.
        2. heading: ALL-CAPS line or ends with :
        3. code_block: 4+ space indent or fenced
        4. paragraph: fallback
        """
        lines = text.split('\n')
        first_line = lines[0] if lines else ""
        
        # List item detection
        if re.match(r'^\s*[-*]\s+', first_line):
            return "list_item"
        if re.match(r'^\s*\d+\.\s+', first_line):
            return "list_item"
        
        # Heading detection (single line)
        if len(lines) == 1 or (len(lines) == 2 and not lines[1].strip()):
            # ALL-CAPS (at least 3 caps, and >50% of alphas are caps)
            alphas = [c for c in first_line if c.isalpha()]
            if len(alphas) >= 3:
                caps = sum(1 for c in alphas if c.isupper())
                if caps / len(alphas) > 0.5:
                    return "heading"
            
            # Ends with colon
            if first_line.strip().endswith(':'):
                return "heading"
        
        # Code block detection (all lines indented by 4+ spaces)
        if all(line.startswith('    ') or not line.strip() for line in lines):
            return "code_block"
        
        # Fenced code block
        if first_line.strip().startswith('```') or first_line.strip().startswith('~~~'):
            return "code_block"
        
        # Default
        return "paragraph"
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimate (~chars / 4)."""
        return max(1, round(len(text) / 4))
