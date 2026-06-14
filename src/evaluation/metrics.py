"""Evaluation metrics: QWK and MAE."""
import numpy as np
from sklearn.metrics import cohen_kappa_score


def quadratic_weighted_kappa(
    y_true: np.ndarray, y_pred: np.ndarray, score_range: tuple[float, float] | None = None
) -> float:
    """Compute Quadratic Weighted Kappa.

    当 score_range 不为 None 时，先将归一化 [0,1] 分数去归一化到原始范围，
    再进行四舍五入计算离散 Kappa。

    当 score_range 为 None 且值域为 [0,1] 区间时，自动分 10 个等级计算，
    避免归一化分数 round 后只剩 0/1 两个类别。
    """
    y_t = np.asarray(y_true, dtype=float)
    y_p = np.asarray(y_pred, dtype=float)

    if score_range is not None:
        s_min, s_max = score_range
        y_t = y_t * (s_max - s_min) + s_min
        y_p = y_p * (s_max - s_min) + s_min
        y_t_rounded = np.round(y_t).astype(int)
        y_p_rounded = np.round(y_p).astype(int)
    elif y_t.min() >= 0 and y_t.max() <= 1:
        n_levels = 10
        y_t_rounded = np.clip(np.round(y_t * (n_levels - 1)), 0, n_levels - 1).astype(int)
        y_p_rounded = np.clip(np.round(y_p * (n_levels - 1)), 0, n_levels - 1).astype(int)
    else:
        y_t_rounded = np.round(y_t).astype(int)
        y_p_rounded = np.round(y_p).astype(int)

    return cohen_kappa_score(y_t_rounded, y_p_rounded, weights="quadratic")


def mean_absolute_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Mean Absolute Error."""
    return float(np.mean(np.abs(np.array(y_true) - np.array(y_pred))))


def pearson_correlation(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Compute Pearson correlation coefficient."""
    return float(np.corrcoef(y_true, y_pred)[0, 1])
