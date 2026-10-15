"""Historial en memoria de los cálculos hechos por tarjeta.

Es temporal: cuando tengamos base de datos esto se reemplaza.
"""

from app.modelos import RespuestaTarifa


class HistorialTarjeta:
    calculos: list[RespuestaTarifa] = []

    def __init__(self, tarjeta: str):
        self.tarjeta = tarjeta

    def registrar(self, respuesta: RespuestaTarifa) -> None:
        self.calculos.append(respuesta)

    def listar(self) -> list[RespuestaTarifa]:
        return list(self.calculos)


_historiales: dict[str, HistorialTarjeta] = {}


def obtener_historial(tarjeta: str) -> HistorialTarjeta:
    if tarjeta not in _historiales:
        _historiales[tarjeta] = HistorialTarjeta(tarjeta)
    return _historiales[tarjeta]
