"""
Train the final model and save everything the app needs.
Run from the project root:  python src/train_final.py

- Random Forest in a leakage-free Pipeline, isotonic-calibrated
- decision threshold chosen on OUT-OF-FOLD training predictions (target sensitivity >= 0.90),
  so the test set stays untouched
- deployed model uses only what a user can enter: age, sex, biomarkers
- SHAP plots saved to reports/, artifacts to models/model.joblib
"""
import json
import os
import sys

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (brier_score_loss, confusion_matrix, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import StratifiedKFold, cross_val_predict, train_test_split
from sklearn.pipeline import Pipeline

sys.path.insert(0, os.path.dirname(__file__))
from pipeline import (NUMERIC, PASSTHROUGH, RANDOM_STATE, build_features, load_data,
                      make_preprocessor)

TARGET_SENSITIVITY = 0.90
DATA = "data/Debernardi_et_al_2020_data.csv"
# sample_origin / patient_cohort describe the study design, not the patient -> not deployed
DEPLOY_CATEGORICAL = ["sex"]


def make_base():
    return Pipeline([
        ("pre", make_preprocessor(DEPLOY_CATEGORICAL)),
        ("clf", RandomForestClassifier(n_estimators=300, max_depth=6,
                                       class_weight="balanced", random_state=RANDOM_STATE)),
    ])


def pick_threshold_oof(y, proba, target=TARGET_SENSITIVITY):
    best = 0.05
    for t in np.arange(0.05, 0.95, 0.01):
        if recall_score(y, (proba >= t).astype(int)) >= target:
            best = float(t)
    return round(best, 2)


def main():
    os.makedirs("models", exist_ok=True)
    os.makedirs("reports", exist_ok=True)
    df = build_features(load_data(DATA))
    cols = NUMERIC + DEPLOY_CATEGORICAL + PASSTHROUGH
    X, y = df[cols], df["target_binary"]
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)

    cal = CalibratedClassifierCV(make_base(), method="isotonic", cv=5)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    oof = cross_val_predict(cal, X_tr, y_tr, cv=cv, method="predict_proba")[:, 1]
    threshold = pick_threshold_oof(y_tr, oof)

    cal.fit(X_tr, y_tr)
    proba = cal.predict_proba(X_te)[:, 1]
    pred = (proba >= threshold).astype(int)
    metrics = {
        "threshold": threshold,
        "test_roc_auc": round(roc_auc_score(y_te, proba), 4),
        "test_brier": round(brier_score_loss(y_te, proba), 4),
        "test_sensitivity": round(recall_score(y_te, pred), 4),
        "test_precision": round(precision_score(y_te, pred), 4),
        "test_specificity": round(recall_score(y_te, pred, pos_label=0), 4),
        "confusion_matrix": confusion_matrix(y_te, pred).tolist(),
        "n_train": int(len(X_tr)), "n_test": int(len(X_te)),
    }

    Xe, ye, pe = X_te.reset_index(drop=True), y_te.reset_index(drop=True), pd.Series(pred)
    fair = []
    for sx in sorted(Xe["sex"].unique()):
        m = Xe["sex"] == sx
        fair.append({"group": f"sex={sx}", "n": int(m.sum()), "positives": int(ye[m].sum()),
                     "sensitivity": round(float(recall_score(ye[m], pe[m])), 3)})
    bins = pd.cut(Xe["age"], bins=[0, 50, 65, 120], labels=["<50", "50-65", ">65"])
    for g in ["<50", "50-65", ">65"]:
        m = bins == g
        if m.sum() and ye[m].sum():
            fair.append({"group": f"age {g}", "n": int(m.sum()), "positives": int(ye[m].sum()),
                         "sensitivity": round(float(recall_score(ye[m], pe[m])), 3)})
    metrics["subgroup_sensitivity"] = fair

    # SHAP on a plain (uncalibrated) forest fitted on the same training data
    base = make_base().fit(X_tr, y_tr)
    pre, rf = base.named_steps["pre"], base.named_steps["clf"]
    names = [n.split("__", 1)[-1] for n in pre.get_feature_names_out()]
    Xt = pre.transform(X_te)
    Xt = Xt.toarray() if hasattr(Xt, "toarray") else np.asarray(Xt)
    sv = shap.TreeExplainer(rf).shap_values(Xt)
    sv = sv[1] if isinstance(sv, list) else (sv[..., 1] if sv.ndim == 3 else sv)
    shap.summary_plot(sv, Xt, feature_names=names, show=False, plot_size=(8, 5))
    plt.tight_layout(); plt.savefig("reports/shap_beeswarm.png", dpi=130); plt.close()
    shap.summary_plot(sv, Xt, feature_names=names, plot_type="bar", show=False, plot_size=(7, 4.5))
    plt.tight_layout(); plt.savefig("reports/shap_importance.png", dpi=130); plt.close()
    imp = sorted(zip(names, np.abs(sv).mean(0)), key=lambda t: -t[1])
    metrics["top_features_shap"] = [(n, round(float(v), 4)) for n, v in imp[:6]]

    joblib.dump({"calibrated": cal, "base": base, "threshold": threshold,
                 "feature_names": names, "columns": cols,
                 "train_medians": X_tr[NUMERIC].median().to_dict(),
                 "train_ranges": {c: [float(X_tr[c].min()), float(X_tr[c].max())] for c in NUMERIC}},
                "models/model.joblib")
    with open("reports/final_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()
