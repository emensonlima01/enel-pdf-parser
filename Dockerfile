ARG PYTHON_VERSION=3.11.9
FROM python:${PYTHON_VERSION}-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000 \
    WEB_CONCURRENCY=1 \
    WEB_THREADS=1 \
    GUNICORN_TIMEOUT=300 \
    PADDLE_PDX_MODEL_SOURCE=BOS \
    PDF_DPI=300 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libopenblas0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY src ./src

RUN python -c "from src.ocr.engine import init_ocr; init_ocr()"

EXPOSE 8000

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-1} --threads ${WEB_THREADS:-1} --timeout ${GUNICORN_TIMEOUT:-300} src.api:app"]
