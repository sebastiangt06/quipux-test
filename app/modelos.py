from datetime import datetime
from enum import Enum

from pydantic import BaseModel

try:
    from pydantic import field_validator as _validar_campo
except ImportError:
    from pydantic import validator as _validar_campo


class Perfil(str, Enum):
    GENERAL = "general"
    ESTUDIANTE = "estudiante"
    ADULTO_MAYOR = "adulto_mayor"


class Validacion(BaseModel):
    id: str
    estacion: str
    fecha_hora: datetime

    @_validar_campo("fecha_hora")
    def validar_zona_horaria(cls, valor: datetime) -> datetime:
        if valor.tzinfo is None or valor.tzinfo.utcoffset(valor) is None:
            raise ValueError("fecha_hora debe incluir zona horaria")
        return valor


class SolicitudTarifa(BaseModel):
    tarjeta: str
    perfil: Perfil = Perfil.GENERAL
    validaciones: list[Validacion]

    @_validar_campo("validaciones")
    def validar_ids_unicos(cls, validaciones : list[Validacion]) -> list[Validacion]:
        ids = [v.id for v in validaciones]
        if len(ids) != len(set(ids)):
            raise ValueError("Los identificadores de validación no pueden estar duplicados")
        return validaciones


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
