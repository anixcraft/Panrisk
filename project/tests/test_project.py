import os
import sys

import pytest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, ROOT)
from i18n import T  # noqa: E402
from predict import predict_case, risk_band  # noqa: E402

CASE = dict(age=60, sex="F", creatinine=1.0, LYVE1=1.0, REG1B=30.0, TFF1=200.0,
            plasma_CA19_9=None, REG1A=None)
HIGH = dict(age=68, sex="M", creatinine=0.4, LYVE1=8.0, REG1B=150.0, TFF1=1500.0,
            plasma_CA19_9=400.0, REG1A=900.0)


def test_probability_valid_and_missing_ok():
    r = predict_case(CASE)
    assert 0 <= r["probability"] <= 1 and r["band"] in {"low", "inconclusive", "high"}


def test_high_marker_case_scores_higher():
    assert predict_case(HIGH)["probability"] > predict_case(CASE)["probability"]


def test_bands():
    assert risk_band(0.5, 0.23) == "high"
    assert risk_band(0.15, 0.23) == "inconclusive"
    assert risk_band(0.05, 0.23) == "low"


def test_translations_have_same_keys():
    assert set(T["hi"]) == set(T["en"]) == set(T["mr"])


@pytest.mark.parametrize("lang", ["en", "hi", "mr"])
def test_languages_return_text(lang):
    r = predict_case(HIGH, lang=lang)
    assert r["guidance"] and len(r["factors"]) == 3


def test_out_of_range_warns():
    assert predict_case({**CASE, "age": 105})["warnings"]


def test_api():
    from fastapi.testclient import TestClient
    from app.api import app
    c = TestClient(app)
    assert c.get("/health").status_code == 200
    ok = c.post("/predict", json={**CASE, "lang": "hi"})
    assert ok.status_code == 200 and "probability" in ok.json()
    assert c.post("/predict", json={**CASE, "creatinine": -1}).status_code == 422


def test_streamlit_app_runs():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(os.path.join(ROOT, "app", "streamlit_app.py"), default_timeout=60).run()
    assert not at.exception
    at.button[0].click().run()
    assert not at.exception and len(at.metric) == 1
