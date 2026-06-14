"""Tests for data preprocessing pipeline."""
import pytest
import numpy as np
import pandas as pd

from src.data_preprocessing.loader import normalize_scores, get_score_range_per_set
from src.data_preprocessing.cleaner import clean_text
from src.data_preprocessing.splitter import split_by_prompt
from src.data_preprocessing.tokenizer import create_tokenizer
from src.evaluation.metrics import quadratic_weighted_kappa, mean_absolute_error, pearson_correlation


def test_clean_text_html():
    assert clean_text("&amp; hello &lt;world&gt;") == "& hello <world>"


def test_clean_text_whitespace():
    assert clean_text("hello   world\n\nfoo") == "hello world foo"


def test_clean_text_url():
    # URL removed; double space from removal gets collapsed by \s+ -> single space
    result = clean_text("check http://example.com here")
    assert "http" not in result
    assert "check" in result
    assert "here" in result


def test_clean_text_empty():
    assert clean_text("") == ""
    assert clean_text(None) == ""


def test_normalize_scores(sample_df):
    df = normalize_scores(sample_df)
    assert "score_normalized" in df.columns
    # Set 1: min=2, max=6 -> normalized values
    set1 = df[df["essay_set"] == 1]
    assert set1["score_normalized"].iloc[0] == pytest.approx(0.0, abs=0.01)  # score=2
    assert set1["score_normalized"].iloc[2] == pytest.approx(1.0, abs=0.01)  # score=6


def test_score_range_per_set(sample_df):
    ranges = get_score_range_per_set(sample_df)
    assert 1 in ranges
    assert ranges[1]["min"] == 2
    assert ranges[1]["max"] == 6


def test_split_by_prompt(sample_df):
    train, val, test = split_by_prompt(sample_df, test_size=0.3, val_size=0.3)
    # No overlap between train and test essay IDs
    train_ids = set(train["essay_id"])
    test_ids = set(test["essay_id"])
    assert train_ids.isdisjoint(test_ids)
    # No overlap of essay_set between train and test (true prompt isolation)
    train_sets = set(train["essay_set"])
    test_sets = set(test["essay_set"])
    assert train_sets.isdisjoint(test_sets)


def test_tokenizer():
    tokenizer = create_tokenizer()
    texts = ["hello world", "this is a test"]
    encoded = tokenizer(
        texts, max_length=32, truncation=True, padding="max_length",
        return_tensors="pt",
    )
    assert "input_ids" in encoded
    assert "attention_mask" in encoded
    assert encoded["input_ids"].shape[0] == 2
    assert encoded["input_ids"].shape[1] == 32


def test_qwk_perfect():
    y = np.array([1, 2, 3, 4, 5])
    assert quadratic_weighted_kappa(y, y) == pytest.approx(1.0, abs=0.01)


def test_qwk_random():
    y_true = np.array([1, 2, 3, 4, 5])
    y_pred = np.array([5, 4, 3, 2, 1])
    qwk = quadratic_weighted_kappa(y_true, y_pred)
    assert qwk < 0  # Perfect disagreement should be negative


def test_mae():
    y_true = np.array([1.0, 2.0, 3.0])
    y_pred = np.array([1.5, 2.5, 3.5])
    assert mean_absolute_error(y_true, y_pred) == pytest.approx(0.5, abs=0.01)


def test_pearson():
    y = np.array([1, 2, 3, 4, 5])
    assert pearson_correlation(y, y) == pytest.approx(1.0, abs=0.01)
