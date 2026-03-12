import pandas as pd
import re

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text

def load_asap_tsv(file_path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(file_path, sep="\t", encoding="cp1252")
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, sep="\t", encoding="latin1")

    df = df[["essay_id", "essay_set", "essay", "domain1_score"]].copy()
    df["essay"] = df["essay"].apply(clean_text)
    df["domain1_score"] = df["domain1_score"].astype(float)

    return df