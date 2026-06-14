"""Pytest fixtures."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def sample_essay():
    return "I believe that writing skills are fundamental to academic success. Students who write well can express their ideas clearly."


@pytest.fixture
def sample_df():
    import pandas as pd
    return pd.DataFrame({
        "essay_id": [1, 2, 3, 4, 5, 6],
        "essay_set": [1, 1, 1, 2, 2, 2],
        "essay_text": [
            "essay one content here",
            "essay two content here",
            "essay three content here",
            "essay four content here",
            "essay five content here",
            "essay six content here",
        ],
        "score": [2, 4, 6, 3, 6, 9],
    })
