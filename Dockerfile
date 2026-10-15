FROM python:3.12-slim

WORKDIR /srv
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--port", "8000"]
