FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

RUN mkdir -p data/input data/output data/success data/error data/logs

CMD ["python", "-m", "src.main"]
