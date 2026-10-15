from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class Perfil(str, Enum):
    GENERAL = "general"
    ESTUDIANTE = "estudiante"
    ADULTO_MAYOR = "adulto_mayor"


class Validacion(BaseModel):
    id: str
    estacion: str
    fecha_hora: datetime


class SolicitudTarifa(BaseModel):
    tarjeta: str
    perfil: Perfil = Perfil.GENERAL
    validaciones: list[Validacion]


class Cobro(BaseModel):
    validacion_id: str
    fecha_hora: datetime
    tipo: str
    valor: int


class RespuestaTarifa(BaseModel):
    tarjeta: str
    perfil: Perfil
    cobros: list[Cobro]
    total: int
