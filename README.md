# tarifas-t2

Servicio que calcula lo que se le cobra a una tarjeta por sus validaciones en
la Línea T2.

## Correr local

```
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux / macOS
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Documentación interactiva en http://localhost:8000/docs

## Tests

```
pytest
```

## Docker

```
docker compose up --build
```
