from app.config import TARIFA_BASE
from app.modelos import Perfil
from app.tarifas import aplicar_descuento


def test_general_no_tiene_descuento():
    assert aplicar_descuento(TARIFA_BASE, Perfil.GENERAL) == TARIFA_BASE


def test_descuento_redondea_a_multiplo_de_50():
    assert aplicar_descuento(TARIFA_BASE, Perfil.ESTUDIANTE) % 50 == 0
