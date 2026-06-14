"""中文 BERT 评分模型训练器。"""
import os
import sys
import argparse
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, get_linear_schedule_with_warmup
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from src.models.advanced_model import CNScoringModel
from src.evaluation.metrics import quadratic_weighted_kappa, mean_absolute_error


class CNAESDataset(Dataset):
    """中文作文评分数据集。"""

    def __init__(self, texts, scores, tokenizer, max_length=512):
        self.texts = list(texts)
        self.scores = list(scores)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx] if isinstance(self.texts[idx], str) else ""
        encoded = self.tokenizer(
            text, max_length=self.max_length, truncation=True,
            padding="max_length", return_tensors="pt",
        )
        return {
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "score": torch.tensor(self.scores[idx], dtype=torch.float32),
        }


def normalize_per_set(df: pd.DataFrame) -> pd.DataFrame:
    """按 essay_set 分别归一化到 [0, 1]。"""
    df = df.copy()
    df["score_norm"] = 0.0
    for es in sorted(df["essay_set"].unique()):
        mask = df["essay_set"] == es
        scores = df.loc[mask, "score"]
        s_min, s_max = scores.min(), scores.max()
        if s_max > s_min:
            df.loc[mask, "score_norm"] = (scores - s_min) / (s_max - s_min)
        else:
            df.loc[mask, "score_norm"] = 0.5
    return df


def split_random(df: pd.DataFrame, test_size=0.2, val_size=0.1, seed=42):
    """随机样本划分（翻译数据来自同一源，prompt 隔离意义有限）。"""
    from sklearn.model_selection import train_test_split
    train_df, test_df = train_test_split(df, test_size=test_size, random_state=seed)
    val_ratio = val_size / (1 - test_size)
    train_df, val_df = train_test_split(train_df, test_size=val_ratio, random_state=seed)
    return train_df, val_df, test_df


def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # 加载翻译后的中文数据
    df = pd.read_csv(args.data_path)
    print(f"Chinese data: {len(df)} essays, {df['essay_set'].nunique()} sets")

    # 按 essay_set 归一化（和英文模型一致）
    df = normalize_per_set(df)
    print(f"Score norm range: [{df['score_norm'].min():.2f}, {df['score_norm'].max():.2f}]")

    # 随机划分（翻译数据同源，无需 prompt 隔离）
    train_df, val_df, test_df = split_random(
        df, test_size=args.test_size, val_size=args.val_size
    )

    train_texts = train_df["essay_text"].tolist()
    train_scores = train_df["score_norm"].tolist()
    val_texts = val_df["essay_text"].tolist()
    val_scores = val_df["score_norm"].tolist()
    test_texts = test_df["essay_text"].tolist()
    test_scores = test_df["score_norm"].tolist()
    print(f"Split: train={len(train_texts)}, val={len(val_texts)}, test={len(test_texts)}")

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    train_ds = CNAESDataset(train_texts, train_scores, tokenizer, args.max_length)
    val_ds = CNAESDataset(val_texts, val_scores, tokenizer, args.max_length)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size * 2, shuffle=False)

    # 模型
    model = CNScoringModel(model_name=args.model_name, num_heads=1).to(device)

    # 优化器
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = len(train_loader) * args.epochs
    warmup_steps = int(total_steps * 0.1)
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )
    criterion = torch.nn.MSELoss()

    # 训练
    best_qwk = -1.0
    patience_counter = 0
    os.makedirs(args.output_dir, exist_ok=True)

    use_amp = device == "cuda"
    amp_device = "cuda" if use_amp else "cpu"

    for epoch in range(args.epochs):
        model.train()
        train_loss = 0.0
        for batch in tqdm(train_loader, desc=f"Epoch {epoch + 1}/{args.epochs}"):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            scores = batch["score"].to(device)

            with torch.amp.autocast(amp_device, enabled=use_amp):
                preds = model(input_ids, attention_mask).squeeze(-1)
                loss = criterion(preds, scores)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            scheduler.step()
            train_loss += loss.item()

        avg_train_loss = train_loss / len(train_loader)

        # 验证
        model.eval()
        val_preds_list, val_labels_list = [], []
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                scores = batch["score"].to(device)
                with torch.amp.autocast(amp_device, enabled=use_amp):
                    preds = model(input_ids, attention_mask).squeeze(-1)
                val_preds_list.extend(preds.cpu().numpy())
                val_labels_list.extend(scores.cpu().numpy())

        val_preds_arr = np.array(val_preds_list)
        val_labels_arr = np.array(val_labels_list)
        qwk = quadratic_weighted_kappa(val_labels_arr, val_preds_arr)
        mae = mean_absolute_error(val_labels_arr, val_preds_arr)

        print(
            f"Epoch {epoch + 1}: loss={avg_train_loss:.4f}, "
            f"qwk={qwk:.4f}, mae={mae:.4f}"
        )

        if qwk > best_qwk:
            best_qwk = qwk
            patience_counter = 0
            torch.save({
                "model_state_dict": model.state_dict(),
                "tokenizer_name": args.model_name,
                "qwk": qwk,
                "mae": mae,
                "model_type": "bert-chinese",
            }, os.path.join(args.output_dir, "best_model.pt"))
            print(f"  => Saved (QWK={qwk:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"Early stop at epoch {epoch + 1}")
                break

    print(f"\nDone. Best QWK: {best_qwk:.4f} -> {args.output_dir}/best_model.pt")

    # 测试
    test_ds = CNAESDataset(test_texts, test_scores, tokenizer, args.max_length)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size * 2, shuffle=False)

    checkpoint = torch.load(
        os.path.join(args.output_dir, "best_model.pt"), map_location=device, weights_only=False
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    test_preds, test_labels_list = [], []
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            scores = batch["score"].to(device)
            with torch.amp.autocast(amp_device, enabled=use_amp):
                preds = model(input_ids, attention_mask).squeeze(-1)
            test_preds.extend(preds.cpu().numpy())
            test_labels_list.extend(scores.cpu().numpy())

    test_qwk = quadratic_weighted_kappa(np.array(test_labels_list), np.array(test_preds))
    test_mae = mean_absolute_error(np.array(test_labels_list), np.array(test_preds))
    print(f"Test — QWK: {test_qwk:.4f}, MAE: {test_mae:.4f}")


def main():
    parser = argparse.ArgumentParser(description="Train Chinese BERT AES model")
    parser.add_argument("--data_path", default="data/raw/chinese/asap_zh.csv")
    parser.add_argument("--model_name", default="bert-base-chinese")
    parser.add_argument("--output_dir", default="models/zh_bert")
    parser.add_argument("--max_length", type=int, default=512)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--test_size", type=float, default=0.15)
    parser.add_argument("--val_size", type=float, default=0.15)
    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
