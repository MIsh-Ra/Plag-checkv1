FROM python:3.10-slim

# Install system dependencies, including Tesseract and Poppler for OCR
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Adjust as necessary if uvicorn needs different parameters or for celery
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
