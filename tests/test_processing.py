import json

from app.services.processing_service import process


def test_word_count():
    result = process("one two three")
    assert result["word_count"] == 3


def test_line_count_single_line():
    result = process("one two three")
    assert result["line_count"] == 1


def test_line_count_multiple_lines():
    result = process("line one\nline two\nline three")
    assert result["line_count"] == 3


def test_word_count_multiline():
    result = process("hello world\nfoo bar")
    assert result["word_count"] == 4


def test_keywords_is_list():
    result = process("python api database python api python")
    keywords = json.loads(result["keywords"])
    assert isinstance(keywords, list)


def test_keywords_most_frequent_first():
    result = process("python python python api api database")
    keywords = json.loads(result["keywords"])
    assert keywords[0] == "python"
    assert keywords[1] == "api"


def test_keywords_excludes_stopwords():
    result = process("the and is a python")
    keywords = json.loads(result["keywords"])
    assert "the" not in keywords
    assert "and" not in keywords
    assert "is" not in keywords


def test_keywords_non_empty_for_real_content():
    content = "FastAPI SQLAlchemy database python service document"
    result = process(content)
    keywords = json.loads(result["keywords"])
    assert len(keywords) > 0


def test_summary_is_placeholder():
    result = process("any content here")
    assert result["summary"] == "placeholder"


def test_empty_content():
    result = process("")
    assert result["word_count"] == 0
    assert result["line_count"] == 0
    assert result["summary"] == "placeholder"
