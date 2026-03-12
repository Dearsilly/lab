import torch
from torch.utils.data import Dataset

SCORE_RANGES = {
    1: (2, 12),
    2: (1, 6),
    3: (0, 3),
    4: (0, 3),
    5: (0, 4),
    6: (0, 4),
    7: (0, 30),
    8: (0, 60),
}


def normalize_score(essay_set: int, score: float) -> float:
    min_s, max_s = SCORE_RANGES[essay_set]
    return (score - min_s) / (max_s - min_s)


def denormalize_score(essay_set: int, score: float) -> float:
    min_s, max_s = SCORE_RANGES[essay_set]
    return score * (max_s - min_s) + min_s


class EssayDataset(Dataset):
    def __init__(self, df, tokenizer, max_len=512):
        self.df = df.reset_index(drop=True)
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]

        essay_set = int(row["essay_set"])
        essay = str(row["essay"])
        score = float(row["domain1_score"])

        # 输入保留 set 信息
        text = f"[SET_{essay_set}] {essay}"

        # 标签做归一化
        norm_score = normalize_score(essay_set, score)

        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_len,
            return_tensors="pt"
        )

        item = {
            "essay_set": torch.tensor(essay_set, dtype=torch.long),
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(norm_score, dtype=torch.float),
        }

        if "token_type_ids" in encoding:
            item["token_type_ids"] = encoding["token_type_ids"].squeeze(0)

        return item