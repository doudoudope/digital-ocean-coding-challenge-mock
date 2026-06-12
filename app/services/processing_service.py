import json
import re
from collections import Counter

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "it", "this", "that", "was", "are", "be", "as",
    "by", "from", "not", "have", "has", "had", "he", "she", "they", "we",
    "you", "i", "its", "into", "than", "then", "so", "if", "about", "up",
    "out", "no", "can", "will", "do", "did", "my", "your", "their", "our",
}

TOP_KEYWORDS = 10


def process(content: str) -> dict:
    words = content.split()
    lines = content.splitlines()

    tokens = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in words]
    tokens = [t for t in tokens if len(t) > 2 and t not in _STOPWORDS]

    counts = Counter(tokens)
    keywords = [word for word, _ in counts.most_common(TOP_KEYWORDS)]

    return {
        "word_count": len(words),
        "line_count": len(lines),
        "keywords": json.dumps(keywords),
        "summary": "placeholder",
    }
