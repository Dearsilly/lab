import torch
import pandas as pd
from torch.utils.data import DataLoader
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer

from src.preprocess import load_asap_tsv
from src.dataset import EssayDataset, denormalize_score
from src.model import BertForEssayScoring
from src.metrics import calc_metrics

MODEL_NAME = "bert-base-uncased"
MODEL_PATH = "models/best_model.pt"
TOKENIZER_PATH = "models/tokenizer"
DATA_PATH = "data/asap/training_set_rel3.tsv"

MAX_LEN = 512
BATCH_SIZE = 8
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_model():
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_PATH)

    model = BertForEssayScoring(MODEL_NAME).to(DEVICE)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=DEVICE))
    model.eval()

    return tokenizer, model


def evaluate_loader(model, loader):
    model.eval()
    true_scores, pred_scores = [], []

    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(DEVICE)
            attention_mask = batch["attention_mask"].to(DEVICE)
            labels = batch["labels"].to(DEVICE)
            essay_sets = batch["essay_set"].cpu().numpy().tolist()

            token_type_ids = batch.get("token_type_ids")
            if token_type_ids is not None:
                token_type_ids = token_type_ids.to(DEVICE)

            outputs = model(input_ids, attention_mask, token_type_ids)

            pred_norms = outputs.cpu().numpy().tolist()
            true_norms = labels.cpu().numpy().tolist()

            for essay_set, true_norm, pred_norm in zip(essay_sets, true_norms, pred_norms):
                true_score = denormalize_score(int(essay_set), float(true_norm))
                pred_score = denormalize_score(int(essay_set), float(pred_norm))

                true_scores.append(true_score)
                pred_scores.append(pred_score)

    return true_scores, pred_scores


def evaluate_per_set(val_df, preds):
    result_df = val_df.copy().reset_index(drop=True)
    result_df["pred"] = preds

    print("\n===== Per-set Evaluation =====")
    for essay_set in sorted(result_df["essay_set"].unique()):
        subset = result_df[result_df["essay_set"] == essay_set]

        metrics = calc_metrics(
            subset["domain1_score"].tolist(),
            subset["pred"].tolist()
        )

        print(
            f"Set {essay_set}: "
            f"MSE={metrics['mse']:.4f}, "
            f"MAE={metrics['mae']:.4f}, "
            f"QWK={metrics['qwk']:.4f}, "
            f"N={len(subset)}"
        )


def main():
    print("Loading data...")
    df = load_asap_tsv(DATA_PATH)

    # 与 train.py 保持一致
    _, val_df = train_test_split(df, test_size=0.1, random_state=42)

    print("Loading model...")
    tokenizer, model = load_model()

    val_dataset = EssayDataset(val_df, tokenizer, MAX_LEN)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)

    print("Running evaluation...")
    labels, preds = evaluate_loader(model, val_loader)

    metrics = calc_metrics(labels, preds)

    print("\n===== Overall Evaluation =====")
    print(f"MSE: {metrics['mse']:.4f}")
    print(f"MAE: {metrics['mae']:.4f}")
    print(f"QWK: {metrics['qwk']:.4f}")

    evaluate_per_set(val_df, preds)


if __name__ == "__main__":
    main()