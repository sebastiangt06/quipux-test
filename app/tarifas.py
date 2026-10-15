"""Cálculo de lo que se le cobra a una tarjeta por sus validaciones."""

from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from app.config import (DESCUENTOS, MAX_TRANSBORDOS_POR_VIAJE, MULTIPLO_REDONDEO, TARIFA_BASE, VALOR_TRANSBORDO, VENTANA_TRANSBORDO_MIN)
from app.modelos import Cobro, Perfil, RespuestaTarifa, SolicitudTarifa


def aplicar_descuento(valor: int, perfil: Perfil) -> int:
    """Aplica el descuento del perfil y redondea al múltiplo de 50 más cercano.
    (mitad hacia arriba)."""
    if valor == 0:
        return 0
    porcentaje_descuento = Decimal(str(DESCUENTOS[perfil.value]))
    multiplo = Decimal(str(MULTIPLO_REDONDEO))
    valor_con_descuento = Decimal(valor) * (Decimal(100) - porcentaje_descuento) / Decimal(100)
    multiplos = (valor_con_descuento / multiplo).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(multiplos * multiplo)


def calcular_tarifa(solicitud: SolicitudTarifa) -> RespuestaTarifa:
    """Calcula los cobros aplicando las reglas de tarifa integrada."""
    if not solicitud.validaciones:
        return RespuestaTarifa(
            tarjeta=solicitud.tarjeta,
            perfil=solicitud.perfil,
            cobros=[],
            total=0,
        )

    # Las validaciones pueden llegar desordenadas; procesar en orden cronológico.
    validaciones_ordenadas = sorted(solicitud.validaciones, key=lambda v: v.fecha_hora)

    cobros: list[Cobro] = []
    inicio_viaje = None
    transbordos_en_viaje = 0
    ventana_limite = timedelta(minutes=VENTANA_TRANSBORDO_MIN)

    for val in validaciones_ordenadas:
        if (
            inicio_viaje is None
            or (val.fecha_hora - inicio_viaje) > ventana_limite
            or transbordos_en_viaje >= MAX_TRANSBORDOS_POR_VIAJE
        ):
            # Inicia un viaje nuevo: tarifa base
            inicio_viaje = val.fecha_hora
            transbordos_en_viaje = 0
            tipo = "tarifa"
            valor = aplicar_descuento(TARIFA_BASE, solicitud.perfil)
        elif transbordos_en_viaje == 0:
            # Primer transbordo dentro de la ventana de 90 min
            transbordos_en_viaje = 1
            tipo = "transbordo"
            valor = aplicar_descuento(VALOR_TRANSBORDO, solicitud.perfil)
        else:
            # Segundo transbordo dentro de la ventana de 90 min: gratis
            transbordos_en_viaje = 2
            tipo = "transbordo_gratis"
            valor = 0

        cobros.append(
            Cobro(
                validacion_id=val.id,
                fecha_hora=val.fecha_hora,
                tipo=tipo,
                valor=valor,
            )
        )

    total = sum(c.valor for c in cobros)
    return RespuestaTarifa(
        tarjeta=solicitud.tarjeta,
        perfil=solicitud.perfil,
        cobros=cobros,
        total=total,
    )
