"""Text cleaning utilities."""
import re
import html


def clean_text(text: str) -> str:
    """Basic text cleaning for ASAP essays."""
    if not isinstance(text, str):
        return ""
    text = html.unescape(text)
    text = re.sub(r"@\w+", " ", text)        # Remove @mentions
    text = re.sub(r"http\S+", " ", text)      # Remove URLs
    text = re.sub(r"\s+", " ", text)          # Collapse whitespace
    return text.strip()
