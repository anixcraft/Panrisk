"""Read biomarker values from an uploaded report (CSV, TXT or text-based PDF).
Never trusted blindly: the app always shows the values for the patient to confirm."""
import csv
import io
import re

HEADER_MAP = {"creatinine": "creatinine", "lyve1": "LYVE1", "reg1b": "REG1B", "reg1a": "REG1A",
              "tff1": "TFF1", "plasmaca199": "plasma_CA19_9", "ca199": "plasma_CA19_9",
              "age": "age", "sex": "sex", "gender": "sex"}
PATTERNS = {
    "creatinine": r"creatinine",
    "LYVE1": r"LYVE[\s\-]?1",
    "REG1B": r"REG[\s\-]?1[\s\-]?B",
    "REG1A": r"REG[\s\-]?1[\s\-]?A",
    "TFF1": r"TFF[\s\-]?1",
    "plasma_CA19_9": r"CA[\s\-]?19[\s\-]?9",
}
NUM = r"[^0-9\n]{0,25}?(\d+(?:\.\d+)?)"
MAX_TEXT = 200_000


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def _sex(v):
    v = str(v).strip().lower()
    return "F" if v in ("f", "female") else "M" if v in ("m", "male") else None


def from_csv(text):
    rows = list(csv.DictReader(io.StringIO(text)))
    out = {}
    if not rows:
        return out
    for k, v in rows[0].items():
        f = HEADER_MAP.get(_norm(k or ""))
        if not f or v is None or str(v).strip() == "":
            continue
        if f == "sex":
            s = _sex(v)
            if s:
                out[f] = s
        else:
            try:
                out[f] = float(v)
            except ValueError:
                pass
    return out


def from_text(text):
    out = {}
    for field, pat in PATTERNS.items():
        m = re.search(pat + NUM, text, re.I)
        if m:
            out[field] = float(m.group(1))
    m = re.search(r"\bage\b[^0-9\n]{0,10}(\d{1,3})", text, re.I)
    if m:
        out["age"] = float(m.group(1))
    m = re.search(r"\b(?:sex|gender)\b[^A-Za-z\n]{0,10}(female|male|f|m)\b", text, re.I)
    if m and _sex(m.group(1)):
        out["sex"] = _sex(m.group(1))
    return out


def extract(path, ext):
    """Returns (values, notes)."""
    notes = []
    if ext == ".pdf":
        from pypdf import PdfReader
        try:
            reader = PdfReader(path)
            if reader.is_encrypted:
                return {}, ["This PDF is password-protected. Please enter the values manually."]
            text = "\n".join((p.extract_text() or "") for p in reader.pages[:20])[:MAX_TEXT]
        except Exception:
            return {}, ["We could not read this PDF. Please enter the values manually."]
        if not text.strip():
            return {}, ["This PDF looks scanned (no readable text). Please enter the values manually."]
        return from_text(text), notes
    with open(path, "rb") as f:
        text = f.read(MAX_TEXT).decode("utf-8", errors="replace")
    if ext == ".csv":
        vals = from_csv(text)
        return (vals if vals else from_text(text)), notes
    return from_text(text), notes
