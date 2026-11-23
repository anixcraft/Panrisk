FROM python:3.11-slim
WORKDIR /app
COPY requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt
COPY src ./src
COPY app ./app
COPY data ./data
# Train inside the image so the model matches the installed library versions.
RUN python src/train_final.py
ENV APP_DB=/data/app.db
VOLUME /data
EXPOSE 8000
# Behind HTTPS also set: -e APP_SECURE_COOKIES=1 -e APP_SECRET=<long random string>
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
