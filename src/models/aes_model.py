"""AES Model: BERT + Regression Head."""
import torch
import torch.nn as nn
from transformers import AutoModel, AutoConfig


class AESModel(nn.Module):
    """BERT encoder + linear regression head for automated essay scoring."""

    def __init__(self, model_name: str = "bert-base-uncased", dropout: float = 0.1):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(model_name)
        hidden_size = self.encoder.config.hidden_size
        self.regressor = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(hidden_size, 1),
            nn.Sigmoid(),
        )

    def forward(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor
    ) -> torch.Tensor:
        """Forward pass. Returns scores in [0, 1]."""
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls_embedding = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        cls_embedding = cls_embedding.float()
        score = self.regressor(cls_embedding).squeeze(-1)
        return score
