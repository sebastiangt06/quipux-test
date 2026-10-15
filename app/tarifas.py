"""Cálculo de lo que se le cobra a una tarjeta por sus validaciones."""

from app.config import DESCUENTOS, MULTIPLO_REDONDEO, TARIFA_BASE
from app.modelos import Cobro, Perfil, RespuestaTarifa, SolicitudTarifa


def aplicar_descuento(valor: int, perfil: Perfil) -> int:
    """Aplica el descuento del perfil y redondea al múltiplo de 50 más cercano."""
    descuento = DESCUENTOS[perfil.value] / 100
    valor_con_descuento = valor * (1 - descuento)
    return round(valor_con_descuento / MULTIPLO_REDONDEO) * MULTIPLO_REDONDEO


def calcular_tarifa(solicitud: SolicitudTarifa) -> RespuestaTarifa:
    # Por ahora cada validación paga la tarifa completa.
    cobros = []
    for validacion in solicitud.validaciones:
        cobros.append(
            Cobro(
                validacion_id=validacion.id,
                fecha_hora=validacion.fecha_hora,
                tipo="tarifa",
                valor=aplicar_descuento(TARIFA_BASE, solicitud.perfil),
            )
        )

    total = sum(c.valor for c in cobros)
    return RespuestaTarifa(
        tarjeta=solicitud.tarjeta,
        perfil=solicitud.perfil,
        cobros=cobros,
        total=total,
    )
