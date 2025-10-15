"""Sample file data for testing file type detection.

These are realistic file headers/samples that mimic real file types.
"""


class FileSamples:
    """Provides sample file bytes for different file types."""
    
    @staticmethod
    def pdf() -> bytes:
        """Sample PDF file header."""
        return b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n' + b'Some PDF content here' * 100
    
    @staticmethod
    def docx() -> bytes:
        """Sample DOCX file header (ZIP format with proper structure)."""
        # DOCX files are ZIP archives - need more complete ZIP structure for python-magic
        # This is a minimal valid ZIP file structure
        return (
            b'PK\x03\x04\x14\x00\x00\x00\x08\x00'  # ZIP local file header
            b'\x00\x00\x00\x00\x00\x00\x00\x00'  # CRC, compressed size
            b'\x00\x00\x00\x00\x00\x00\x00\x00'  # Uncompressed size
            b'\x13\x00\x00\x00'  # Filename length
            b'[Content_Types].xml'  # Filename (DOCX identifier)
            + b'\x00' * 8000  # Padding to look like real file
        )
    
    @staticmethod
    def doc() -> bytes:
        """Sample DOC file header (old Word format)."""
        # Old Word documents have this signature (OLE compound file)
        # Need more complete header for python-magic to detect
        return (
            b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'  # OLE signature
            b'\x00\x00\x00\x00\x00\x00\x00\x00'  # CLSID
            b'\x00\x00\x00\x00\x00\x00\x00\x00'
            b'\x3e\x00\x03\x00\xfe\xff\x09\x00'  # Minor version, DLL version
            + b'\x00' * 8000  # Padding to look like real file
        )
    
    @staticmethod
    def txt() -> bytes:
        """Sample plain text file."""
        return b'This is a plain text file.\nWith multiple lines.\nAnd some content.'
    
    @staticmethod
    def html() -> bytes:
        """Sample HTML file."""
        return b'''<!DOCTYPE html>
<html>
<head>
    <title>Test Document</title>
</head>
<body>
    <h1>This is a test</h1>
    <p>Some HTML content here.</p>
</body>
</html>'''
    
    @staticmethod
    def email_rfc822() -> bytes:
        """Sample email file (RFC 822 format - like Enron emails)."""
        return b'''From: john.doe@enron.com
To: jane.smith@enron.com
Subject: Q3 Financial Results
Date: Mon, 15 Oct 2001 10:30:00 -0500

<html>
<body>
<p>Please review the attached Q3 results.</p>
</body>
</html>'''
    
    @staticmethod
    def unknown_binary() -> bytes:
        """Sample unknown binary file."""
        # Random binary data that doesn't match any known format
        return b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a' + b'\xff\xd8\xff\xe0' + b'\x00' * 200
    
    @staticmethod
    def xml() -> bytes:
        """Sample XML file."""
        return b'''<?xml version="1.0" encoding="UTF-8"?>
<document>
    <title>Test XML</title>
    <content>Some XML content</content>
</document>'''
    
    @staticmethod
    def csv() -> bytes:
        """Sample CSV file."""
        return b'''Name,Age,City
John,30,New York
Jane,25,Los Angeles
Bob,35,Chicago'''
    
    @staticmethod
    def markdown() -> bytes:
        """Sample Markdown file."""
        return b'''# Test Document

## Section 1

This is some markdown content.

- Item 1
- Item 2
- Item 3'''

