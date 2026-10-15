from fastapi import FastAPI

from app.historial import obtener_historial
from app.modelos import RespuestaTarifa, SolicitudTarifa
from app.tarifas import calcular_tarifa

app = FastAPI(title="Tarifas Línea T2", version="0.3.0")


@app.get("/salud")
def salud() -> dict[str, str]:
    return {"estado": "ok"}


@app.post("/tarifas/calcular", response_model=RespuestaTarifa)
def calcular(solicitud: SolicitudTarifa) -> RespuestaTarifa:
    respuesta = calcular_tarifa(solicitud)
    obtener_historial(solicitud.tarjeta).registrar(respuesta)
    return respuesta


@app.get("/tarjetas/{tarjeta}/historial", response_model=list[RespuestaTarifa])
def historial(tarjeta: str) -> list[RespuestaTarifa]:
    return obtener_historial(tarjeta).listar()
