from fastapi.testclient import TestClient

from app.config import TARIFA_BASE
from app.main import app

cliente = TestClient(app)


def test_salud():
    r = cliente.get("/salud")
    assert r.status_code == 200
    assert r.json() == {"estado": "ok"}


def test_una_validacion_paga_tarifa_completa():
    r = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-TEST-001",
            "perfil": "general",
            "validaciones": [
                {"id": "v1", "estacion": "E01", "fecha_hora": "2025-03-10T07:12:00-05:00"}
            ],
        },
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["total"] == TARIFA_BASE
    assert cuerpo["cobros"][0]["tipo"] == "tarifa"


def test_historial_registra_el_calculo():
    cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-TEST-002",
            "validaciones": [
                {"id": "v1", "estacion": "E04", "fecha_hora": "2025-03-10T09:00:00-05:00"}
            ],
        },
    )
    r = cliente.get("/tarjetas/T-TEST-002/historial")
    assert r.status_code == 200
    assert len(r.json()) >= 1
