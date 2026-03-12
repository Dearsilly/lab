import os
import torch
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer
from tqdm import tqdm

from src.preprocess import load_asap_tsv
from src.dataset import EssayDataset, denormalize_score
from src.model import BertForEssayScoring
from src.metrics import calc_metrics

MODEL_NAME = "bert-base-uncased"
DATA_PATH = "data/asap/training_set_rel3.tsv"

MAX_LEN = 512
BATCH_SIZE = 8
EPOCHS = 3
LR = 2e-5

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def evaluate(model, loader):
    model.eval()
    preds, labels = [], []

    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            label = batch["labels"].to(DEVICE)
            essay_sets = batch["essay_set"].cpu().numpy().tolist()

            token_type_ids = batch.get("token_type_ids")
            if token_type_ids is not None:
                token_type_ids = token_type_ids.to(DEVICE)

            outputs = model(input_ids, attention_mask, token_type_ids)

            pred_norms = outputs.cpu().numpy().tolist()
            label_norms = label.cpu().numpy().tolist()

            for essay_set, label_norm, pred_norm in zip(essay_sets, label_norms, pred_norms):
                real_label = denormalize_score(int(essay_set), float(label_norm))
                real_pred = denormalize_score(int(essay_set), float(pred_norm))

                labels.append(real_label)
                preds.append(real_pred)

    return calc_metrics(labels, preds)


def train():
    print("Loading data...")
    df = load_asap_tsv(DATA_PATH)

    # 与 evaluate.py 保持一致
    train_df, val_df = train_test_split(df, test_size=0.1, random_state=42)

    print(f"Train size: {len(train_df)}")
    print(f"Val size: {len(val_df)}")

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    train_dataset = EssayDataset(train_df, tokenizer, MAX_LEN)
    val_dataset = EssayDataset(val_df, tokenizer, MAX_LEN)

    train_loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=2,
        pin_memory=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=2,
        pin_memory=True
    )

    print("Building model...")
    model = BertForEssayScoring(MODEL_NAME).to(DEVICE)

    optimizer = torch.optim.AdamW(model.parameters(), lr=LR)
    criterion = torch.nn.MSELoss()

    best_qwk = -1.0

    os.makedirs("models", exist_ok=True)

    print(f"Training on device: {DEVICE}")
    print("Start training...")

    for epoch in range(EPOCHS):
        model.train()
        total_loss = 0.0

        loop = tqdm(train_loader, desc=f"Epoch {epoch + 1}/{EPOCHS}")
        for batch in loop:
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["labels"].to(DEVICE)

            token_type_ids = batch.get("token_type_ids")
            if token_type_ids is not None:
                token_type_ids = token_type_ids.to(DEVICE)

            optimizer.zero_grad()

            outputs = model(input_ids, attention_mask, token_type_ids)
            loss = criterion(outputs, labels)

            loss.backward()
            optimizer.step()

            total_loss += loss.item()
            loop.set_postfix(loss=f"{loss.item():.4f}")

        avg_train_loss = total_loss / len(train_loader)
        metrics = evaluate(model, val_loader)

        print(
            f"Epoch {epoch + 1}: "
            f"train_loss={avg_train_loss:.4f}, "
            f"metrics={metrics}"
        )

        if metrics["qwk"] > best_qwk:
            best_qwk = metrics["qwk"]

            torch.save(model.state_dict(), "models/best_model.pt")
            tokenizer.save_pretrained("models/tokenizer")

            print("Best model saved.")
            print(f"Current best QWK: {best_qwk:.4f}")

    print("Training finished.")
    print(f"Best validation QWK: {best_qwk:.4f}")


if __name__ == "__main__":
    train()