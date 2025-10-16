"""
Test PDF extractor with Tesseract OCR fallback.

Simple test to examine one PDF at a time.
"""
import pytest
import json
from pathlib import Path
from services.text_extraction.pdf_extractor import PDFExtractor


@pytest.fixture
def pdf_extractor():
    """Create PDFExtractor instance."""
    return PDFExtractor()


@pytest.fixture
def sample_files_dir():
    """Path to sample PDF files."""
    return Path(__file__).parent.parent / "helpers" / "sample_files" / "pdf"


@pytest.fixture
def output_dir():
    """Path to output directory for extracted JSON."""
    output = Path(__file__).parent.parent / "file_output"
    output.mkdir(exist_ok=True)
    return output


def save_extraction_output(result, case_id: str, output_dir: Path):
    """Save extraction to case/document folder structure."""
    doc_id = result.document_id
    
    # Create directory: cases/case_X/documents/doc_Y/extraction/
    extraction_dir = output_dir / "cases" / case_id / "documents" / f"doc_{doc_id}" / "extraction"
    extraction_dir.mkdir(parents=True, exist_ok=True)
    
    # Save blocks.json
    blocks_path = extraction_dir / "blocks.json"
    with open(blocks_path, 'w', encoding='utf-8') as f:
        json.dump(result.model_dump(), f, indent=2, ensure_ascii=False)
    
    return blocks_path


@pytest.mark.asyncio
async def test_extract_pdf():
    """Extract a single PDF and examine the results.
    
    Change the filename below to test different PDFs from the samples folder.
    """
    # CHANGE THIS to test different PDFs
    test_filename = "EXH005-02542.PDF"
    # Other options: enron1992.pdf, enron1993.pdf, enron1994.pdf, EXH005-02542.PDF, etc.
    
    # Check both pdf and ocr folders
    sample_dir_ocr = Path(__file__).parent.parent / "helpers" / "sample_files" / "ocr"
    sample_dir_pdf = Path(__file__).parent.parent / "helpers" / "sample_files" / "pdf"
    output_dir = Path(__file__).parent.parent / "file_output"
    
    # Try OCR folder first, then PDF folder
    file_path = sample_dir_ocr / test_filename
    if not file_path.exists():
        file_path = sample_dir_pdf / test_filename
    
    if not file_path.exists():
        print(f"File not found: {test_filename}")
        print(f"Available OCR PDFs: {list(sample_dir_ocr.glob('*.PDF'))}")
        print(f"Available PDF files: {list(sample_dir_pdf.glob('*.pdf'))}")
        pytest.skip(f"Test file not found: {test_filename}")
    
    print(f"\n{'='*70}")
    print(f"Testing: {test_filename}")
    print(f"{'='*70}")
    
    # Read file
    file_data = file_path.read_bytes()
    file_size_mb = len(file_data) / (1024 * 1024)
    print(f"File size: {file_size_mb:.2f} MB")
    
    # Extract
    pdf_extractor = PDFExtractor()
    
    result = await pdf_extractor.extract(
        file_data=file_data,
        filename=test_filename,
        document_id=1001
    )
    
    # Save output
    output_path = save_extraction_output(result, "case_pdf_1", output_dir)
    
    # Print summary
    print(f"\n[EXTRACTION COMPLETE]")
    print(f"  Pages: {result.page_count}")
    print(f"  Total blocks: {result.total_blocks}")
    print(f"  Pages with OCR: {sum(1 for p in result.pages if p.needs_ocr)}")
    print(f"  Pages with text: {sum(1 for p in result.pages if p.has_text_layer)}")
    print(f"  Total images: {sum(p.image_count or 0 for p in result.pages)}")
    print(f"\n  Saved to: {output_path}")
    
    # Show first 3 pages in detail
    print(f"\n{'='*70}")
    print("First 3 Pages Detail:")
    print(f"{'='*70}")
    
    for page in result.pages[:3]:
        print(f"\nPage {page.page_index}:")
        print(f"  Size: {page.width:.0f}x{page.height:.0f} pts, Rotation: {page.rotation}°")
        print(f"  Char count: {page.char_count}")
        print(f"  Has text layer: {page.has_text_layer}")
        print(f"  Needs OCR: {page.needs_ocr}")
        print(f"  Page kind: {page.page_kind}")
        print(f"  Blocks: {page.block_count}, Images: {page.image_count}")
        
        # Show first 2 blocks
        for i, block in enumerate(page.blocks[:2]):
            text_preview = block.text[:80].replace('\n', ' ')
            if len(block.text) > 80:
                text_preview += "..."
            print(f"    Block {i} ({block.kind}): {text_preview}")
    
    if result.page_count > 3:
        print(f"\n... and {result.page_count - 3} more pages")
    
    print(f"\n{'='*70}")
    print("Review the blocks.json file to see full extraction results")
    print(f"{'='*70}")

