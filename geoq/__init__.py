# -*- coding: utf-8 -*-
"""GeoQ: escorrentía superficial con el método del Número de Curva.

Complemento de QGIS desarrollado en el CEIDE (UNLP - CIC).

Copyright (C) 2024 Fabio A. Montealegre M. & Fernanda J. Gaspari

Este programa es software libre; puede redistribuirlo y/o modificarlo bajo
los términos de la Licencia Pública General de GNU publicada por la Free
Software Foundation, versión 2 o (a su elección) cualquier versión posterior.
"""


def classFactory(iface):
    """Punto de entrada que QGIS llama al cargar el complemento."""
    from .geoq_plugin import GeoQPlugin
    return GeoQPlugin(iface)
