# -*- coding: utf-8 -*-
"""Configuración común de las pruebas de GeoQ."""

import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')


@pytest.fixture(scope='session')
def qgis():
    """Inicia QGIS sin interfaz, con Procesos y el proveedor de GeoQ."""
    core = pytest.importorskip('qgis.core')
    aplicacion = core.QgsApplication([], False)
    aplicacion.initQgis()
    # Carpeta de los complementos que vienen con QGIS (Procesos)
    for carpeta in (
            os.path.join(core.QgsApplication.pkgDataPath(), 'python',
                         'plugins'),
            '/usr/share/qgis/python/plugins'):
        if os.path.isdir(carpeta) and carpeta not in sys.path:
            sys.path.append(carpeta)
    from processing.core.Processing import Processing
    Processing.initialize()
    from geoq.geoq_provider import GeoQProvider
    proveedor = GeoQProvider()
    core.QgsApplication.processingRegistry().addProvider(proveedor)
    yield aplicacion
    core.QgsApplication.processingRegistry().removeProvider(proveedor)
    aplicacion.exitQgis()


@pytest.fixture(scope='session')
def datos(qgis, tmp_path_factory):
    """Rutas de las capas de prueba (ver datos_prueba.py)."""
    import datos_prueba
    return datos_prueba.crear_casos(str(tmp_path_factory.mktemp('datos')))
