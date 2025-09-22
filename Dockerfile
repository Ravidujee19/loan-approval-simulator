#Dockerfile
# ---------- Builder + Runtime ----------
FROM python:3.11-slim

# Avoid writing .pyc files and enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /srv

# Install build tools if needed
RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy app code and example env
COPY agents/ agents/
COPY example.env .

# Expose the port
EXPOSE 8000

# Run uvicorn
CMD ["python", "-m", "uvicorn", "agents.applicant_evaluator.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]

# version 2
# # ---------- Builder ----------
# FROM python:3.11-slim AS builder
# ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*
# WORKDIR /app

# COPY requirements.txt .
# # Build wheels into /wheels
# RUN pip install --upgrade pip \
#  && pip wheel --no-cache-dir --no-deps -r requirements.txt -w /wheels


# # ---------- Runtime ----------
# # FROM gcr.io/distroless/python3.11-debian12:nonroot
# FROM gcr.io/distroless/python3-debian12:nonroot



# ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# WORKDIR /srv

# # Copy wheels + install them into site-packages location
# COPY --from=builder /wheels /wheels
# COPY --from=builder /app/requirements.txt .
# # Instead of running pip, copy wheels directly into Python's site-packages
# COPY --from=builder /usr/local /usr/local

# # Copy your code
# COPY agents/ agents/
# COPY example.env /srv/example.env

# # Runtime settings
# ENV PATH="/srv/.local/bin:${PATH}"
# EXPOSE 8000
# USER nonroot
# VOLUME ["/srv/var"]
# ENV TMPDIR=/srv/var

# # Use uvicorn with module path
# CMD ["python", "-m", "uvicorn", "agents.applicant_evaluator.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]




# ---------- Builder ----------
# FROM python:3.12-slim AS builder
# ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# RUN apt-get update && apt-get install -y --no-install-recommends build-essential gcc && rm -rf /var/lib/apt/lists/*
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --upgrade pip && pip wheel --no-cache-dir --no-deps -r requirements.txt -w /wheels

# # ---------- Runtime ----------
# FROM gcr.io/distroless/python3-debian12:nonroot
# ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
# WORKDIR /srv
# COPY --from=builder /wheels /wheels
# COPY requirements.txt .
# RUN python -m pip install --no-deps --no-index -f /wheels -r requirements.txt
# COPY agents/ agents/
# COPY example.env /srv/example.env
# ENV PATH="/srv/.local/bin:${PATH}"
# EXPOSE 8000
# USER nonroot
# # Read-only FS with a small writable temp dir
# VOLUME ["/srv/var"]
# ENV TMPDIR=/srv/var
# CMD ["-m","uvicorn","agents.applicant_evaluator.app.main:app","--host","0.0.0.0","--port","8000","--proxy-headers","--forwarded-allow-ips","*"]
