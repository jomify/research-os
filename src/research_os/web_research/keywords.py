STOP_WORDS: set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "from", "by", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "can", "shall", "not",
    "no", "that", "this", "these", "those", "it", "its", "we", "you",
    "i", "me", "my", "our", "your", "he", "she", "they", "them", "find",
    "recent", "papers", "paper", "search", "please", "show", "give",
    "get", "look", "looking", "need", "want", "like", "using", "use",
}


def extract_keywords(prompt: str, domain_hints: list[str] | None = None) -> list[str]:
    """Extract meaningful search keywords from a natural language prompt."""
    cleaned = prompt.lower()
    for ch in ",.!?;:'\"()[]{}":
        cleaned = cleaned.replace(ch, " ")

    words = cleaned.split()
    keywords: list[str] = []
    for w in words:
        w = w.strip("-")
        if not w or len(w) <= 2:
            continue
        if w in STOP_WORDS:
            continue
        keywords.append(w)

    if not keywords:
        keywords = ["machine", "learning"]

    return keywords
