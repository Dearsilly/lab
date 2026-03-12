import torch.nn as nn
from transformers import AutoModel

class BertForEssayScoring(nn.Module):
    def __init__(self, model_name: str, dropout: float = 0.3):
        super().__init__()
        self.bert = AutoModel.from_pretrained(model_name)
        hidden_size = self.bert.config.hidden_size

        self.dropout = nn.Dropout(dropout)
        self.regressor = nn.Linear(hidden_size, 1)

    def forward(self, input_ids, attention_mask, token_type_ids=None):
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids if token_type_ids is not None else None
        )

        cls_output = outputs.last_hidden_state[:, 0, :]
        score = self.regressor(self.dropout(cls_output))
        return score.squeeze(-1)