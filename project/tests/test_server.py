import os
import sys
import tempfile

TMP = tempfile.mkdtemp()
os.environ["APP_DB"] = os.path.join(TMP, "test.db")
ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.server import app  # noqa: E402

REG = {"full_name": "Test Patient", "age": 55, "sex": "F", "password": "correct-horse", "lang": "en"}
VALS = {"age": 68, "sex": "M", "creatinine": 0.4, "LYVE1": 8, "REG1B": 150, "TFF1": 1500,
        "plasma_CA19_9": 400, "REG1A": 900}


def new_client():
    c = TestClient(app)
    r = c.post("/api/register", json=REG)
    assert r.status_code == 200, r.text
    return c, r.json()["patient_code"]


def tiny_pdf(text):
    objs = ["<< /Type /Catalog /Pages 2 0 R >>", "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
            "/Resources << /Font << /F1 5 0 R >> >> >>"]
    stream = f"BT /F1 12 Tf 50 700 Td ({text}) Tj ET"
    objs += [f"<< /Length {len(stream)} >>\nstream\n{stream}\nendstream",
             "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{i} 0 obj\n{o}\nendobj\n".encode()
    x = len(out)
    out += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n".encode()
    for o in offs:
        out += f"{o:010d} 00000 n \n".encode()
    return out + f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{x}\n%%EOF".encode()


def test_auth_flow():
    assert TestClient(app).get("/api/me").status_code == 401
    c, code = new_client()
    assert code.startswith("PT") and c.get("/api/me").json()["full_name"] == "Test Patient"
    c.post("/api/logout")
    assert c.get("/api/me").status_code == 401
    assert c.post("/api/login", json={"patient_code": code, "password": "wrong-pass1"}).status_code == 401
    assert c.post("/api/login", json={"patient_code": code.lower(), "password": "correct-horse"}).status_code == 200
    assert c.get("/api/me").status_code == 200


def test_register_validation():
    c = TestClient(app)
    assert c.post("/api/register", json={**REG, "password": "short"}).status_code == 422
    assert c.post("/api/register", json={**REG, "age": 12}).status_code == 422


def test_lockout_after_five_failures():
    c, code = new_client()
    c.post("/api/logout")
    for _ in range(5):
        assert c.post("/api/login", json={"patient_code": code, "password": "nope-nope1"}).status_code == 401
    assert c.post("/api/login", json={"patient_code": code, "password": "correct-horse"}).status_code == 401


def test_doctor_selection_and_booking():
    c, _ = new_client()
    docs = c.get("/api/doctors").json()
    assert len(docs) >= 3
    me = c.patch("/api/me", json={"doctor_id": docs[0]["id"]}).json()
    assert me["doctor"]["id"] == docs[0]["id"]
    assert c.patch("/api/me", json={"doctor_id": 999}).status_code == 404
    from datetime import date, timedelta
    day = next(d for d in (date.today() + timedelta(days=i) for i in range(1, 8)) if d.weekday() != 6)
    slots = c.get("/api/slots", params={"doctor_id": docs[0]["id"], "day": day.isoformat()}).json()["slots"]
    assert slots
    b = c.post("/api/appointments", json={"doctor_id": docs[0]["id"], "slot": slots[0], "reason": "check"})
    assert b.status_code == 200
    other, _ = new_client()
    assert other.post("/api/appointments", json={"doctor_id": docs[0]["id"], "slot": slots[0]}).status_code == 409
    assert slots[0] not in c.get("/api/slots", params={"doctor_id": docs[0]["id"], "day": day.isoformat()}).json()["slots"]
    appts = c.get("/api/appointments").json()
    assert appts[0]["upcoming"] and appts[0]["doctor"]
    assert other.delete(f"/api/appointments/{b.json()['id']}").status_code == 404   # not theirs
    assert c.delete(f"/api/appointments/{b.json()['id']}").status_code == 200
    assert c.post("/api/appointments", json={"doctor_id": docs[0]["id"], "slot": "2001-01-01 10:00"}).status_code == 409


def test_result_flow_and_privacy():
    c, _ = new_client()
    r = c.post("/api/results", json=VALS)
    assert r.status_code == 200
    d = r.json()
    assert d["band"] in {"low", "inconclusive", "high"} and d["expectation"] and d["disclaimer"]
    hi = c.get(f"/api/results/{d['id']}", params={"lang": "hi"}).json()
    assert hi["lang"] == "hi" and hi["guidance"] != d["guidance"]
    assert len(c.get("/api/results").json()) == 1
    other, _ = new_client()
    assert other.get(f"/api/results/{d['id']}").status_code == 404
    assert other.get("/api/results").json() == []
    assert c.post("/api/results", json={**VALS, "creatinine": -1}).status_code == 422
    assert c.post("/api/results", json={**VALS, "report_id": 99999}).status_code == 404


def test_upload_csv_txt_pdf():
    c, _ = new_client()
    csv = b"age,sex,creatinine,LYVE1,REG1B,TFF1,plasma_CA19_9\n62,Female,0.9,3.2,45.5,210,37\n"
    e = c.post("/api/reports/extract", files={"file": ("lab.csv", csv, "text/csv")}).json()
    assert e["values"]["LYVE1"] == 3.2 and e["values"]["sex"] == "F" and e["missing"] == []
    txt = b"Age: 70\nSex: Male\nCreatinine (mg/ml): 0.5\nLYVE1: 7.7\nREG1B: 100\nTFF1: 900\nCA 19-9: 250"
    e = c.post("/api/reports/extract", files={"file": ("lab.txt", txt, "text/plain")}).json()
    assert e["values"]["plasma_CA19_9"] == 250
    pdf = tiny_pdf("Creatinine 0.8  LYVE1 2.5  REG1B 30  TFF1 200")
    e = c.post("/api/reports/extract", files={"file": ("lab.pdf", pdf, "application/pdf")}).json()
    assert e["values"].get("LYVE1") == 2.5 and "age" in e["missing"]
    assert any("not found" in n for n in e["notes"])


def test_upload_rejections():
    c, _ = new_client()
    assert c.post("/api/reports/extract", files={"file": ("x.exe", b"MZ", "application/octet-stream")}).status_code == 400
    assert c.post("/api/reports/extract", files={"file": ("x.pdf", b"not a pdf", "application/pdf")}).status_code == 400
    assert c.post("/api/reports/extract", files={"file": ("x.txt", b"a" * (5 * 1024 * 1024 + 10), "text/plain")}).status_code == 413
    assert TestClient(app).post("/api/reports/extract", files={"file": ("x.txt", b"hi", "text/plain")}).status_code == 401


def test_headers_and_static():
    c = TestClient(app)
    r = c.get("/api/doctors")
    assert r.headers["cache-control"] == "no-store" and r.headers["x-frame-options"] == "DENY"


def test_assetlinks(monkeypatch):
    c = TestClient(app)
    monkeypatch.delenv("ASSETLINKS_JSON", raising=False)
    assert c.get("/.well-known/assetlinks.json").status_code == 404
    monkeypatch.setenv("ASSETLINKS_JSON", '[{"relation":["delegate_permission/common.handle_all_urls"]}]')
    r = c.get("/.well-known/assetlinks.json")
    assert r.status_code == 200 and r.json()[0]["relation"]
    monkeypatch.setenv("ASSETLINKS_JSON", "not json")
    assert c.get("/.well-known/assetlinks.json").status_code == 500
