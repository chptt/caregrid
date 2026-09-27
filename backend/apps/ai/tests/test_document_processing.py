import pytest
import tempfile
import os
from pathlib import Path


class TestValidateFile:
    def test_valid_txt(self):
        from backend.apps.ai.document_processing.extractor import validate_file
        validate_file('test.txt', 1000)

    def test_valid_pdf(self):
        from backend.apps.ai.document_processing.extractor import validate_file
        validate_file('document.pdf', 5000)

    def test_valid_docx(self):
        from backend.apps.ai.document_processing.extractor import validate_file
        validate_file('record.docx', 2000)

    def test_invalid_extension(self):
        from backend.apps.ai.document_processing.extractor import validate_file, ALLOWED_EXTENSIONS
        with pytest.raises(ValueError, match='Unsupported file type'):
            validate_file('malware.exe', 100)

    def test_invalid_no_extension(self):
        from backend.apps.ai.document_processing.extractor import validate_file
        with pytest.raises(ValueError, match='Unsupported file type'):
            validate_file('Makefile', 100)

    def test_file_too_large(self):
        from backend.apps.ai.document_processing.extractor import validate_file, MAX_FILE_SIZE
        with pytest.raises(ValueError, match='File too large'):
            validate_file('big.pdf', MAX_FILE_SIZE + 1)

    def test_exact_max_size(self):
        from backend.apps.ai.document_processing.extractor import validate_file, MAX_FILE_SIZE
        validate_file('exact.txt', MAX_FILE_SIZE)


class TestExtractTxt:
    def test_extract_simple_text(self):
        from backend.apps.ai.document_processing.extractor import extract_txt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write('Hello, World!')
            fpath = f.name
        try:
            result = extract_txt(fpath)
            assert result == 'Hello, World!'
        finally:
            os.unlink(fpath)

    def test_extract_multiline(self):
        from backend.apps.ai.document_processing.extractor import extract_txt
        content = 'Line 1\nLine 2\nLine 3'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            fpath = f.name
        try:
            result = extract_txt(fpath)
            assert result == content
        finally:
            os.unlink(fpath)

    def test_extract_empty_file(self):
        from backend.apps.ai.document_processing.extractor import extract_txt
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            fpath = f.name
        try:
            result = extract_txt(fpath)
            assert result == ''
        finally:
            os.unlink(fpath)


class TestExtractDispatch:
    def test_extract_txt_dispatch(self):
        from backend.apps.ai.document_processing.extractor import extract
        content = 'Text content'
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            f.write(content)
            fpath = f.name
        try:
            result = extract(fpath, 'txt')
            assert result == content
        finally:
            os.unlink(fpath)

    def test_extract_unknown_type(self):
        from backend.apps.ai.document_processing.extractor import extract
        with pytest.raises(ValueError, match='No extractor'):
            extract('file.xyz', 'xyz')

    def test_extract_missing_file(self):
        from backend.apps.ai.document_processing.extractor import extract
        with pytest.raises(FileNotFoundError):
            extract('/nonexistent/file.txt', 'txt')


class TestSanitize:
    def test_remove_html_tags(self):
        from backend.apps.ai.document_processing.cleaner import sanitize
        result = sanitize('<p>Hello</p>')
        assert result == 'Hello'

    def test_remove_nested_tags(self):
        from backend.apps.ai.document_processing.cleaner import sanitize
        result = sanitize('<div><span>deep</span></div>')
        assert result == 'deep'

    def test_remove_script_tags(self):
        from backend.apps.ai.document_processing.cleaner import sanitize
        result = sanitize('before<script>alert("xss")</script>after')
        assert result == 'beforeafter'

    def test_remove_script_with_attrs(self):
        from backend.apps.ai.document_processing.cleaner import sanitize
        result = sanitize('x<script type="text/javascript">evil()</script>y')
        assert result == 'xy'

    def test_strip_whitespace(self):
        from backend.apps.ai.document_processing.cleaner import sanitize
        result = sanitize('  Hello World  ')
        assert result == 'Hello World'

    def test_remove_control_chars(self):
        from backend.apps.ai.document_processing.cleaner import sanitize
        result = sanitize('Hello\x00World\x1f!')
        assert result == 'HelloWorld!'

    def test_no_html(self):
        from backend.apps.ai.document_processing.cleaner import sanitize
        result = sanitize('Plain text')
        assert result == 'Plain text'

    def test_empty_string(self):
        from backend.apps.ai.document_processing.cleaner import sanitize
        result = sanitize('')
        assert result == ''


class TestTextChunker:
    def test_single_chunk_small_text(self):
        from backend.apps.ai.document_processing.chunker import TextChunker
        chunker = TextChunker(chunk_size=1000, overlap=200)
        text = 'Short text.'
        chunks = chunker.chunk(text)
        assert len(chunks) == 1
        assert chunks[0].text == 'Short text.'
        assert chunks[0].index == 0
        assert chunks[0].start_char == 0
        assert chunks[0].end_char == len(text)

    def test_multiple_chunks_no_overlap_point(self):
        from backend.apps.ai.document_processing.chunker import TextChunker
        chunker = TextChunker(chunk_size=20, overlap=5)
        text = 'a' * 50
        chunks = chunker.chunk(text)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c.text) <= 20

    def test_chunk_overlap(self):
        from backend.apps.ai.document_processing.chunker import TextChunker
        chunker = TextChunker(chunk_size=30, overlap=10)
        text = 'a' * 100
        chunks = chunker.chunk(text)
        assert len(chunks) > 1
        for i in range(1, len(chunks)):
            assert chunks[i].start_char < chunks[i - 1].end_char

    def test_chunk_indices_sequential(self):
        from backend.apps.ai.document_processing.chunker import TextChunker
        chunker = TextChunker(chunk_size=10, overlap=2)
        text = 'x' * 35
        chunks = chunker.chunk(text)
        for i, c in enumerate(chunks):
            assert c.index == i

    def test_chunk_respects_period_boundary(self):
        from backend.apps.ai.document_processing.chunker import TextChunker
        chunker = TextChunker(chunk_size=100, overlap=20)
        text = 'First sentence. Second sentence. ' + ('x' * 200)
        chunks = chunker.chunk(text)
        assert chunks[0].text.rstrip().endswith('Second sentence.')

    def test_empty_text(self):
        from backend.apps.ai.document_processing.chunker import TextChunker
        chunker = TextChunker()
        chunks = chunker.chunk('')
        assert len(chunks) == 1
        assert chunks[0].text == ''

    def test_custom_chunk_size(self):
        from backend.apps.ai.document_processing.chunker import TextChunker
        chunker = TextChunker(chunk_size=5, overlap=1)
        text = 'hello world'
        chunks = chunker.chunk(text)
        assert len(chunks) > 1
