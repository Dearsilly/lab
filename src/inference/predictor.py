"""Single essay prediction."""
import torch
import numpy as np

from src.inference.model_loader import load_model
from src.inference.preprocessor import preprocess


class Predictor:
    """Encapsulates model inference for a single essay."""

    def __init__(self, model, tokenizer, device, max_length: int = 512):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.max_length = max_length

    def predict(self, text: str) -> dict:
        """Predict score for a single essay."""
        text = preprocess(text)
        if not text:
            return {"score": None, "error": "Empty text after preprocessing"}

        encoded = self.tokenizer(
            text,
            max_length=self.max_length,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )

        input_ids = encoded["input_ids"].to(self.device)
        attention_mask = encoded["attention_mask"].to(self.device)

        with torch.no_grad():
            with torch.amp.autocast("cuda" if self.device == "cuda" else "cpu", enabled=self.device == "cuda"):
                score = self.model(input_ids, attention_mask)
            score = score.cpu().item()

        return {"score": round(float(score), 4), "error": None}


# Singleton
_predictor = None


def get_predictor(model_path: str = "models/best_model.pt") -> Predictor:
    """Get or create the global predictor instance."""
    global _predictor
    if _predictor is None:
        model, tokenizer, device = load_model(model_path)
        _predictor = Predictor(model, tokenizer, device)
    return _predictor
