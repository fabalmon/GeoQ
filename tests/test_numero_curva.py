# -*- coding: utf-8 -*-
"""Pruebas de las tablas y fórmulas del Número de Curva (no requieren QGIS).

Se ejecutan con:  python -m pytest tests/test_numero_curva.py
"""

import importlib.util
import os

import pytest

# Se carga el módulo directamente desde su archivo para no depender de QGIS.
_RUTA = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'geoq', 'numero_curva.py')
_spec = importlib.util.spec_from_file_location('numero_curva', _RUTA)
nc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nc)


def test_tabla_completa():
    assert sorted(nc.TABLA_NC) == list(range(10, 590, 10))
    assert sorted(nc.COBERTURAS) == sorted(nc.TABLA_NC)
    for codigo, fila in nc.TABLA_NC.items():
        assert len(fila) == 12, codigo
        assert all(isinstance(v, int) and 0 < v <= 100 for v in fila), codigo


def test_nc_crece_con_la_humedad():
    """Para todo suelo y cobertura: NC(CHA I) <= NC(CHA II) <= NC(CHA III)."""
    for codigo in nc.TABLA_NC:
        for suelo in (1, 2, 3, 4):
            seco, medio, humedo = (
                nc.numero_curva(suelo, codigo, cha) for cha in (0, 1, 2))
            assert seco <= medio <= humedo, (codigo, suelo)


def test_ejemplo_del_manual():
    """Tabla 4 del manual: barbecho (Cod_Veg 10) en CHA II."""
    assert [nc.numero_curva(s, 10, 1) for s in (1, 2, 3, 4)] == [
        77, 86, 91, 94]


def test_valores_corregidos_440_y_550():
    """Valores indicados por el autor para la versión 2.9."""
    assert nc.TABLA_NC[440] == (40, 61, 78, 56, 75, 87, 67, 77, 84,
                                74, 83, 91)
    assert nc.TABLA_NC[550] == (80, 91, 96, 80, 91, 96, 81, 91, 96,
                                82, 92, 97)
    assert nc.numero_curva(4, 440, 1) == 83   # Cod_NC 444, CHA II
    assert nc.numero_curva(4, 550, 2) == 97   # Cod_NC 554, CHA III


@pytest.mark.parametrize('valor, esperado', [
    (1, 1), (4, 4), (2.0, 2), ('3', 3), (' b ', 2), ('D', 4), ('a', 1),
    (0, None), (5, None), ('E', None), (None, None), ('', None),
    (1.5, None), (float('nan'), None), ('NULL', None),
])
def test_codigo_suelo(valor, esperado):
    assert nc.codigo_suelo(valor) == esperado


@pytest.mark.parametrize('valor, esperado', [
    (10, 10), (580, 580), (250.0, 250), ('170', 170), (' 50 ', 50),
    (15, None), (0, None), (590, None), ('pastizal', None), (None, None),
])
def test_codigo_cobertura(valor, esperado):
    assert nc.codigo_cobertura(valor) == esperado


def test_balance_ejemplo():
    """NC 77 y una tormenta de 80,1 mm, calculado a mano."""
    b = nc.balance(77, 80.1)
    assert b['S'] == pytest.approx(75.8701, abs=1e-4)
    assert b['Io'] == pytest.approx(15.1740, abs=1e-4)
    assert b['Q'] == pytest.approx(29.9396, abs=1e-4)
    assert b['F'] == pytest.approx(34.9864, abs=1e-4)
    assert b['CE'] == pytest.approx(37.3778, abs=1e-4)


def test_balance_cierra():
    """P = Q + F + Io y CE + CF + CIo = 100, para cualquier NC y lluvia."""
    for numero in (3, 25, 55, 77, 91, 100):
        for pp in (0.5, 5, 20, 80.1, 250, 1000):
            b = nc.balance(numero, pp)
            assert b['CE'] + b['CF'] + b['CIo'] == pytest.approx(100)
            assert min(b.values()) >= 0
            if pp > b['Io']:
                assert b['Q'] + b['F'] + b['Io'] == pytest.approx(pp)
            else:
                assert b['Q'] == 0 and b['F'] == 0 and b['CIo'] == 100


def test_balance_casos_limite():
    # Lluvia igual a las abstracciones iniciales: todo queda retenido.
    io = nc.balance(77, 80.1)['Io']
    b = nc.balance(77, io)
    assert (b['Q'], b['F'], b['CE'], b['CF'], b['CIo']) == (0, 0, 0, 0, 100)
    # Sin lluvia no hay división por cero.
    b = nc.balance(77, 0)
    assert (b['Q'], b['CE'], b['CF']) == (0, 0, 0)
    # NC 100 (agua o superficie impermeable): escurre toda la lluvia.
    b = nc.balance(100, 50)
    assert b['S'] == 0 and b['Q'] == pytest.approx(50)
    assert b['CE'] == pytest.approx(100)
