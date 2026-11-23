"""Prediction engine: calibrated probability, risk band, per-patient SHAP explanation."""
import os
import sys

import joblib
import numpy as np
import pandas as pd
import shap

sys.path.insert(0, os.path.dirname(__file__))
from i18n import factor_label, tr  # noqa: E402

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "model.joblib")
INCONCLUSIVE_FRACTION = 0.6   # design choice (not validated): p in [0.6*t, t) -> "inconclusive"
_ART = {}


def _load():
    if not _ART:
        if not os.path.exists(MODEL_PATH):
            raise RuntimeError("Model not found. Run:  python src/train_final.py")
        art = joblib.load(MODEL_PATH)
        art["explainer"] = shap.TreeExplainer(art["base"].named_steps["clf"])
        _ART.update(art)
    return _ART


def _group(name):
    if name.startswith("sex_"):
        return "sex"
    if name.endswith("_missing"):
        return name[: -len("_missing")]
    return name


def risk_band(p, threshold):
    if p >= threshold:
        return "high"
    if p >= INCONCLUSIVE_FRACTION * threshold:
        return "inconclusive"
    return "low"


def predict_case(inputs, lang="en", top_k=3):
    """inputs: age, sex ('F'/'M'), creatinine, LYVE1, REG1B, TFF1,
    plasma_CA19_9 (None if not measured), REG1A (None if not measured)."""
    art = _load()
    row = {k: inputs[k] for k in ("age", "sex", "creatinine", "LYVE1", "REG1B", "TFF1")}
    row["plasma_CA19_9"] = inputs.get("plasma_CA19_9")
    row["REG1A"] = inputs.get("REG1A")
    row["plasma_CA19_9_missing"] = int(row["plasma_CA19_9"] is None)
    row["REG1A_missing"] = int(row["REG1A"] is None)
    df = pd.DataFrame([row])[art["columns"]]
    for c in ("plasma_CA19_9", "REG1A"):
        df[c] = pd.to_numeric(df[c], errors="coerce")

    p = float(art["calibrated"].predict_proba(df)[0, 1])
    band = risk_band(p, art["threshold"])

    pre = art["base"].named_steps["pre"]
    Xt = pre.transform(df)
    Xt = Xt.toarray() if hasattr(Xt, "toarray") else np.asarray(Xt)
    sv = art["explainer"].shap_values(Xt)
    sv = sv[1] if isinstance(sv, list) else (sv[..., 1] if sv.ndim == 3 else sv)
    agg = {}
    for n, v in zip(art["feature_names"], np.asarray(sv)[0]):
        agg[_group(n)] = agg.get(_group(n), 0.0) + float(v)
    factors = []
    for feat, c in sorted(agg.items(), key=lambda kv: -abs(kv[1]))[:top_k]:
        label = factor_label(lang, feat)
        factors.append({"feature": feat, "label": label, "contribution": round(c, 4),
                        "direction": "raises" if c > 0 else "lowers",
                        "sentence": tr(lang, "raised" if c > 0 else "lowered", f=label)})

    warnings = []
    for f, (lo, hi) in art["train_ranges"].items():
        v = row.get(f)
        if v is not None and not (lo <= float(v) <= hi):
            warnings.append(tr(lang, "warn_range", f=factor_label(lang, f)))

    return {"probability": round(min(max(p, 0.01), 0.99), 4),  # clipped for display only
            "band": band, "threshold": art["threshold"],
            "band_label": tr(lang, f"band_{band}"), "guidance": tr(lang, f"guide_{band}"),
            "factors": factors, "warnings": warnings, "lang": lang}
