FROM python:3.13.3-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY applicant_evaluator.py ./

# Expose port
EXPOSE 5001

# Start app with Uvicorn
CMD ["uvicorn", "applicant_evaluator:app", "--host", "0.0.0.0", "--port", "5001"]
