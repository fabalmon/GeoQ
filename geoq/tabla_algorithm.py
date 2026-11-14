# -*- coding: utf-8 -*-
"""Herramienta de consulta: tabla de códigos de cobertura y Número de Curva.

Copyright (C) 2024 Fabio A. Montealegre M. & Fernanda J. Gaspari
CEIDE - UNLP - CIC. Licencia GNU GPL versión 2 o posterior.
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsFeature,
    QgsFeatureSink,
    QgsFields,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterFeatureSink,
)

from . import numero_curva
from .compat import campo_entero, campo_texto
from .geoq_algorithm import RUTA_ICONO, URL_AYUDA


class TablaNCAlgorithm(QgsProcessingAlgorithm):
    """Genera la tabla de códigos de cobertura con su Número de Curva."""

    SALIDA = 'TABLA'

    def name(self):
        return 'tablanc'

    def displayName(self):
        return self.tr('Tabla de códigos y Número de Curva')

    def shortDescription(self):
        return self.tr('Tabla de consulta con los códigos de cobertura de '
                       'GeoQ y su Número de Curva.')

    def shortHelpString(self):
        return self.tr(
            '<p>Crea una tabla de consulta con los códigos de cobertura '
            'vegetal y uso del suelo que utiliza GeoQ (<b>Cod_Veg</b>), su '
            'descripción y el Número de Curva que les corresponde para '
            'cada grupo hidrológico de suelo (A, B, C, D) y cada Condición '
            'de Humedad Antecedente (I, II, III).</p>'
            '<p>Sirve de guía para codificar la capa de cobertura antes de '
            'ejecutar GeoQ.</p>'
            '<p>Grupos hidrológicos (<b>Cod_Sue</b>): A = 1, B = 2, C = 3, '
            'D = 4.</p>')

    def icon(self):
        return QIcon(RUTA_ICONO)

    def helpUrl(self):
        return URL_AYUDA

    def tr(self, texto):
        return QCoreApplication.translate('GeoQ', texto)

    def createInstance(self):
        return TablaNCAlgorithm()

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFeatureSink(
            self.SALIDA, self.tr('Códigos de cobertura y Número de Curva'),
            QgsProcessing.SourceType.TypeVector))

    def processAlgorithm(self, parameters, context, feedback):
        campos = QgsFields()
        campos.append(campo_entero('Cod_Veg', 5))
        campos.append(campo_texto('Cobertura'))
        campos.append(campo_texto('Uso_suelo'))
        for grupo in numero_curva.GRUPOS_HIDROLOGICOS:
            for cha in numero_curva.CHA:
                campos.append(campo_entero('{}_{}'.format(grupo, cha), 3))

        sumidero, destino = self.parameterAsSink(
            parameters, self.SALIDA, context, campos,
            Qgis.WkbType.NoGeometry, QgsCoordinateReferenceSystem())
        if sumidero is None:
            raise QgsProcessingException(
                self.invalidSinkError(parameters, self.SALIDA))

        for codigo, valores in numero_curva.TABLA_NC.items():
            cobertura, uso = numero_curva.COBERTURAS[codigo]
            fila = QgsFeature(campos)
            fila.setAttributes([codigo, cobertura, uso] + list(valores))
            sumidero.addFeature(fila, QgsFeatureSink.Flag.FastInsert)
        return {self.SALIDA: destino}
