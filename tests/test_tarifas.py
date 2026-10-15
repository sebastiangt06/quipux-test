from datetime import datetime
import unittest

from app.config import TARIFA_BASE, VALOR_TRANSBORDO
from app.modelos import Perfil, SolicitudTarifa, Validacion
from app.tarifas import aplicar_descuento, calcular_tarifa


def test_general_no_tiene_descuento():
    assert aplicar_descuento(TARIFA_BASE, Perfil.GENERAL) == TARIFA_BASE
    assert aplicar_descuento(VALOR_TRANSBORDO, Perfil.GENERAL) == VALOR_TRANSBORDO
    assert aplicar_descuento(0, Perfil.GENERAL) == 0

def test_descuento_redondea_a_multiplo_de_50():
    assert aplicar_descuento(TARIFA_BASE, Perfil.ESTUDIANTE) % 50 == 0
    assert aplicar_descuento(TARIFA_BASE, Perfil.ADULTO_MAYOR) % 50 == 0


def test_descuentos_y_redondeo_mitad_exacta_hacia_arriba():
    # Tarifa base ($3.200):
    # - estudiante (35 % desc.): 3200 * 0.65 = 2080 -> 2100
    # - adulto_mayor (55 % desc.): 3200 * 0.45 = 1440 -> 1450
    assert aplicar_descuento(TARIFA_BASE, Perfil.ESTUDIANTE) == 2100
    assert aplicar_descuento(TARIFA_BASE, Perfil.ADULTO_MAYOR) == 1450

    # Primer transbordo ($500) produce mitades exactas entre múltiplos de $50:
    # - estudiante (35 % desc.): 500 * 0.65 = 325 -> mitad exacta entre 300 y 350 -> 350
    # - adulto_mayor (55 % desc.): 500 * 0.45 = 225 -> mitad exacta entre 200 y 250 -> 250
    assert aplicar_descuento(VALOR_TRANSBORDO, Perfil.ESTUDIANTE) == 350
    assert aplicar_descuento(VALOR_TRANSBORDO, Perfil.ADULTO_MAYOR) == 250


def test_primer_transbordo_segundo_gratis_y_viaje_siguiente():
    solicitud = SolicitudTarifa(
        tarjeta="T-CICLO-01",
        perfil=Perfil.GENERAL,
        validaciones=[
            Validacion(id="v1", estacion="E01", fecha_hora=datetime.fromisoformat("2025-03-10T08:00:00-05:00")),
            Validacion(id="v2", estacion="E02", fecha_hora=datetime.fromisoformat("2025-03-10T08:20:00-05:00")),
            Validacion(id="v3", estacion="E03", fecha_hora=datetime.fromisoformat("2025-03-10T08:50:00-05:00")),
            Validacion(id="v4", estacion="E04", fecha_hora=datetime.fromisoformat("2025-03-10T09:10:00-05:00")),
            Validacion(id="v5", estacion="E05", fecha_hora=datetime.fromisoformat("2025-03-10T09:40:00-05:00")),
        ],
    )
    respuesta = calcular_tarifa(solicitud)

    assert [(c.validacion_id, c.tipo, c.valor) for c in respuesta.cobros] == [
        ("v1", "tarifa", 3200),
        ("v2", "transbordo", 500),
        ("v3", "transbordo_gratis", 0),
        ("v4", "tarifa", 3200),
        ("v5", "transbordo", 500),
    ]
    assert respuesta.total == 7400


def test_limite_exacto_90_minutos_y_justo_despues():
    # Exactamente a los 90 minutos desde la primera validación del viaje sigue siendo transbordo
    solicitud_exacta = SolicitudTarifa(
        tarjeta="T-LIM-01",
        perfil=Perfil.GENERAL,
        validaciones=[
            Validacion(id="v1", estacion="E01", fecha_hora=datetime.fromisoformat("2025-03-10T07:00:00-05:00")),
            Validacion(id="v2", estacion="E02", fecha_hora=datetime.fromisoformat("2025-03-10T08:30:00-05:00")),
        ],
    )
    resp_exacta = calcular_tarifa(solicitud_exacta)
    assert [(c.validacion_id, c.tipo, c.valor) for c in resp_exacta.cobros] == [
        ("v1", "tarifa", 3200),
        ("v2", "transbordo", 500),
    ]
    assert resp_exacta.total == 3700

    # Un segundo después de los 90 minutos inicia un nuevo viaje
    solicitud_despues = SolicitudTarifa(
        tarjeta="T-LIM-02",
        perfil=Perfil.GENERAL,
        validaciones=[
            Validacion(id="v1", estacion="E01", fecha_hora=datetime.fromisoformat("2025-03-10T07:00:00-05:00")),
            Validacion(id="v2", estacion="E02", fecha_hora=datetime.fromisoformat("2025-03-10T08:30:01-05:00")),
        ],
    )
    resp_despues = calcular_tarifa(solicitud_despues)
    assert [(c.validacion_id, c.tipo, c.valor) for c in resp_despues.cobros] == [
        ("v1", "tarifa", 3200),
        ("v2", "tarifa", 3200),
    ]
    assert resp_despues.total == 6400


def test_ventana_se_mide_desde_primera_validacion_del_viaje():
    # v1 en t=0, v2 en t=60m (1er transbordo), v3 en t=100m (a 40m de v2 pero a 100m de v1 -> nuevo viaje)
    solicitud = SolicitudTarifa(
        tarjeta="T-VENTANA-01",
        perfil=Perfil.GENERAL,
        validaciones=[
            Validacion(id="v1", estacion="E01", fecha_hora=datetime.fromisoformat("2025-03-10T07:00:00-05:00")),
            Validacion(id="v2", estacion="E02", fecha_hora=datetime.fromisoformat("2025-03-10T08:00:00-05:00")),
            Validacion(id="v3", estacion="E03", fecha_hora=datetime.fromisoformat("2025-03-10T08:40:00-05:00")),
        ],
    )
    respuesta = calcular_tarifa(solicitud)
    assert [(c.validacion_id, c.tipo, c.valor) for c in respuesta.cobros] == [
        ("v1", "tarifa", 3200),
        ("v2", "transbordo", 500),
        ("v3", "tarifa", 3200),
    ]
    assert respuesta.total == 6900


def test_validaciones_fuera_de_orden_con_distintas_zonas_horarias():
    # b7c0 (11:58:27Z = 06:58:27-05:00) -> inicio viaje 1
    # b7c1 (07:41:12-05:00 = 12:41:12Z) -> transbordo viaje 1 (+42m 45s)
    # b7c2 (13:05:00-05:00 = 18:05:00Z) -> inicio viaje 2
    # b7c3 (18:30:40Z = 13:30:40-05:00) -> transbordo viaje 2 (+25m 40s)
    solicitud = SolicitudTarifa(
        tarjeta="T-118230",
        perfil=Perfil.ESTUDIANTE,
        validaciones=[
            Validacion(id="b7c2", estacion="E12", fecha_hora=datetime.fromisoformat("2025-03-10T13:05:00-05:00")),
            Validacion(id="b7c0", estacion="E03", fecha_hora=datetime.fromisoformat("2025-03-10T11:58:27+00:00")),
            Validacion(id="b7c1", estacion="E05", fecha_hora=datetime.fromisoformat("2025-03-10T07:41:12-05:00")),
            Validacion(id="b7c3", estacion="E12", fecha_hora=datetime.fromisoformat("2025-03-10T18:30:40+00:00")),
        ],
    )
    respuesta = calcular_tarifa(solicitud)
    assert [(c.validacion_id, c.tipo, c.valor) for c in respuesta.cobros] == [
        ("b7c0", "tarifa", 2100),
        ("b7c1", "transbordo", 350),
        ("b7c2", "tarifa", 2100),
        ("b7c3", "transbordo", 350),
    ]
    assert respuesta.total == 4900


class TestTarifasUnit(unittest.TestCase):
    def test_suite_tarifas(self):
        test_general_no_tiene_descuento()
        test_descuento_redondea_a_multiplo_de_50()
        test_descuentos_y_redondeo_mitad_exacta_hacia_arriba()
        test_primer_transbordo_segundo_gratis_y_viaje_siguiente()
        test_limite_exacto_90_minutos_y_justo_despues()
        test_ventana_se_mide_desde_primera_validacion_del_viaje()
        test_validaciones_fuera_de_orden_con_distintas_zonas_horarias()