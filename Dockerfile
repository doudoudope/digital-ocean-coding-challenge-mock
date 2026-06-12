FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

RUN mkdir -p /app/uploads /app/data

ENV DATABASE_URL=sqlite:////app/data/documents.db
ENV UPLOAD_DIR=/app/uploads
ENV MAX_FILE_SIZE_MB=10

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
