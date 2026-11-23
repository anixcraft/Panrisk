# Pancreatic Cancer Detection — AI/ML Project

Academic project, Dept. of Computer Science and Engineering, 2026–2027.

## Dataset

Debernardi et al. (2020), *urinary biomarkers for pancreatic cancer*
(PLOS Medicine, open access, CC-BY). 590 patients, 3-class diagnosis
(control / benign / PDAC). See `data/Debernardi_et_al_2020_documentation.csv`
for column definitions. **Cite the original paper in any report or
presentation.**

## Patient app (PancRISK+ Care, working title)

An installable web app (PWA) with a mobile-style interface:

- **Register / log in** with a generated Patient ID (e.g. `PT123456`) and a password. Passwords are hashed (scrypt), sessions use
  signed HttpOnly cookies, and 5 wrong attempts lock the account for 5 minutes.
- **Doctors**: browse demo (fictional) doctors and choose "my doctor".
- **Appointments**: pick doctor, date and a free slot (Mon-Sat, next 14 days), view, and cancel. Double-booking is blocked.
- **Check a report**: upload a CSV, TXT or text-based PDF (or type values). Extracted values are shown for the patient to verify,
  then the model returns a risk score, a band, plain-language reasons, and **what to expect next** in English, Hindi or Marathi.
- **Results history**, print / save as PDF, language switch.

Limits (be upfront about these in your presentation):
- The model needs the **urinary biomarker panel** (creatinine, LYVE1, REG1B, TFF1; CA19-9 and REG1A optional). Routine lab reports
  usually do not contain LYVE1, REG1B or TFF1, so no estimate is possible from them. Scanned images are not read (no OCR).
- Results are **research-prototype risk signals, not diagnoses**. Doctors and appointments are demo data; there is no clinic
  integration, reminders or payments. Menus and buttons are English only (results are trilingual).
- SQLite file storage, no encryption at rest. **Do not use real patient data.** Real use would need security review, consent,
  data-protection compliance and clinical validation.

## Turn it into a real app (free routes)

**1. Windows desktop app.** Install Python 3.10-3.12 (tick "Add Python to PATH"), then double-click `start_windows_app.bat`.
First run installs everything and trains the model (a few minutes); after that it opens the app in its own window (Microsoft Edge
app mode). Close the minimized "PancRISK+ server" window to stop it. (Written for Windows 10/11; not tested on Windows by the author.)

**2. Put it online with free HTTPS (Hugging Face Space).** `space_bundle.zip` contains exactly the files to upload.
1. Create a free account at huggingface.co, then *New Space*: SDK **Docker** (Blank), hardware **CPU basic (free)**.
2. *Files* tab, *Add file*, *Upload files*: unzip `space_bundle.zip` and drag in what is **inside** it
   (`README.md`, `Dockerfile`, `requirements-app.txt`, `app/`, `src/`, `data/`), then commit.
3. Wait for *Building* to become *Running* (several minutes: it installs packages and trains the model).
4. Open the **direct address** `https://<username>-<space-name>.hf.space` (the preview inside the Hugging Face page is blank on purpose).

Free Spaces sleep when idle (first open is slow), and their disk is temporary: accounts and results vanish on restart. Fine for a demo,
not for real use. Rebuild the bundle after code changes with `python deploy/make_space_bundle.py`.

**3. Android app (APK).** Do step 2 first, then go to pwabuilder.com, paste your `hf.space` address, press *Start*, then *Package for
stores*, then *Android*. Choose the **signed** option so you get an installable `.apk` (inside the downloaded zip; keep the signing key
safe). Copy the `.apk` to your phone and install it (allow installs from your file manager). Without the extra "asset links" step the
app shows a browser address bar; to remove it, put the JSON PWABuilder gives you into a Space variable named `ASSETLINKS_JSON`
(the app serves it at `/.well-known/assetlinks.json`). Publishing on Google Play needs a paid developer account; sharing the APK is free.
The wrapper only displays your hosted app, so the Space must be running. Menus on those sites can change slightly over time.

**iPhone:** open the `hf.space` address in Safari, *Share*, *Add to Home Screen*.

## Project structure
```
data/            raw CSV + documentation (app.db and uploads are created at run time, git-ignored)
notebooks/       01_cleaning_eda_baseline.ipynb (EDA, 6-model comparison, calibration, decision curve, fairness)
src/             pipeline.py, calibration.py, train_final.py, predict.py, i18n.py, report.py
app/             server.py (patient app API), appdb.py, appsec.py, report_extract.py, static/ (the app UI + PWA files)
                 api.py + streamlit_app.py (earlier research demos)
models/          model.joblib (created by train_final.py)
reports/         SHAP plots, final_metrics.json
tests/           pytest suite (18 tests: model, languages, login, lockout, booking, privacy, uploads)
tests_ui/        simulated-browser walkthrough of the real screens (needs Node: npm install, then node ui_test.js)
start_windows_app.bat, deploy/ (Space bundle builder), Dockerfile, docker-compose.yml, MODEL_CARD.md
```

## How to run (Windows PowerShell, from the project folder)
```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe src\train_final.py                         # once, creates models/model.joblib for your library versions
.venv\Scripts\python.exe -m uvicorn app.server:app --reload          # then open http://localhost:8000
.venv\Scripts\python.exe -m pytest tests -q                          # 18 tests
```
On your phone (same Wi-Fi): run uvicorn with `--host 0.0.0.0`, find your PC's address with `ipconfig`, open `http://<that address>:8000`.
"Install app / Add to Home Screen" needs HTTPS, so for that deploy it to a free HTTPS host (set `APP_SECURE_COOKIES=1` and
a long random `APP_SECRET`). Free hosts with temporary disks will lose the demo database on restart.
`docker compose up --build` also works (Docker not tested here). The earlier research demo: `python -m streamlit run app/streamlit_app.py`.

## Roadmap
1. ✅ Dataset and setup  2. ✅ EDA  3. ✅ Baseline  4. ✅ Six-model comparison  5. ✅ Calibration, threshold, fairness
6. ✅ SHAP  7. ✅ FastAPI + Streamlit, multilingual (EN/HI/MR), HTML report  8. ✅ Docker, model card
Next: native-speaker review of Hindi/Marathi, more languages, external validation, imaging (CNN) module.

## Disclaimer
Academic research and education prototype. Not a medical device; must not be used for diagnosis or clinical decisions.
