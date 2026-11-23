"""FastAPI service.  Run from project root:  uvicorn app.api:app --reload"""
import os
import sys
from typing import Literal, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from predict import predict_case  # noqa: E402

app = FastAPI(title="Pancreatic Cancer Risk Screening (research prototype)", version="0.1")


class Case(BaseModel):
    age: float = Field(ge=18, le=110)
    sex: Literal["F", "M"]
    creatinine: float = Field(ge=0, le=20)
    LYVE1: float = Field(ge=0, le=1000)
    REG1B: float = Field(ge=0, le=5000)
    TFF1: float = Field(ge=0, le=5000)
    plasma_CA19_9: Optional[float] = Field(default=None, ge=0, le=100000)
    REG1A: Optional[float] = Field(default=None, ge=0, le=5000)
    lang: Literal["en", "hi", "mr"] = "en"


@app.get("/health")
def health():
    return {"status": "ok", "disclaimer": "Research prototype; not a medical diagnosis."}


@app.post("/predict")
def predict(case: Case):
    d = case.model_dump()
    lang = d.pop("lang")
    return predict_case(d, lang=lang)
