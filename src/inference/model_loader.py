"""Model loading and inference utilities."""
import torch
from pathlib import Path
from typing import Optional
from transformers import AutoTokenizer

from src.models.aes_model import AESModel
from src.models.advanced_model import CNScoringModel


def load_model(
    model_path: str = "models/best_model.pt",
    device: str = None,
    model_name: Optional[str] = None,
    model_class: type = AESModel,
):
    """Load trained AES model and tokenizer.

    Args:
        model_path: Path to saved checkpoint.
        device: "cuda" | "cpu". Auto-detected if None.
        model_name: Override tokenizer/model name from checkpoint.
        model_class: Model class to instantiate (AESModel or CNScoringModel).
    """
    if device is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    checkpoint = torch.load(model_path, map_location=device, weights_only=False)
    if model_name is None:
        model_name = checkpoint.get("tokenizer_name", "bert-base-uncased")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = model_class(model_name=model_name)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    qwk_val = checkpoint.get("qwk")
    if isinstance(qwk_val, float):
        print(f"Model loaded from {model_path} (QWK={qwk_val:.4f})")
    else:
        print(f"Model loaded from {model_path}")
    return model, tokenizer, device
