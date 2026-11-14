# -*- coding: utf-8 -*-
"""Pequeñas ayudas para que el mismo código funcione en QGIS 3 y QGIS 4.

Copyright (C) 2024 Fabio A. Montealegre M. & Fernanda J. Gaspari
Licencia GNU GPL versión 2 o posterior.
"""

from qgis.PyQt.QtCore import QMetaType, QVariant
from qgis.core import Qgis, QgsField, QgsProcessingParameterDefinition

# Desde QGIS 3.38 los campos se definen con QMetaType; antes, con QVariant.
if Qgis.QGIS_VERSION_INT >= 33800:
    _ENTERO = QMetaType.Type.Int
    _DECIMAL = QMetaType.Type.Double
    _TEXTO = QMetaType.Type.QString
else:
    _ENTERO = QVariant.Type.Int
    _DECIMAL = QVariant.Type.Double
    _TEXTO = QVariant.Type.String

# Marca de "parámetro avanzado" (cambió de lugar en QGIS 3.36).
try:
    PARAMETRO_AVANZADO = Qgis.ProcessingParameterFlag.Advanced
except AttributeError:
    PARAMETRO_AVANZADO = QgsProcessingParameterDefinition.Flag.FlagAdvanced


def campo_entero(nombre, longitud=10):
    return QgsField(nombre, _ENTERO, '', longitud, 0)


def campo_decimal(nombre, longitud=10, precision=2):
    return QgsField(nombre, _DECIMAL, '', longitud, precision)


def campo_texto(nombre, longitud=150):
    return QgsField(nombre, _TEXTO, '', longitud, 0)
