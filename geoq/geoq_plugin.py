# -*- coding: utf-8 -*-
"""Integración de GeoQ con la interfaz de QGIS (menú, botón y proveedor).

Copyright (C) 2024 Fabio A. Montealegre M. & Fernanda J. Gaspari
CEIDE - UNLP - CIC. Licencia GNU GPL versión 2 o posterior.
"""

from qgis.PyQt.QtGui import QAction, QIcon
from qgis.core import QgsApplication
import processing

from .geoq_algorithm import RUTA_ICONO
from .geoq_provider import GeoQProvider

MENU = '&GeoQ'


class GeoQPlugin:

    def __init__(self, iface):
        self.iface = iface
        self.provider = None
        self.acciones = []

    def initProcessing(self):
        """Registra las herramientas de GeoQ en la Caja de herramientas."""
        self.provider = GeoQProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()
        self._agregar_accion('GeoQ: escorrentía superficial',
                             'geoq:escorrentia', en_barra=True)
        self._agregar_accion('Tabla de códigos y Número de Curva',
                             'geoq:tablanc', en_barra=False)

    def unload(self):
        for accion in self.acciones:
            self.iface.removePluginMenu(MENU, accion)
            self.iface.removeToolBarIcon(accion)
        self.acciones = []
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None

    def _agregar_accion(self, texto, algoritmo, en_barra):
        accion = QAction(QIcon(RUTA_ICONO), texto, self.iface.mainWindow())
        accion.triggered.connect(
            lambda _marcado=False: processing.execAlgorithmDialog(algoritmo))
        self.iface.addPluginToMenu(MENU, accion)
        if en_barra:
            self.iface.addToolBarIcon(accion)
        self.acciones.append(accion)
