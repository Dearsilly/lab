import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, cohen_kappa_score


def calc_metrics(y_true, y_pred):
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    mse = mean_squared_error(y_true, y_pred)
    mae = mean_absolute_error(y_true, y_pred)

    y_true_round = np.round(y_true).astype(int)
    y_pred_round = np.round(y_pred).astype(int)

    qwk = cohen_kappa_score(y_true_round, y_pred_round, weights="quadratic")

    return {
        "mse": float(mse),
        "mae": float(mae),
        "qwk": float(qwk),
    }