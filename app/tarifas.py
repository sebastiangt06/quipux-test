"""Cálculo de lo que se le cobra a una tarjeta por sus validaciones."""

from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app.config import (DESCUENTOS, MULTIPLO_REDONDEO, TARIFA_BASE, VALOR_TRANSBORDO, VENTANA_TRANSBORDO_MIN)
from app.modelos import Cobro, Perfil, RespuestaTarifa, SolicitudTarifa


def aplicar_descuento(valor: int, perfil: Perfil) -> int:
    """Aplica el descuento del perfil y redondea al múltiplo de 50 más cercano.
    (mitad hacia arriba)."""
    if valor == 0:
        return 0
    porcentaje_descuento = Decimal(str(DESCUENTOS[perfil.value]))
    multiplo = Decimal(str(MULTIPLO_REDONDEO))
    valor_con_descuento = Decimal(valor) * (Decimal(100) - porcentaje_descuento) / Decimal(100)
    multiplos = (valor_con_descuento / multiplo).quantize(Decimal("1"), roundng=ROUND_HALF_UP)
    return int(multiplos * multiplo)


def calcular_tarifa(solicitud: SolicitudTarifa) -> RespuestaTarifa:
    # Por ahora cada validación paga la tarifa completa.
    ventana_transbordo = timedelta(minutes=VENTANA_TRANSBORDO_MIN)
    validaciones_ordenadas = sorted(solicitud.validaciones, key=lambda v: v.fecha_hora)
    cobros = list[Cobro] = []
    inicio_viaje: datetime | None = None
    transbordos_en_viaje = 0
    for validacion in solicitud.validaciones:
        en_ventana = (
            inicio_viaje is not None
            and (validacion.fecha_hora - inicio_viaje) <= ventana_transbordo
        )

        if not en_ventana or transbordos_en_viaje >= 2:
            inicio_viaje = validacion.fecha_hora
            transbordos_en_viaje = 0
            tipo = "tarifa"
            valor_base = TARIFA_BASE
        elif transbordos_en_viaje == 0:
            transbordos_en_viaje = 1
            tipo = "transbordo"
            valor_base = VALOR_TRANSBORDO
        else:
            transbordos_en_viaje = 2
            tipo = "transbordo_gratis"
            valor_base = 0
        cobros.append(
            Cobro(
                validacion_id=validacion.id,
                fecha_hora=validacion.fecha_hora,
                tipo=tipo,
                valor=aplicar_descuento(valor_base, solicitud.perfil),
            )
        )

    total = sum(c.valor for c in cobros)
    return RespuestaTarifa(
        tarjeta=solicitud.tarjeta,
        perfil=solicitud.perfil,
        cobros=cobros,
        total=total,
    )
