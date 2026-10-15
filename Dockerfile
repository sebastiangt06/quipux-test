FROM python:3.12-slim

WORKDIR /srv
COPY . .
RUN pip install --no-cache-dir --default-timeout=120 --retries=5 -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]