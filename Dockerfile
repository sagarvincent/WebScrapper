# One image, two entry points (web via gunicorn, worker via worker.py).
# Selenium/Chromium is intentionally NOT installed: the default fetch path is
# requests-only. Add a browser layer here only if fetch_js() becomes required.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Default to the web tier. The worker Deployment overrides this with:
#   command: ["python", "worker.py"]
# Web is stateless now, so multiple gunicorn workers are safe.
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "--access-logfile", "-", "app:app"]
