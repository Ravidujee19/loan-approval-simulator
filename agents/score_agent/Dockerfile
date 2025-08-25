FROM python:3.13.3-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY score_agent.py ./

EXPOSE 5002
CMD ["uvicorn", "score_agent:app", "--host", "0.0.0.0", "--port", "5002"]
