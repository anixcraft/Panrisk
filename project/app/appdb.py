"""SQLite storage (free, file based). Demo doctors are fictional."""
import os
import sqlite3

ROOT = os.path.join(os.path.dirname(__file__), "..")
DB_PATH = os.environ.get("APP_DB", os.path.join(ROOT, "data", "app.db"))
DATA_DIR = os.path.dirname(os.path.abspath(DB_PATH))
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")

SCHEMA = """
CREATE TABLE IF NOT EXISTS patients(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_code TEXT UNIQUE NOT NULL,
  full_name TEXT NOT NULL, age INTEGER NOT NULL,
  sex TEXT NOT NULL CHECK(sex IN ('F','M')),
  phone TEXT, lang TEXT NOT NULL DEFAULT 'en',
  pw_hash TEXT NOT NULL, doctor_id INTEGER,
  failed_logins INTEGER NOT NULL DEFAULT 0, locked_until REAL NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS doctors(
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, specialty TEXT NOT NULL,
  languages TEXT NOT NULL, bio TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS appointments(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id INTEGER NOT NULL, doctor_id INTEGER NOT NULL,
  slot TEXT NOT NULL, reason TEXT, status TEXT NOT NULL DEFAULT 'booked',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE UNIQUE INDEX IF NOT EXISTS ux_slot ON appointments(doctor_id, slot) WHERE status='booked';
CREATE TABLE IF NOT EXISTS reports(
  id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER NOT NULL,
  filename TEXT, stored_path TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS results(
  id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER NOT NULL, report_id INTEGER,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  inputs TEXT NOT NULL, probability REAL NOT NULL, band TEXT NOT NULL, payload TEXT NOT NULL);
"""

DEMO_DOCTORS = [
    (1, "Dr. Asha Verma (demo)", "Gastroenterology", "English, Hindi",
     "Fictional demo profile. Digestive and pancreatic conditions."),
    (2, "Dr. Rohan Iyer (demo)", "Medical Oncology", "English, Hindi, Marathi",
     "Fictional demo profile. Cancer evaluation and follow-up."),
    (3, "Dr. Meera Kulkarni (demo)", "Hepatobiliary Surgery", "English, Marathi",
     "Fictional demo profile. Liver, bile duct and pancreas surgery."),
    (4, "Dr. Imran Shaikh (demo)", "General Physician", "English, Hindi, Marathi",
     "Fictional demo profile. First point of contact for any health concern."),
]


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)  # one connection per request
    conn.row_factory = sqlite3.Row
    return conn


def init():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    conn = connect()
    try:
        conn.executescript(SCHEMA)
        if not conn.execute("SELECT 1 FROM doctors LIMIT 1").fetchone():
            conn.executemany("INSERT INTO doctors VALUES (?,?,?,?,?)", DEMO_DOCTORS)
        conn.commit()
    finally:
        conn.close()
