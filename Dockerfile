FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --timeout 120 --retries 10 -r requirements.txt

COPY . .

ENV PYTHONPATH="${PYTHONPATH}:/app"

CMD ["python", "image_assessment_service/cli.py", "--config", "/app/config.yaml"]