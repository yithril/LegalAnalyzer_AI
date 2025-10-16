"""
Tests for TXT file text extraction.

Tests extraction of plain text files into logical pages with block detection.
"""
import pytest
import json
from pathlib import Path
from services.text_extraction.text_extractor import TextExtractor
from services.models import DocumentType


@pytest.fixture
def txt_extractor():
    """Create TextExtractor instance."""
    return TextExtractor()


@pytest.fixture
def sample_files_dir():
    """Path to sample text files."""
    return Path(__file__).parent.parent / "helpers" / "sample_files" / "text"


@pytest.fixture
def output_dir():
    """Path to output directory for extracted JSON (mimics MinIO structure)."""
    # Mimic production structure: cases/case_X/documents/doc_Y/extraction/
    output = Path(__file__).parent.parent / "file_output"
    output.mkdir(exist_ok=True)
    return output


def save_extraction_output(result, case_id: int, output_dir: Path):
    """Save extraction result to file_output with production-like structure.
    
    Structure: file_output/cases/case_X/documents/doc_Y/extraction/blocks.json
    """
    doc_id = result.document_id
    
    # Create directory structure
    extraction_dir = output_dir / "cases" / f"case_{case_id}" / "documents" / f"doc_{doc_id}" / "extraction"
    extraction_dir.mkdir(parents=True, exist_ok=True)
    
    # Save blocks.json
    blocks_path = extraction_dir / "blocks.json"
    with open(blocks_path, 'w', encoding='utf-8') as f:
        json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
    
    return blocks_path


@pytest.mark.asyncio
class TestTxtExtractor:
    """Test TXT file extraction."""
    
    async def test_can_handle_text_extractable(self, txt_extractor):
        """Should handle TEXT_EXTRACTABLE document type."""
        assert txt_extractor.can_handle(DocumentType.TEXT_EXTRACTABLE) is True
        assert txt_extractor.can_handle(DocumentType.OCR_NEEDED) is False
    
    async def test_extract_small_email(self, txt_extractor, sample_files_dir, output_dir):
        """Should extract real_email.txt with logical pages."""
        # Load file
        file_path = sample_files_dir / "real_email.txt"
        file_data = file_path.read_bytes()
        
        # Extract
        result = await txt_extractor.extract(
            file_data=file_data,
            filename="real_email.txt",
            document_id=1
        )
        
        # Verify structure
        assert result.model == "page_blocks.v1"
        assert result.document_id == 1
        assert result.file_type == "txt"
        assert result.page_count >= 1
        assert result.total_blocks > 0
        assert len(result.pages) == result.page_count
        
        # Verify extraction metadata
        assert "original_size_bytes" in result.extraction_metadata
        assert "char_count" in result.extraction_metadata
        assert result.extraction_metadata["encoding"] == "utf-8"
        
        # Verify pages have required fields
        for page in result.pages:
            assert page.char_start is not None
            assert page.char_end is not None
            assert page.char_end > page.char_start
            assert page.token_estimate is not None
            assert page.token_estimate > 0
            assert page.block_count == len(page.blocks)
            assert page.hash is not None
        
        # Verify blocks have required fields
        for page in result.pages:
            for block in page.blocks:
                assert block.text
                assert block.kind in ["paragraph", "list_item", "heading", "code_block"]
                assert block.char_start is not None
                assert block.char_end is not None
                assert block.token_estimate is not None
                assert block.lines is not None
                assert block.block_id is not None
        
        # Save output using production structure
        output_path = save_extraction_output(result, case_id=1, output_dir=output_dir)
        
        print(f"\n[PASS] Extracted real_email.txt:")
        print(f"   Pages: {result.page_count}")
        print(f"   Total blocks: {result.total_blocks}")
        print(f"   Char count: {result.extraction_metadata['char_count']:,}")
        print(f"   Saved to: {output_path}")
    
    async def test_extract_spam_email(self, txt_extractor, sample_files_dir, output_dir):
        """Should extract spam.txt with logical pages."""
        file_path = sample_files_dir / "spam.txt"
        file_data = file_path.read_bytes()
        
        result = await txt_extractor.extract(
            file_data=file_data,
            filename="spam.txt",
            document_id=2
        )
        
        assert result.page_count >= 1
        assert result.total_blocks > 0
        
        # Save output using production structure
        output_path = save_extraction_output(result, case_id=1, output_dir=output_dir)
        
        print(f"\n[PASS] Extracted spam.txt:")
        print(f"   Pages: {result.page_count}")
        print(f"   Total blocks: {result.total_blocks}")
        print(f"   Saved to: {output_path}")
    
    async def test_extract_file_1(self, txt_extractor, sample_files_dir, output_dir):
        """Should extract 1.txt (another Enron email)."""
        file_path = sample_files_dir / "1.txt"
        file_data = file_path.read_bytes()
        
        result = await txt_extractor.extract(
            file_data=file_data,
            filename="1.txt",
            document_id=3
        )
        
        assert result.page_count >= 1
        assert result.total_blocks > 0
        
        # Save output using production structure
        output_path = save_extraction_output(result, case_id=1, output_dir=output_dir)
        
        print(f"\n[PASS] Extracted 1.txt:")
        print(f"   Pages: {result.page_count}")
        print(f"   Total blocks: {result.total_blocks}")
        print(f"   Saved to: {output_path}")
    
    async def test_page_sizing(self, txt_extractor, sample_files_dir):
        """Pages should respect size constraints."""
        # Use a larger file
        file_path = sample_files_dir / "1.txt"
        file_data = file_path.read_bytes()
        
        result = await txt_extractor.extract(
            file_data=file_data,
            filename="1.txt",
            document_id=4
        )
        
        for page in result.pages:
            page_size = page.char_end - page.char_start
            # Pages should generally be under MAX_PAGE_SIZE
            # (allow small overage for boundary cases)
            assert page_size <= txt_extractor.MAX_PAGE_SIZE + 100, \
                f"Page {page.page_index} too large: {page_size} chars"
    
    async def test_block_detection(self, txt_extractor, sample_files_dir):
        """Should detect different block types."""
        file_path = sample_files_dir / "real_email.txt"
        file_data = file_path.read_bytes()
        
        result = await txt_extractor.extract(
            file_data=file_data,
            filename="real_email.txt",
            document_id=5
        )
        
        # Collect all block types
        block_types = set()
        for page in result.pages:
            for block in page.blocks:
                block_types.add(block.kind)
        
        # Should have at least paragraphs
        assert "paragraph" in block_types
        
        print(f"\n[INFO] Block types detected: {', '.join(sorted(block_types))}")
    
    async def test_get_all_text_method(self, txt_extractor, sample_files_dir):
        """get_all_text() should reconstruct full document text."""
        file_path = sample_files_dir / "real_email.txt"
        file_data = file_path.read_bytes()
        original_text = file_data.decode('utf-8')
        
        result = await txt_extractor.extract(
            file_data=file_data,
            filename="real_email.txt",
            document_id=6
        )
        
        # Get all text
        extracted_text = result.get_all_text()
        
        # Should have reconstructed most of the text
        # (may differ slightly due to normalization and paragraph joining)
        assert len(extracted_text) > 0
        assert len(extracted_text) >= len(original_text) * 0.8, \
            "Extracted text should preserve most of original"
    
    async def test_get_blocks_by_kind(self, txt_extractor, sample_files_dir):
        """get_blocks_by_kind() should filter blocks correctly."""
        file_path = sample_files_dir / "real_email.txt"
        file_data = file_path.read_bytes()
        
        result = await txt_extractor.extract(
            file_data=file_data,
            filename="real_email.txt",
            document_id=7
        )
        
        # Get paragraphs
        paragraphs = result.get_blocks_by_kind("paragraph")
        assert len(paragraphs) > 0
        
        # All should be paragraphs
        for block in paragraphs:
            assert block.kind == "paragraph"
    
    async def test_page_overlap(self, txt_extractor):
        """Pages should have overlap (except first page)."""
        # Create a large enough text to span multiple pages
        large_text = "This is a paragraph.\n\n" * 500  # ~10KB
        file_data = large_text.encode('utf-8')
        
        result = await txt_extractor.extract(
            file_data=file_data,
            filename="large_test.txt",
            document_id=8
        )
        
        if result.page_count > 1:
            # First page should have no overlap
            assert result.pages[0].overlap_prev_chars is None
            
            # Subsequent pages should have overlap
            for page in result.pages[1:]:
                assert page.overlap_prev_chars is not None
                assert page.overlap_prev_chars > 0
                print(f"   Page {page.page_index}: {page.overlap_prev_chars} chars overlap")
    
    async def test_char_offsets_are_absolute(self, txt_extractor, sample_files_dir):
        """Block char offsets should be absolute document positions."""
        file_path = sample_files_dir / "real_email.txt"
        file_data = file_path.read_bytes()
        original_text = file_data.decode('utf-8')
        
        # Normalize like the extractor does
        import unicodedata
        original_text = unicodedata.normalize('NFKC', original_text)
        
        result = await txt_extractor.extract(
            file_data=file_data,
            filename="real_email.txt",
            document_id=9
        )
        
        # Check that block offsets point to correct positions in original text
        for page in result.pages:
            for block in page.blocks:
                # Extract text using the offsets
                extracted_segment = original_text[block.char_start:block.char_end]
                
                # Should match block text (allowing for minor normalization differences)
                assert block.text in extracted_segment or extracted_segment in block.text, \
                    f"Block offset mismatch at {block.char_start}-{block.char_end}"
    
    async def test_token_estimates(self, txt_extractor, sample_files_dir):
        """Token estimates should be reasonable (~chars / 4)."""
        file_path = sample_files_dir / "real_email.txt"
        file_data = file_path.read_bytes()
        
        result = await txt_extractor.extract(
            file_data=file_data,
            filename="real_email.txt",
            document_id=10
        )
        
        for page in result.pages:
            page_chars = page.char_end - page.char_start
            estimated_tokens = page.token_estimate
            
            # Rough token estimate should be ~25% of char count
            # Allow range of 15-35% (some variation is expected)
            min_tokens = page_chars * 0.15
            max_tokens = page_chars * 0.35
            
            assert min_tokens <= estimated_tokens <= max_tokens, \
                f"Page {page.page_index} token estimate seems off: " \
                f"{estimated_tokens} tokens for {page_chars} chars"
    
    async def test_all_sample_files(self, txt_extractor, sample_files_dir, output_dir):
        """Should successfully extract all sample text files."""
        txt_files = list(sample_files_dir.glob("*.txt"))
        
        assert len(txt_files) > 0, "No sample TXT files found"
        
        results = {}
        
        for txt_file in txt_files:
            file_data = txt_file.read_bytes()
            
            result = await txt_extractor.extract(
                file_data=file_data,
                filename=txt_file.name,
                document_id=hash(txt_file.name) % 10000
            )
            
            results[txt_file.name] = {
                "pages": result.page_count,
                "blocks": result.total_blocks,
                "chars": result.extraction_metadata["char_count"]
            }
            
            # Save each extraction using production structure
            # All test files go to case_999 for this batch test
            save_extraction_output(result, case_id=999, output_dir=output_dir)
        
        # Print summary
        print(f"\n{'='*60}")
        print("Extraction Summary for All Files:")
        print(f"{'='*60}")
        for filename, stats in results.items():
            print(f"  {filename:20s} → {stats['pages']:2d} pages, {stats['blocks']:3d} blocks, {stats['chars']:6,d} chars")
        print(f"{'='*60}")

