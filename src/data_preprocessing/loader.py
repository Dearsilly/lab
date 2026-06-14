"""ASAP Dataset loader."""
import pandas as pd
from pathlib import Path


def load_asap_csv(csv_path: str = "data/raw/asap/asap_all.csv") -> pd.DataFrame:
    """Load the merged ASAP CSV file."""
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} essays from {csv_path}")
    return df


def get_score_range_per_set(df: pd.DataFrame) -> dict:
    """Get min/max score for each essay set."""
    ranges = {}
    for essay_set in sorted(df["essay_set"].unique()):
        subset = df[df["essay_set"] == essay_set]
        ranges[essay_set] = {
            "min": float(subset["score"].min()),
            "max": float(subset["score"].max()),
            "mean": float(subset["score"].mean()),
            "std": float(subset["score"].std()),
            "count": len(subset),
        }
    return ranges


def normalize_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize scores to [0, 1] range per essay set."""
    df = df.copy()
    df["score_normalized"] = 0.0
    for essay_set in df["essay_set"].unique():
        mask = df["essay_set"] == essay_set
        scores = df.loc[mask, "score"]
        s_min, s_max = scores.min(), scores.max()
        if s_max > s_min:
            df.loc[mask, "score_normalized"] = (scores - s_min) / (s_max - s_min)
        else:
            df.loc[mask, "score_normalized"] = 0.5
    return df
