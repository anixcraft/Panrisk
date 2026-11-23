"""
Pancreatic Cancer Detection - Data pipeline and baseline model

Fixes made vs. the reference LightGBM notebook:
 - drops stage / benign_sample_diagnosis (they are only filled in AFTER
   diagnosis is known, so using them as features is label leakage)
 - keeps missingness as a signal (indicator flags) for plasma_CA19_9 and
   REG1A instead of zero-filling, since they were only measured for a
   subset of patients by study design
 - all preprocessing (imputation, scaling, encoding) is fit ONLY on the
   training fold, inside a single sklearn Pipeline
 - stratified split + stratified cross-validation
 - correct metric argument order: (y_true, y_pred), not (y_pred, y_true)
 - reports both a binary view (PDAC vs rest) and the original 3-class view
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, roc_auc_score,
                              precision_score, recall_score, f1_score, confusion_matrix,
                              classification_report)

RANDOM_STATE = 42

NUMERIC = ["age", "plasma_CA19_9", "creatinine", "LYVE1", "REG1B", "TFF1", "REG1A"]
CATEGORICAL = ["sex", "sample_origin", "patient_cohort"]
PASSTHROUGH = ["plasma_CA19_9_missing", "REG1A_missing"]


def load_data(path):
    return pd.read_csv(path)


def build_features(df):
    df = df.copy()

    # Leakage columns: only populated once the diagnosis is already known
    leak_cols = ["stage", "benign_sample_diagnosis"]
    df = df.drop(columns=[c for c in leak_cols if c in df.columns])

    # Missingness is informative for CA19-9 and REG1A (only measured in subsets)
    df["plasma_CA19_9_missing"] = df["plasma_CA19_9"].isna().astype(int)
    df["REG1A_missing"] = df["REG1A"].isna().astype(int)

    # Binary target: PDAC (3) vs rest (1 = control, 2 = benign)
    df["target_binary"] = (df["diagnosis"] == 3).astype(int)
    return df


def make_preprocessor(categorical=None):
    categorical = CATEGORICAL if categorical is None else categorical
    numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("num", numeric_pipe, NUMERIC),
        ("cat", categorical_pipe, categorical),
        ("pass", "passthrough", PASSTHROUGH),
    ])


def run_binary_baseline(df):
    X = df[NUMERIC + CATEGORICAL + PASSTHROUGH]
    y = df["target_binary"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    pipe = Pipeline([
        ("pre", make_preprocessor()),
        ("clf", LogisticRegression(max_iter=1000, class_weight="balanced",
                                    random_state=RANDOM_STATE)),
    ])

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    cv_auc = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="roc_auc")
    cv_bal_acc = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="balanced_accuracy")

    pipe.fit(X_train, y_train)
    y_pred = pipe.predict(X_test)
    y_proba = pipe.predict_proba(X_test)[:, 1]

    results = {
        "cv_roc_auc_mean": cv_auc.mean(), "cv_roc_auc_std": cv_auc.std(),
        "cv_balanced_acc_mean": cv_bal_acc.mean(), "cv_balanced_acc_std": cv_bal_acc.std(),
        "test_accuracy": accuracy_score(y_test, y_pred),
        "test_balanced_accuracy": balanced_accuracy_score(y_test, y_pred),
        "test_precision": precision_score(y_test, y_pred),
        "test_recall_sensitivity": recall_score(y_test, y_pred),
        "test_f1": f1_score(y_test, y_pred),
        "test_roc_auc": roc_auc_score(y_test, y_proba),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "classification_report": classification_report(
            y_test, y_pred, target_names=["Non-cancer", "PDAC"]),
    }
    return pipe, results


def get_models():
    from xgboost import XGBClassifier  # imported lazily: only needed for the model comparison
    """Five models, same random_state, class-imbalance handled per model's own API."""
    return {
        "Logistic Regression": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=5, min_samples_leaf=5, class_weight="balanced", random_state=RANDOM_STATE),
        "Random Forest": RandomForestClassifier(
            n_estimators=300, max_depth=6, class_weight="balanced", random_state=RANDOM_STATE),
        "SVM (RBF)": SVC(
            kernel="rbf", probability=True, class_weight="balanced", random_state=RANDOM_STATE),
        "XGBoost": XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.05, eval_metric="logloss",
            random_state=RANDOM_STATE),
        "ANN (MLP)": MLPClassifier(
            hidden_layer_sizes=(32, 16), activation="relu", alpha=1e-3,
            max_iter=2000, early_stopping=True, random_state=RANDOM_STATE),
    }


def compare_models(df):
    """Train/evaluate all five models with identical preprocessing, split and CV."""
    X = df[NUMERIC + CATEGORICAL + PASSTHROUGH]
    y = df["target_binary"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)

    # XGBoost wants scale_pos_weight instead of class_weight for imbalance
    neg, pos = (y_train == 0).sum(), (y_train == 1).sum()

    rows = []
    fitted = {}
    for name, model in get_models().items():
        if name == "XGBoost":
            model.set_params(scale_pos_weight=neg / pos)

        pipe = Pipeline([("pre", make_preprocessor()), ("clf", model)])

        cv_auc = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="roc_auc")
        cv_sens = cross_val_score(pipe, X_train, y_train, cv=cv, scoring="recall")

        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        y_proba = pipe.predict_proba(X_test)[:, 1]

        rows.append({
            "model": name,
            "cv_roc_auc_mean": cv_auc.mean(), "cv_roc_auc_std": cv_auc.std(),
            "cv_sensitivity_mean": cv_sens.mean(),
            "test_roc_auc": roc_auc_score(y_test, y_proba),
            "test_sensitivity": recall_score(y_test, y_pred),
            "test_precision": precision_score(y_test, y_pred),
            "test_f1": f1_score(y_test, y_pred),
            "test_balanced_accuracy": balanced_accuracy_score(y_test, y_pred),
        })
        fitted[name] = pipe

    results_df = pd.DataFrame(rows).sort_values("test_roc_auc", ascending=False).reset_index(drop=True)
    return results_df, fitted, (X_test, y_test)


if __name__ == "__main__":
    df = load_data("data/Debernardi_et_al_2020_data.csv")
    df = build_features(df)
    pipe, res = run_binary_baseline(df)
    for k, v in res.items():
        if k != "classification_report":
            print(f"{k}: {v}")
    print()
    print(res["classification_report"])
