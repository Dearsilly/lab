"""进阶多任务 AES 模型：DeBERTa-v3 编码器 + 4 个回归头。"""
import torch
import torch.nn as nn
from transformers import AutoModel


class AESMultiTaskModel(nn.Module):
    """DeBERTa-v3 编码器 + 4 维回归头（总分/内容/结构/语言）。

    所有头共享编码器，额外显存开销 < 1MB。
    输出 shape: (batch, 4)，列顺序: [total, content, structure, language]
    """

    HEAD_NAMES = ["total", "content", "structure", "language"]

    def __init__(
        self,
        model_name: str = "microsoft/deberta-v3-base",
        num_heads: int = 4,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.model_name = model_name
        self.encoder = AutoModel.from_pretrained(model_name)
        hidden_size = self.encoder.config.hidden_size

        self.heads = nn.ModuleList([
            nn.Sequential(
                nn.Dropout(dropout),
                nn.Linear(hidden_size, 1),
                nn.Sigmoid(),
            )
            for _ in range(num_heads)
        ])

    def forward(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor
    ) -> torch.Tensor:
        """返回 (batch, 4) 的分数张量，范围 [0, 1]。"""
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        # 转回 fp32 避免 autocast 下 Linear 层 dtype 不匹配
        pooled = pooled.float()
        scores = [head(pooled) for head in self.heads]
        return torch.cat(scores, dim=-1)


class CNScoringModel(nn.Module):
    """中文评分模型：BERT-base-chinese + 可选多任务头。"""

    def __init__(
        self,
        model_name: str = "bert-base-chinese",
        num_heads: int = 1,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.model_name = model_name
        self.encoder = AutoModel.from_pretrained(model_name)
        hidden_size = self.encoder.config.hidden_size

        self.heads = nn.ModuleList([
            nn.Sequential(
                nn.Dropout(dropout),
                nn.Linear(hidden_size, 1),
                nn.Sigmoid(),
            )
            for _ in range(num_heads)
        ])

    def forward(
        self, input_ids: torch.Tensor, attention_mask: torch.Tensor
    ) -> torch.Tensor:
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled = outputs.last_hidden_state[:, 0, :]
        pooled = pooled.float()
        scores = [head(pooled) for head in self.heads]
        return torch.cat(scores, dim=-1)
