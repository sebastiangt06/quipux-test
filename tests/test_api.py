import unittest
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

def test_validaciones_vacias_retorna_200_y_total_cero():
    r = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta" : "T-VACIA-001",
            "validaciones" : [],
        }
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo == {
        "tarjeta": "T-VACIA-001",
        "perfil" : "general",
        "cobros" : [],
        "total": 0,
    }

def test_perfil_omitido_usa_general():
    r = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-SIN-PERFIL-001",
            "validaciones": [
                {"id": "v1", "estacion": "E01", "fecha_hora": "2025-03-10T07:00:00-05:00"},
                {"id": "v2", "estacion": "E02", "fecha_hora": "2025-03-10T07:30:00-05:00"},
            ],
        },
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["perfil"] == "general"
    assert [c["valor"] for c in cuerpo["cobros"]] == [3200, 500]
    assert cuerpo["total"] == 3700


def test_validaciones_desordenadas_transbordos_y_descuentos_endpoint():
    r = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-ORDEN-001",
            "perfil": "adulto_mayor",
            "validaciones": [
                {"id": "v4", "estacion": "E04", "fecha_hora": "2025-03-10T09:30:01-05:00"},
                {"id": "v2", "estacion": "E02", "fecha_hora": "2025-03-10T08:15:00-05:00"},
                {"id": "v1", "estacion": "E01", "fecha_hora": "2025-03-10T08:00:00-05:00"},
                {"id": "v3", "estacion": "E03", "fecha_hora": "2025-03-10T09:30:00-05:00"},
            ],
        },
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert [(c["validacion_id"], c["tipo"], c["valor"]) for c in cuerpo["cobros"]] == [
        ("v1", "tarifa", 1450),
        ("v2", "transbordo", 250),
        ("v3", "transbordo_gratis", 0),
        ("v4", "tarifa", 1450),
    ]
    assert cuerpo["total"] == 3150


def test_rechaza_perfil_invalido_con_422():
    r = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-ERR-PERFIL",
            "perfil": "ejecutivo",
            "validaciones": [
                {"id": "v1", "estacion": "E01", "fecha_hora": "2025-03-10T07:00:00-05:00"}
            ],
        },
    )
    assert r.status_code == 422

def test_rechaza_fecha_sin_zona_horaria_con_422():
    r = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-ERR-TZ",
            "perfil": "general",
            "validaciones": [
                {"id": "v1", "estacion": "E01", "fecha_hora": "2025-03-10T07:00:00"}
            ],
        },
    )
    assert r.status_code == 422

def test_rechaza_identificadores_duplicados_con_422():
    r = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-ERR-DUP",
            "perfil": "general",
            "validaciones": [
                {"id": "v_dup", "estacion": "E01", "fecha_hora": "2025-03-10T07:00:00-05:00"},
                {"id": "v_dup", "estacion": "E02", "fecha_hora": "2025-03-10T07:20:00-05:00"},
            ],
        },
    )
    assert r.status_code == 422


def test_aislamiento_historial_entre_tarjetas_bug_17():
    r1 = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-AISLADA-A",
            "perfil": "general",
            "validaciones": [
                {"id": "a1", "estacion": "E01", "fecha_hora": "2025-03-10T06:00:00-05:00"}
            ],
        },
    )
    assert r1.status_code == 200

    r2 = cliente.post(
        "/tarifas/calcular",
        json={
            "tarjeta": "T-AISLADA-B",
            "perfil": "estudiante",
            "validaciones": [
                {"id": "b1", "estacion": "E02", "fecha_hora": "2025-03-10T07:00:00-05:00"},
                {"id": "b2", "estacion": "E03", "fecha_hora": "2025-03-10T07:30:00-05:00"},
            ],
        },
    )
    assert r2.status_code == 200

    hist_a = cliente.get("/tarjetas/T-AISLADA-A/historial").json()
    hist_b = cliente.get("/tarjetas/T-AISLADA-B/historial").json()
    hist_inexistente = cliente.get("/tarjetas/T-AISLADA-C/historial").json()

    assert len(hist_a) == 1
    assert all(item["tarjeta"] == "T-AISLADA-A" for item in hist_a)
    assert hist_a[0]["total"] == 3200

    assert len(hist_b) == 1
    assert all(item["tarjeta"] == "T-AISLADA-B" for item in hist_b)
    assert hist_b[0]["total"] == 2450

    assert hist_inexistente == []


