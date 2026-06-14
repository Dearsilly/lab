"""DeBERTa-v3 多任务训练器：英文作文评分模型升级训练。"""
import os
import sys
import argparse
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, get_linear_schedule_with_warmup
from tqdm import tqdm

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from src.data_preprocessing.loader import load_asap_csv, normalize_scores
from src.data_preprocessing.cleaner import clean_text
from src.data_preprocessing.splitter import split_by_prompt
from src.models.advanced_model import AESMultiTaskModel
from src.evaluation.metrics import quadratic_weighted_kappa, mean_absolute_error


class MultiTaskDataset(Dataset):
    """多任务数据集：文本 + 总分 + 伪维度标签。"""

    def __init__(self, texts, scores_norm, tokenizer, max_length=512):
        self.texts = list(texts)
        self.scores_norm = list(scores_norm)
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

        total = self.scores_norm[idx]
        # 所有维度先学习总评分（训练稳定后会自动分化）
        targets = torch.full((4,), total, dtype=torch.float32)

        return {
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "targets": targets,
        }


def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # 数据
    df = load_asap_csv()
    df["essay_text"] = df["essay_text"].apply(clean_text)
    df = normalize_scores(df)
    train_df, val_df, test_df = split_by_prompt(
        df, test_size=args.test_size, val_size=args.val_size
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    train_ds = MultiTaskDataset(
        train_df["essay_text"], train_df["score_normalized"], tokenizer, args.max_length
    )
    val_ds = MultiTaskDataset(
        val_df["essay_text"], val_df["score_normalized"], tokenizer, args.max_length
    )

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size * 2, shuffle=False)

    # 模型
    model = AESMultiTaskModel(
        model_name=args.model_name, num_heads=4, dropout=args.dropout
    ).to(device)

    # 优化器
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = len(train_loader) * args.epochs
    warmup_steps = int(total_steps * 0.1)
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )

    # 加权损失：总评分权重更高
    head_weights = torch.tensor([1.0, 0.5, 0.5, 0.5], device=device)
    criterion = torch.nn.MSELoss(reduction="none")

    # 训练循环
    best_qwk = -1.0
    patience_counter = 0
    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    use_amp = device == "cuda"
    amp_device = "cuda" if use_amp else "cpu"

    for epoch in range(args.epochs):
        model.train()
        train_loss = 0.0
        for batch in tqdm(train_loader, desc=f"Epoch {epoch + 1}/{args.epochs}"):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            targets = batch["targets"].to(device)

            with torch.amp.autocast(amp_device, enabled=use_amp):
                preds = model(input_ids, attention_mask)
                loss_per_head = criterion(preds, targets)
                loss = (loss_per_head * head_weights).mean()

            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()
            train_loss += loss.item()

        avg_train_loss = train_loss / len(train_loader)

        # 验证
        model.eval()
        val_total_preds, val_total_labels = [], []
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                targets = batch["targets"].to(device)
                with torch.amp.autocast(amp_device, enabled=use_amp):
                    preds = model(input_ids, attention_mask)
                val_total_preds.extend(preds[:, 0].cpu().numpy())
                val_total_labels.extend(targets[:, 0].cpu().numpy())

        val_preds_arr = np.array(val_total_preds)
        val_labels_arr = np.array(val_total_labels)
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
                "model_type": "deberta-v3-multitask",
            }, os.path.join(output_dir, "best_model.pt"))
            print(f"  => Saved (QWK={qwk:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"Early stop at epoch {epoch + 1}")
                break

    print(f"\nDone. Best QWK: {best_qwk:.4f} -> {output_dir}/best_model.pt")

    # 测试集评估
    test_ds = MultiTaskDataset(
        test_df["essay_text"], test_df["score_normalized"], tokenizer, args.max_length
    )
    test_loader = DataLoader(test_ds, batch_size=args.batch_size * 2, shuffle=False)

    checkpoint = torch.load(
        os.path.join(output_dir, "best_model.pt"), map_location=device, weights_only=False
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    test_preds, test_labels = [], []
    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            targets = batch["targets"].to(device)
            with torch.amp.autocast(amp_device, enabled=use_amp):
                preds = model(input_ids, attention_mask)
            test_preds.extend(preds[:, 0].cpu().numpy())
            test_labels.extend(targets[:, 0].cpu().numpy())

    test_qwk = quadratic_weighted_kappa(np.array(test_labels), np.array(test_preds))
    test_mae = mean_absolute_error(np.array(test_labels), np.array(test_preds))
    print(f"Test set — QWK: {test_qwk:.4f}, MAE: {test_mae:.4f}")


def main():
    parser = argparse.ArgumentParser(description="Train DeBERTa-v3 AES model")
    parser.add_argument("--model_name", default="microsoft/deberta-v3-base")
    parser.add_argument("--output_dir", default="models/en_deberta")
    parser.add_argument("--max_length", type=int, default=512)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--lr", type=float, default=1e-5)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--test_size", type=float, default=0.15)
    parser.add_argument("--val_size", type=float, default=0.15)
    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
