FROM python:3.11-slim

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install build tools required for python-multipart (and other libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first to break cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the application
COPY . .

# Fly.io expects apps on PORT=8080
ENV PORT=8080

# Use Gunicorn with Uvicorn workers
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]
