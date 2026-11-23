"""Patient app backend.  Run from project root:  python -m uvicorn app.server:app --reload
Research prototype: NOT a medical device. Do not use with real patient data."""
import json
import os
import secrets
import sqlite3
import sys
import time
import uuid
from datetime import date, datetime, timedelta
from typing import Literal, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "src"))
import appdb  # noqa: E402
import appsec  # noqa: E402
import report_extract  # noqa: E402
from i18n import tr  # noqa: E402
from predict import predict_case  # noqa: E402

LANGS = ("en", "hi", "mr")
MAX_UPLOAD = 5 * 1024 * 1024
SECURE_COOKIES = os.environ.get("APP_SECURE_COOKIES") == "1"
appdb.init()

app = FastAPI(title="Patient app (research prototype)", version="0.2", docs_url=None, redoc_url=None)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; frame-ancestors 'none'")
    if request.url.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


def get_db():
    conn = appdb.connect()
    try:
        yield conn
    finally:
        conn.close()


def current(request: Request, conn=Depends(get_db)):
    pid = appsec.read_token(request.cookies.get("session"))
    row = conn.execute("SELECT * FROM patients WHERE id=?", (pid,)).fetchone() if pid else None
    if not row:
        raise HTTPException(401, "Please log in.")
    return row


def _login_cookie(resp: Response, pid: int):
    resp.set_cookie("session", appsec.make_token(pid), httponly=True, samesite="strict",
                    secure=SECURE_COOKIES, max_age=appsec.TTL, path="/")


def _patient_json(conn, p):
    doc = conn.execute("SELECT * FROM doctors WHERE id=?", (p["doctor_id"],)).fetchone() if p["doctor_id"] else None
    return {"patient_code": p["patient_code"], "full_name": p["full_name"], "age": p["age"],
            "sex": p["sex"], "phone": p["phone"], "lang": p["lang"],
            "doctor": dict(doc) if doc else None}


# ---------- accounts ----------
class Register(BaseModel):
    full_name: str = Field(min_length=2, max_length=80)
    age: int = Field(ge=18, le=110)
    sex: Literal["F", "M"]
    phone: Optional[str] = Field(default=None, max_length=20)
    lang: Literal["en", "hi", "mr"] = "en"
    password: str = Field(min_length=8, max_length=128)


class Login(BaseModel):
    patient_code: str = Field(max_length=20)
    password: str = Field(max_length=128)


@app.post("/api/register")
def register(body: Register, response: Response, conn=Depends(get_db)):
    pw_hash = appsec.hash_password(body.password)
    for _ in range(20):
        code = f"PT{secrets.randbelow(900000) + 100000}"
        try:
            cur = conn.execute(
                "INSERT INTO patients(patient_code,full_name,age,sex,phone,lang,pw_hash) VALUES (?,?,?,?,?,?,?)",
                (code, body.full_name.strip(), body.age, body.sex, (body.phone or "").strip() or None,
                 body.lang, pw_hash))
            conn.commit()
            _login_cookie(response, cur.lastrowid)
            return {"patient_code": code}
        except sqlite3.IntegrityError:
            continue
    raise HTTPException(500, "Could not create an ID. Please try again.")


@app.post("/api/login")
def login(body: Login, response: Response, conn=Depends(get_db)):
    bad = HTTPException(401, "Invalid ID or password, or the account is temporarily locked.")
    row = conn.execute("SELECT * FROM patients WHERE patient_code=?",
                       (body.patient_code.strip().upper(),)).fetchone()
    now = time.time()
    if not row:
        appsec.verify_password(body.password, appsec.DUMMY_HASH)  # keep timing similar
        raise bad
    if row["locked_until"] > now:
        raise bad
    if appsec.verify_password(body.password, row["pw_hash"]):
        conn.execute("UPDATE patients SET failed_logins=0, locked_until=0 WHERE id=?", (row["id"],))
        conn.commit()
        _login_cookie(response, row["id"])
        return {"ok": True}
    fails = row["failed_logins"] + 1
    locked = now + 300 if fails >= 5 else 0
    conn.execute("UPDATE patients SET failed_logins=?, locked_until=? WHERE id=?",
                 (0 if locked else fails, locked, row["id"]))
    conn.commit()
    raise bad


@app.post("/api/logout")
def logout(response: Response):
    response.delete_cookie("session", path="/")
    return {"ok": True}


@app.get("/api/me")
def me(p=Depends(current), conn=Depends(get_db)):
    return _patient_json(conn, p)


class Profile(BaseModel):
    lang: Optional[Literal["en", "hi", "mr"]] = None
    age: Optional[int] = Field(default=None, ge=18, le=110)
    doctor_id: Optional[int] = None
    clear_doctor: bool = False


@app.patch("/api/me")
def update_me(body: Profile, p=Depends(current), conn=Depends(get_db)):
    if body.lang:
        conn.execute("UPDATE patients SET lang=? WHERE id=?", (body.lang, p["id"]))
    if body.age:
        conn.execute("UPDATE patients SET age=? WHERE id=?", (body.age, p["id"]))
    if body.clear_doctor:
        conn.execute("UPDATE patients SET doctor_id=NULL WHERE id=?", (p["id"],))
    elif body.doctor_id is not None:
        if not conn.execute("SELECT 1 FROM doctors WHERE id=?", (body.doctor_id,)).fetchone():
            raise HTTPException(404, "Doctor not found.")
        conn.execute("UPDATE patients SET doctor_id=? WHERE id=?", (body.doctor_id, p["id"]))
    conn.commit()
    return _patient_json(conn, conn.execute("SELECT * FROM patients WHERE id=?", (p["id"],)).fetchone())


# ---------- doctors and appointments ----------
@app.get("/api/doctors")
def doctors(p=Depends(current), conn=Depends(get_db)):
    return [dict(r) for r in conn.execute("SELECT * FROM doctors ORDER BY id")]


def _day_slots(d: date):
    if d.weekday() == 6:  # Sunday closed
        return []
    out = []
    for start, end in (((10, 0), (13, 0)), ((14, 0), (17, 0))):
        t = datetime(d.year, d.month, d.day, *start)
        stop = datetime(d.year, d.month, d.day, *end)
        while t < stop:
            out.append(t.strftime("%Y-%m-%d %H:%M"))
            t += timedelta(minutes=30)
    return out


def _free_slots(conn, doctor_id, d: date):
    if not (date.today() <= d <= date.today() + timedelta(days=14)):
        return []
    taken = {r["slot"] for r in conn.execute(
        "SELECT slot FROM appointments WHERE doctor_id=? AND status='booked' AND slot LIKE ?",
        (doctor_id, d.isoformat() + "%"))}
    earliest = (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    return [s for s in _day_slots(d) if s not in taken and s >= earliest]


@app.get("/api/slots")
def slots(doctor_id: int, day: str, p=Depends(current), conn=Depends(get_db)):
    try:
        d = date.fromisoformat(day)
    except ValueError:
        raise HTTPException(422, "Invalid date.")
    if not conn.execute("SELECT 1 FROM doctors WHERE id=?", (doctor_id,)).fetchone():
        raise HTTPException(404, "Doctor not found.")
    return {"slots": _free_slots(conn, doctor_id, d)}


class Booking(BaseModel):
    doctor_id: int
    slot: str = Field(pattern=r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
    reason: Optional[str] = Field(default=None, max_length=200)


@app.post("/api/appointments")
def book(body: Booking, p=Depends(current), conn=Depends(get_db)):
    if not conn.execute("SELECT 1 FROM doctors WHERE id=?", (body.doctor_id,)).fetchone():
        raise HTTPException(404, "Doctor not found.")
    if body.slot not in _free_slots(conn, body.doctor_id, date.fromisoformat(body.slot[:10])):
        raise HTTPException(409, "That time is not available. Please pick another slot.")
    if conn.execute("SELECT 1 FROM appointments WHERE patient_id=? AND slot=? AND status='booked'",
                    (p["id"], body.slot)).fetchone():
        raise HTTPException(409, "You already have an appointment at that time.")
    try:
        cur = conn.execute("INSERT INTO appointments(patient_id,doctor_id,slot,reason) VALUES (?,?,?,?)",
                           (p["id"], body.doctor_id, body.slot, (body.reason or "").strip() or None))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(409, "That time was just taken. Please pick another slot.")
    return {"id": cur.lastrowid}


@app.get("/api/appointments")
def appointments(p=Depends(current), conn=Depends(get_db)):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = conn.execute(
        "SELECT a.id,a.slot,a.reason,a.status,d.name AS doctor,d.specialty FROM appointments a "
        "JOIN doctors d ON d.id=a.doctor_id WHERE a.patient_id=? ORDER BY a.slot", (p["id"],))
    out = []
    for r in rows:
        d = dict(r)
        d["upcoming"] = d["status"] == "booked" and d["slot"] >= now
        out.append(d)
    return out


@app.delete("/api/appointments/{appt_id}")
def cancel(appt_id: int, p=Depends(current), conn=Depends(get_db)):
    cur = conn.execute("UPDATE appointments SET status='cancelled' WHERE id=? AND patient_id=? AND status='booked'",
                       (appt_id, p["id"]))
    conn.commit()
    if not cur.rowcount:
        raise HTTPException(404, "Appointment not found.")
    return {"ok": True}


# ---------- reports and results ----------
@app.post("/api/reports/extract")
async def extract_report(file: UploadFile = File(...), p=Depends(current), conn=Depends(get_db)):
    name = file.filename or "report"
    ext = os.path.splitext(name)[1].lower()
    if ext not in (".pdf", ".csv", ".txt"):
        raise HTTPException(400, "Please upload a PDF, CSV or TXT report.")
    data = await file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "File is too large (max 5 MB).")
    if ext == ".pdf" and not data.startswith(b"%PDF"):
        raise HTTPException(400, "That file is not a valid PDF.")
    folder = os.path.join(appdb.UPLOAD_DIR, str(p["id"]))
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, uuid.uuid4().hex + ext)
    with open(path, "wb") as f:
        f.write(data)
    cur = conn.execute("INSERT INTO reports(patient_id,filename,stored_path) VALUES (?,?,?)",
                       (p["id"], name[:100], path))
    conn.commit()
    values, notes = report_extract.extract(path, ext)
    needed = ["age", "sex", "creatinine", "LYVE1", "REG1B", "TFF1"]
    missing = [k for k in needed if k not in values]
    if values and missing:
        notes.append("Some required values were not found in the report. Please fill them in below. "
                     "Routine lab reports often do not include LYVE1, REG1B or TFF1.")
    if not values and not notes:
        notes.append("No known biomarker values were found in this report. Please enter them manually.")
    return {"report_id": cur.lastrowid, "filename": name[:100], "values": values,
            "missing": missing, "notes": notes}


class Values(BaseModel):
    age: float = Field(ge=18, le=110)
    sex: Literal["F", "M"]
    creatinine: float = Field(ge=0, le=20)
    LYVE1: float = Field(ge=0, le=1000)
    REG1B: float = Field(ge=0, le=5000)
    TFF1: float = Field(ge=0, le=5000)
    plasma_CA19_9: Optional[float] = Field(default=None, ge=0, le=100000)
    REG1A: Optional[float] = Field(default=None, ge=0, le=5000)


class ResultIn(Values):
    report_id: Optional[int] = None


def _result_view(row, lang):
    payload = json.loads(row["payload"])
    r = payload.get(lang) or payload["en"]
    return {"id": row["id"], "created_at": row["created_at"], "lang": lang,
            "inputs": json.loads(row["inputs"]), **r,
            "expectation": tr(lang, f"expect_{r['band']}"), "disclaimer": tr(lang, "disclaimer")}


@app.post("/api/results")
def create_result(body: ResultIn, p=Depends(current), conn=Depends(get_db)):
    if body.report_id is not None and not conn.execute(
            "SELECT 1 FROM reports WHERE id=? AND patient_id=?", (body.report_id, p["id"])).fetchone():
        raise HTTPException(404, "Report not found.")
    inputs = body.model_dump(exclude={"report_id"})
    payload = {lg: predict_case(dict(inputs), lang=lg) for lg in LANGS}
    base = payload["en"]
    cur = conn.execute(
        "INSERT INTO results(patient_id,report_id,inputs,probability,band,payload) VALUES (?,?,?,?,?,?)",
        (p["id"], body.report_id, json.dumps(inputs), base["probability"], base["band"], json.dumps(payload)))
    conn.commit()
    row = conn.execute("SELECT * FROM results WHERE id=?", (cur.lastrowid,)).fetchone()
    return _result_view(row, p["lang"])


@app.get("/api/results")
def list_results(p=Depends(current), conn=Depends(get_db)):
    rows = conn.execute("SELECT id,created_at,probability,band FROM results WHERE patient_id=? ORDER BY id DESC",
                        (p["id"],))
    return [{**dict(r), "band_label": tr(p["lang"], f"band_{r['band']}")} for r in rows]


@app.get("/api/results/{rid}")
def get_result(rid: int, lang: Optional[Literal["en", "hi", "mr"]] = None,
               p=Depends(current), conn=Depends(get_db)):
    row = conn.execute("SELECT * FROM results WHERE id=? AND patient_id=?", (rid, p["id"])).fetchone()
    if not row:
        raise HTTPException(404, "Result not found.")
    return _result_view(row, lang or p["lang"])


@app.get("/.well-known/assetlinks.json")
def assetlinks():
    """Digital Asset Links for the Android wrapper. Paste the JSON into the ASSETLINKS_JSON environment variable."""
    raw = os.environ.get("ASSETLINKS_JSON")
    if not raw:
        raise HTTPException(404, "Not configured.")
    try:
        return JSONResponse(json.loads(raw))
    except ValueError:
        raise HTTPException(500, "ASSETLINKS_JSON is not valid JSON.")


app.mount("/", StaticFiles(directory=os.path.join(HERE, "static"), html=True), name="static")
