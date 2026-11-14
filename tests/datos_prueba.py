# -*- coding: utf-8 -*-
"""Capas auxiliares para las pruebas de GeoQ.

A partir de los datos de ``Test_data.zip`` (suelos y vegetación de la cuenca
del río Napaleofú) genera los límites de área de estudio y un ráster
sintético de precipitación que usan las pruebas automáticas.
"""

import os
import struct
import zipfile

from osgeo import gdal, osr
from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsFields,
    QgsGeometry,
    QgsProject,
    QgsVectorFileWriter,
    QgsVectorLayer,
)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Tres polígonos dentro de la cuenca de prueba (coordenadas POSGAR 2007 / 5)
POLIGONOS = [
    'Polygon((5584000 5830000, 5590000 5828500, 5597000 5831000, '
    '5601000 5836000, 5598500 5842000, 5591000 5845000, 5585500 5841000, '
    '5583000 5835000, 5584000 5830000))',
    'Polygon((5602500 5843000, 5605500 5843000, 5605500 5845500, '
    '5602500 5845500, 5602500 5843000))',
    'Polygon((5601500 5829000, 5606000 5829000, 5606000 5833000, '
    '5601500 5833000, 5601500 5829000))',
]


def _guardar(ruta, geometrias, crs):
    opciones = QgsVectorFileWriter.SaveVectorOptions()
    opciones.driverName = 'GPKG'
    escritor = QgsVectorFileWriter.create(
        ruta, QgsFields(), Qgis.WkbType.MultiPolygon, crs,
        QgsProject.instance().transformContext(), opciones)
    for geometria in geometrias:
        entidad = QgsFeature()
        entidad.setGeometry(geometria)
        escritor.addFeature(entidad)
    del escritor


def _raster(ruta, extension, resolucion):
    """Ráster WGS84 con un gradiente de lluvia y tres píxeles especiales."""
    x0 = (int(extension.xMinimum() / resolucion) - 1) * resolucion
    y1 = (int(extension.yMaximum() / resolucion) + 1) * resolucion
    columnas = int((extension.xMaximum() - x0) / resolucion) + 2
    filas = int((y1 - extension.yMinimum()) / resolucion) + 2
    datos = gdal.GetDriverByName('GTiff').Create(
        ruta, columnas, filas, 1, gdal.GDT_Float32)
    datos.SetGeoTransform((x0, resolucion, 0, y1, 0, -resolucion))
    wgs84 = osr.SpatialReference()
    wgs84.ImportFromEPSG(4326)
    datos.SetProjection(wgs84.ExportToWkt())
    banda = datos.GetRasterBand(1)
    banda.SetNoDataValue(-9999)
    for fila in range(filas):
        valores = [round(20 + 95.0 * c / columnas + 43.75 * fila / filas, 2)
                   for c in range(columnas)]
        if fila == 2 * filas // 7:
            valores[3 * columnas // 10] = -9999   # píxel sin dato
        if fila == 3 * filas // 7:
            valores[4 * columnas // 10] = 0.0     # píxel sin lluvia
        if fila == 4 * filas // 7:
            valores[2 * columnas // 10] = 5.0     # lluvia menor que Io
        banda.WriteRaster(0, fila, columnas, 1,
                          struct.pack('{}f'.format(columnas), *valores))
    datos.FlushCache()
    del banda, datos


def crear_casos(carpeta):
    """Crea los datos de prueba en ``carpeta`` y devuelve sus rutas."""
    with zipfile.ZipFile(os.path.join(RAIZ, 'Test_data.zip')) as comprimido:
        comprimido.extractall(carpeta)
    rutas = {
        'suelos': os.path.join(carpeta, 'Test_Suelos.gpkg'),
        'cobertura': os.path.join(carpeta, 'Test_Vegetacion.gpkg'),
    }
    suelos = QgsVectorLayer(rutas['suelos'], 'suelos', 'ogr')
    crs = suelos.crs()
    wgs84 = QgsCoordinateReferenceSystem('EPSG:4326')
    a_wgs84 = QgsCoordinateTransform(
        crs, wgs84, QgsProject.instance().transformContext())

    partes = [QgsGeometry.fromWkt(wkt) for wkt in POLIGONOS]
    # Límite con tres entidades de una sola parte
    rutas['limite'] = os.path.join(carpeta, 'limite.gpkg')
    _guardar(rutas['limite'], partes, crs)
    # El mismo límite en coordenadas geográficas
    geograficas = [QgsGeometry(parte) for parte in partes]
    for geometria in geograficas:
        geometria.transform(a_wgs84)
    rutas['limite_wgs84'] = os.path.join(carpeta, 'limite_wgs84.gpkg')
    _guardar(rutas['limite_wgs84'], geograficas, wgs84)
    # El mismo límite con una entidad multiparte (dos partes) y otra simple
    rutas['limite_multiparte'] = os.path.join(carpeta, 'limite_multi.gpkg')
    _guardar(rutas['limite_multiparte'],
             [QgsGeometry.collectGeometry(partes[:2]), partes[2]], crs)

    extension = a_wgs84.transformBoundingBox(suelos.extent())
    rutas['raster'] = os.path.join(carpeta, 'pp_wgs84.tif')
    _raster(rutas['raster'], extension, 0.04)
    rutas['raster_fino'] = os.path.join(carpeta, 'pp_fino_wgs84.tif')
    _raster(rutas['raster_fino'], extension, 0.002)
    return rutas
