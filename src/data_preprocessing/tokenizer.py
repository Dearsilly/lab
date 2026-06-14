"""BERT tokenizer wrapper."""
from transformers import AutoTokenizer


def create_tokenizer(model_name: str = "bert-base-uncased") -> AutoTokenizer:
    """Create and return a HuggingFace tokenizer."""
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return tokenizer


def tokenize_texts(tokenizer, texts: list[str], max_length: int = 512):
    """Tokenize a list of texts. Returns BatchEncoding with input_ids, attention_mask."""
    return tokenizer(
        texts,
        max_length=max_length,
        truncation=True,
        padding="max_length",
        return_tensors="pt",
    )


def get_input_ids(encoded) -> "torch.Tensor":
    """Extract input_ids tensor from BatchEncoding."""
    return encoded["input_ids"]


def get_attention_mask(encoded) -> "torch.Tensor":
    """Extract attention_mask tensor from BatchEncoding."""
    return encoded["attention_mask"]
