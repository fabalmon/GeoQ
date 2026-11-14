#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Arma el ZIP de GeoQ listo para instalar en QGIS o subir al repositorio.

Uso:  python scripts/empaquetar.py

Genera ``dist/GeoQ-main.zip`` con el contenido de la carpeta ``geoq`` dentro
de una carpeta ``GeoQ-main``, que es el nombre con el que el complemento está
registrado en plugins.qgis.org (no se debe cambiar).
"""

import configparser
import os
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEN = os.path.join(RAIZ, 'geoq')
NOMBRE_PAQUETE = 'GeoQ-main'
EXCLUIR_CARPETAS = {'__pycache__'}
EXCLUIR_EXTENSIONES = ('.pyc', '.pyo')


def version():
    metadatos = configparser.ConfigParser()
    metadatos.read(os.path.join(ORIGEN, 'metadata.txt'), encoding='utf-8')
    return metadatos['general']['version']


def empaquetar():
    destino = os.path.join(RAIZ, 'dist')
    os.makedirs(destino, exist_ok=True)
    ruta_zip = os.path.join(destino, NOMBRE_PAQUETE + '.zip')
    archivos = []
    for carpeta, subcarpetas, nombres in os.walk(ORIGEN):
        subcarpetas[:] = sorted(
            s for s in subcarpetas
            if s not in EXCLUIR_CARPETAS and not s.startswith('.'))
        for nombre in sorted(nombres):
            if nombre.startswith('.') or nombre.endswith(EXCLUIR_EXTENSIONES):
                continue
            archivos.append(os.path.join(carpeta, nombre))
    with zipfile.ZipFile(ruta_zip, 'w', zipfile.ZIP_DEFLATED) as comprimido:
        for ruta in archivos:
            relativa = os.path.relpath(ruta, ORIGEN).replace(os.sep, '/')
            comprimido.write(ruta, NOMBRE_PAQUETE + '/' + relativa)
    return ruta_zip, len(archivos)


if __name__ == '__main__':
    ruta, cantidad = empaquetar()
    print('GeoQ {}: {} archivos en {}'.format(version(), cantidad, ruta))
