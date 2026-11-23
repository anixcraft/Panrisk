"""Builds space_bundle/ (and space_bundle.zip): exactly the files to upload to a Hugging Face Docker Space.
Run from the project root:  python deploy/make_space_bundle.py"""
import os
import shutil
import zipfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "space_bundle")

README = """---
title: PancRISK+ Care
emoji: 🧬
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# PancRISK+ Care (research prototype)

Patient-style app: register/login, doctors, appointments, report upload and a **research-prototype**
pancreatic cancer risk estimate in English, Hindi and Marathi.

**Not a medical device. Not a diagnosis. Demo data only: do not enter real patient information.**
The Space disk is temporary: accounts and results are wiped whenever the Space restarts.

**Open the app at its direct address** `https://<username>-<space-name>.hf.space`. The preview inside the
Hugging Face page stays blank on purpose (the app blocks being framed, for security).
Model data: Debernardi et al. (2020), CC-BY.
"""

DOCKERFILE = """FROM python:3.11-slim
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH" PYTHONUNBUFFERED=1 \\
    APP_DB=/home/user/data/app.db APP_SECURE_COOKIES=1
RUN mkdir -p /home/user/app
WORKDIR /home/user/app
COPY --chown=user requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt
COPY --chown=user . .
# Train inside the image so the model always matches the installed library versions.
RUN python src/train_final.py
EXPOSE 7860
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "7860"]
"""

APP_FILES = ["__init__.py", "server.py", "appdb.py", "appsec.py", "report_extract.py"]
SRC_FILES = ["pipeline.py", "train_final.py", "predict.py", "i18n.py", "report.py"]


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    for d in ("app/static", "src", "data"):
        os.makedirs(os.path.join(OUT, d))
    for f in APP_FILES:
        shutil.copy(os.path.join(ROOT, "app", f), os.path.join(OUT, "app", f))
    for f in os.listdir(os.path.join(ROOT, "app", "static")):
        shutil.copy(os.path.join(ROOT, "app", "static", f), os.path.join(OUT, "app", "static", f))
    for f in SRC_FILES:
        shutil.copy(os.path.join(ROOT, "src", f), os.path.join(OUT, "src", f))
    for f in ("Debernardi_et_al_2020_data.csv", "Debernardi_et_al_2020_documentation.csv"):
        shutil.copy(os.path.join(ROOT, "data", f), os.path.join(OUT, "data", f))
    shutil.copy(os.path.join(ROOT, "requirements-app.txt"), os.path.join(OUT, "requirements-app.txt"))
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(README)
    with open(os.path.join(OUT, "Dockerfile"), "w", encoding="utf-8", newline="\n") as f:
        f.write(DOCKERFILE)
    zpath = OUT + ".zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for base, _, files in os.walk(OUT):
            for f in files:
                full = os.path.join(base, f)
                z.write(full, os.path.relpath(full, OUT))
    print("Created", os.path.abspath(OUT), "and", os.path.abspath(zpath))


if __name__ == "__main__":
    main()
