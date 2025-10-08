#Dockerfile
# Builder + Runtime 
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
