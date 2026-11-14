# -*- coding: utf-8 -*-
"""Proveedor de Procesos de GeoQ.

Copyright (C) 2024 Fabio A. Montealegre M. & Fernanda J. Gaspari
CEIDE - UNLP - CIC. Licencia GNU GPL versión 2 o posterior.
"""

from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsProcessingProvider

from .geoq_algorithm import RUTA_ICONO, GeoQAlgorithm
from .tabla_algorithm import TablaNCAlgorithm


class GeoQProvider(QgsProcessingProvider):

    def id(self):
        return 'geoq'

    def name(self):
        return 'GeoQ'

    def icon(self):
        return QIcon(RUTA_ICONO)

    def loadAlgorithms(self):
        self.addAlgorithm(GeoQAlgorithm())
        self.addAlgorithm(TablaNCAlgorithm())
