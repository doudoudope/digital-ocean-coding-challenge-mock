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


def test_keywords_strips_punctuation():
    result = process("python, api. database!")
    keywords = json.loads(result["keywords"])
    assert "python" in keywords
    assert "api" in keywords
    assert "database" in keywords


def test_keywords_excludes_short_words():
    # Words with 2 or fewer chars are filtered out
    result = process("is it go do up at")
    keywords = json.loads(result["keywords"])
    assert "is" not in keywords
    assert "it" not in keywords
    assert "go" not in keywords


def test_keywords_capped_at_ten():
    # Generate 15 unique words, each appearing once
    words = " ".join(f"word{i}word" for i in range(15))
    result = process(words)
    keywords = json.loads(result["keywords"])
    assert len(keywords) <= 10


def test_keywords_case_insensitive():
    result = process("Python PYTHON python")
    keywords = json.loads(result["keywords"])
    assert "python" in keywords
    assert "Python" not in keywords
    assert "PYTHON" not in keywords
