"""Train/val/test split with prompt isolation."""
import pandas as pd
from sklearn.model_selection import train_test_split


def split_by_prompt(
    df: pd.DataFrame,
    test_size: float = 0.2,
    val_size: float = 0.1,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    真正的 prompt 隔离划分：将整个 essay_set 分配到 train/test/val。
    同一 essay_set 的作文不会同时出现在训练集和测试集中，防止数据泄露。

    test_size: essay_set 级别分配给测试集的比例
    val_size: 剩余 essay_set 中分配给验证集的比例
    """
    essay_sets = sorted(df["essay_set"].unique())
    n_sets = len(essay_sets)

    if n_sets < 3:
        # 题目太少时，降级为按样本划分并给出警告
        print("WARNING: fewer than 3 essay_sets, falling back to sample-level split")
        return _split_samples(df, test_size, val_size, random_state)

    # 将 essay_set 整体分配到 train/test
    train_sets, test_sets = train_test_split(
        essay_sets, test_size=max(test_size, 1 / n_sets),
        random_state=random_state,
    )

    # 从 train 的部分中再分出 val
    val_ratio = val_size / (1 - test_size)
    if len(train_sets) >= 2 and val_ratio > 0:
        train_sets, val_sets = train_test_split(
            train_sets, test_size=val_ratio, random_state=random_state,
        )
    else:
        val_sets = []

    train_df = df[df["essay_set"].isin(train_sets)].copy()
    val_df = df[df["essay_set"].isin(val_sets)].copy() if val_sets else pd.DataFrame(columns=df.columns)
    test_df = df[df["essay_set"].isin(test_sets)].copy()

    # 验证无泄露
    train_set_ids = set(train_df["essay_set"].unique())
    test_set_ids = set(test_df["essay_set"].unique())
    val_set_ids = set(val_df["essay_set"].unique())
    assert train_set_ids.isdisjoint(test_set_ids), "Data leak: train and test share essay_sets!"
    assert train_set_ids.isdisjoint(val_set_ids), "Data leak: train and val share essay_sets!"
    assert test_set_ids.isdisjoint(val_set_ids) or not val_sets, "Data leak: test and val share essay_sets!"

    print(
        f"Split: train={len(train_df)} (sets {sorted(train_set_ids)}), "
        f"val={len(val_df)} (sets {sorted(val_set_ids)}), "
        f"test={len(test_df)} (sets {sorted(test_set_ids)})"
    )
    return train_df, val_df, test_df


def _split_samples(
    df: pd.DataFrame, test_size: float, val_size: float, random_state: int
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """备用：样本级划分（当 essay_set 数量不足时使用）。"""
    train_df, test_df = train_test_split(
        df, test_size=test_size, random_state=random_state,
    )
    val_ratio = val_size / (1 - test_size)
    train_df, val_df = train_test_split(
        train_df, test_size=val_ratio, random_state=random_state,
    )
    print(f"Split (sample-level): train={len(train_df)}, val={len(val_df)}, test={len(test_df)}")
    return train_df, val_df, test_df
