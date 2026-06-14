"""Training entry point for AES model."""
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
from src.data_preprocessing.tokenizer import create_tokenizer
from src.data_preprocessing.splitter import split_by_prompt
from src.models.aes_model import AESModel
from src.evaluation.metrics import quadratic_weighted_kappa, mean_absolute_error, pearson_correlation


class AESDataset(Dataset):
    def __init__(self, texts, scores, tokenizer, max_length=512):
        self.texts = list(texts)
        self.scores = list(scores)
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        if not isinstance(text, str):
            text = ""
        encoded = self.tokenizer(
            text,
            max_length=self.max_length,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )
        return {
            "input_ids": encoded["input_ids"].squeeze(0),
            "attention_mask": encoded["attention_mask"].squeeze(0),
            "score": torch.tensor(self.scores[idx], dtype=torch.float32),
        }


def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load and preprocess data
    df = load_asap_csv()
    df["essay_text"] = df["essay_text"].apply(clean_text)
    df = normalize_scores(df)
    train_df, val_df, test_df = split_by_prompt(
        df, test_size=args.test_size, val_size=args.val_size
    )

    tokenizer = create_tokenizer(args.model_name)
    train_ds = AESDataset(
        train_df["essay_text"], train_df["score_normalized"], tokenizer, args.max_length
    )
    val_ds = AESDataset(
        val_df["essay_text"], val_df["score_normalized"], tokenizer, args.max_length
    )

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size * 2, shuffle=False)

    # Model
    model = AESModel(model_name=args.model_name).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    total_steps = len(train_loader) * args.epochs
    warmup_steps = int(total_steps * 0.1)
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )
    criterion = torch.nn.MSELoss()

    best_qwk = -1.0
    patience_counter = 0
    os.makedirs("models", exist_ok=True)

    for epoch in range(args.epochs):
        model.train()
        train_loss = 0.0
        for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{args.epochs}"):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            scores = batch["score"].to(device)

            with torch.amp.autocast("cuda" if torch.cuda.is_available() else "cpu", enabled=args.fp16 and torch.cuda.is_available()):
                preds = model(input_ids, attention_mask)
                loss = criterion(preds, scores)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            scheduler.step()
            train_loss += loss.item()

        avg_train_loss = train_loss / len(train_loader)

        # Validation
        model.eval()
        val_preds, val_labels = [], []
        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                scores = batch["score"].to(device)
                with torch.amp.autocast("cuda" if torch.cuda.is_available() else "cpu", enabled=args.fp16 and torch.cuda.is_available()):
                    preds = model(input_ids, attention_mask)
                val_preds.extend(preds.cpu().numpy())
                val_labels.extend(scores.cpu().numpy())

        val_preds_arr = np.array(val_preds)
        val_labels_arr = np.array(val_labels)
        qwk = quadratic_weighted_kappa(val_labels_arr, val_preds_arr)
        mae = mean_absolute_error(val_labels_arr, val_preds_arr)

        print(
            f"Epoch {epoch+1}: train_loss={avg_train_loss:.4f}, "
            f"val_qwk={qwk:.4f}, val_mae={mae:.4f}"
        )

        if qwk > best_qwk:
            best_qwk = qwk
            patience_counter = 0
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "tokenizer_name": args.model_name,
                    "qwk": qwk,
                    "mae": mae,
                },
                "models/best_model.pt",
            )
            print(f"  Saved best model (QWK={qwk:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= args.patience:
                print(f"Early stopping at epoch {epoch+1}")
                break

    print(f"\nTraining done. Best val QWK: {best_qwk:.4f}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", default="bert-base-uncased")
    parser.add_argument("--max_length", type=int, default=512)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--fp16", action="store_true", default=False)
    parser.add_argument("--test_size", type=float, default=0.2)
    parser.add_argument("--val_size", type=float, default=0.1)
    args = parser.parse_args()
    train(args)


if __name__ == "__main__":
    main()
