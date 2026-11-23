"""
Step 5: Calibration, threshold tuning, and fairness checks.

Carries forward Random Forest (Step 4 winner on ROC-AUC) and:
 - calibrates its probabilities (isotonic regression via CalibratedClassifierCV)
 - picks a sensitivity-first decision threshold (>=90% sensitivity target)
 - checks sensitivity across sex and age subgroups
 - produces a calibration curve and a decision curve analysis plot
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (roc_auc_score, brier_score_loss, recall_score,
                              precision_score, confusion_matrix)

from pipeline import make_preprocessor, NUMERIC, CATEGORICAL, PASSTHROUGH, RANDOM_STATE


def build_calibrated_model(df):
    X = df[NUMERIC + CATEGORICAL + PASSTHROUGH]
    y = df["target_binary"]
    meta = df[["sex", "age"]]

    X_train, X_test, y_train, y_test, meta_train, meta_test = train_test_split(
        X, y, meta, test_size=0.2, stratify=y, random_state=RANDOM_STATE)

    base = Pipeline([
        ("pre", make_preprocessor()),
        ("clf", RandomForestClassifier(n_estimators=300, max_depth=6,
                                        class_weight="balanced", random_state=RANDOM_STATE)),
    ])
    base.fit(X_train, y_train)
    proba_uncal = base.predict_proba(X_test)[:, 1]

    cal = CalibratedClassifierCV(base, method="isotonic", cv=5)
    cal.fit(X_train, y_train)
    proba_cal = cal.predict_proba(X_test)[:, 1]

    return {
        "model": cal, "X_test": X_test, "y_test": y_test.reset_index(drop=True),
        "meta_test": meta_test.reset_index(drop=True),
        "proba_uncal": proba_uncal, "proba_cal": proba_cal,
        "brier_uncal": brier_score_loss(y_test, proba_uncal),
        "brier_cal": brier_score_loss(y_test, proba_cal),
        "roc_auc_cal": roc_auc_score(y_test, proba_cal),
    }


def pick_threshold(y_test, proba_cal, target_sensitivity=0.90):
    """Highest threshold that still meets the target sensitivity (fewest false positives)."""
    rows = []
    for t in np.arange(0.05, 0.95, 0.01):
        pred = (proba_cal >= t).astype(int)
        rows.append((t, recall_score(y_test, pred), precision_score(y_test, pred, zero_division=0)))
    tdf = pd.DataFrame(rows, columns=["threshold", "sensitivity", "precision"])
    eligible = tdf[tdf.sensitivity >= target_sensitivity]
    return eligible.sort_values("threshold", ascending=False).iloc[0], tdf


def fairness_report(y_test, y_pred, meta_test):
    rows = []
    for sx in meta_test["sex"].unique():
        mask = meta_test["sex"] == sx
        if mask.sum() > 0 and y_test[mask].sum() > 0:
            rows.append(("sex", sx, mask.sum(), recall_score(y_test[mask], y_pred[mask])))
    age_bins = pd.cut(meta_test["age"], bins=[0, 50, 65, 100], labels=["<50", "50-65", ">65"])
    for grp in age_bins.dropna().unique():
        mask = age_bins == grp
        if mask.sum() > 0 and y_test[mask].sum() > 0:
            rows.append(("age", str(grp), mask.sum(), recall_score(y_test[mask], y_pred[mask])))
    return pd.DataFrame(rows, columns=["dimension", "group", "n", "sensitivity"])
