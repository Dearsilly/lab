"""Text preprocessing for inference."""
import re
import html


def preprocess(text: str) -> str:
    """Preprocess input text for inference."""
    if not isinstance(text, str):
        return ""
    text = html.unescape(text)
    text = re.sub(r"@\w+", " ", text)
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
