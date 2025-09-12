# syntax=docker/dockerfile:1
FROM python:3.11-slim

# 1) safer, cleaner python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# 2) workdir
WORKDIR /app

# 3) install deps
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 4) copy project files
COPY . /app

# 5) expose the port FastAPI will listen on
EXPOSE 8000

# 6) run the server
# Uses $PORT if a platform (Render/Fly/Cloud Run/etc.) sets it, else 8000 locally
CMD ["sh", "-c", "uvicorn app.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
