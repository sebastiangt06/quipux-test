"""Parámetros tarifarios vigentes de la Línea T2.

Valores en pesos colombianos. Los descuentos están en porcentaje.
"""

TARIFA_BASE = 3200
VALOR_TRANSBORDO = 500
VENTANA_TRANSBORDO_MIN = 90
MULTIPLO_REDONDEO = 50

DESCUENTOS = {
    "general": 0,
    "estudiante": 35,
    "adulto_mayor": 55,
}
