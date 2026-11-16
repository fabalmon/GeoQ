# -*- coding: utf-8 -*-
"""Algoritmo principal de GeoQ: escorrentía superficial por Número de Curva.

Copyright (C) 2024 Fabio A. Montealegre M. & Fernanda J. Gaspari
CEIDE - UNLP - CIC. Licencia GNU GPL versión 2 o posterior.
"""

import math
import os

from qgis.PyQt import sip
from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.core import (
    Qgis,
    QgsCoordinateTransform,
    QgsDistanceArea,
    QgsFeature,
    QgsFeatureSink,
    QgsFields,
    QgsGeometry,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingLayerPostProcessorInterface,
    QgsProcessingMultiStepFeedback,
    QgsProcessingOutputNumber,
    QgsProcessingParameterBand,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
    QgsProcessingUtils,
    QgsRectangle,
    QgsVectorLayer,
)
import processing

from . import numero_curva
from .compat import PARAMETRO_AVANZADO, campo_decimal, campo_entero

CARPETA = os.path.dirname(__file__)
RUTA_ICONO = os.path.join(CARPETA, 'icon.png')
URL_AYUDA = 'https://github.com/fabalmon/GeoQ'

# Filas del ráster de precipitación que se leen por vez.
FILAS_POR_BLOQUE = 256
# A partir de esta cantidad de píxeles se avisa que el proceso será lento.
PIXELES_AVISO = 2000000


def _definido(valor):
    """Indica si un parámetro opcional fue cargado por el usuario."""
    if valor is None:
        return False
    if hasattr(valor, 'isNull') and valor.isNull():
        return False
    return not (isinstance(valor, str) and valor.strip() == '')


def _a_numero(valor):
    """Convierte un atributo en número real; None si es nulo o no numérico."""
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return numero if math.isfinite(numero) else None


class AplicarEstilo(QgsProcessingLayerPostProcessorInterface):
    """Carga un archivo de estilo .qml cuando la capa se agrega al proyecto.

    QGIS usa cada objeto una sola vez y luego lo elimina. Por eso se crea
    uno nuevo para cada capa en cada ejecución (ver ``nuevo``) y se guarda
    una referencia hasta que QGIS lo haya utilizado.
    """

    _pendientes = []

    def __init__(self, ruta_qml):
        super().__init__()
        self.ruta_qml = ruta_qml

    @classmethod
    def nuevo(cls, ruta_qml):
        # Se descartan los que QGIS ya utilizó y eliminó en otras ejecuciones
        cls._pendientes = [p for p in cls._pendientes if not sip.isdeleted(p)]
        procesador = cls(ruta_qml)
        cls._pendientes.append(procesador)
        return procesador

    def postProcessLayer(self, layer, context, feedback):
        if isinstance(layer, QgsVectorLayer) and os.path.exists(self.ruta_qml):
            layer.loadNamedStyle(self.ruta_qml)
            layer.triggerRepaint()


class GeoQAlgorithm(QgsProcessingAlgorithm):
    """Cálculo de la escorrentía superficial con el método del Número de Curva.

    Cruza el grupo hidrológico de suelos con la cobertura vegetal dentro del
    área de estudio, asigna el Número de Curva según la condición de humedad
    antecedente y calcula S, Io, Q, F y los coeficientes CE, CF y CIo.
    """

    # Parámetros de entrada
    LIMITE = 'LIMITE'
    SUELOS = 'SUELOS'
    CAMPO_SUELOS = 'CAMPO_SUELOS'
    COBERTURA = 'COBERTURA'
    CAMPO_COBERTURA = 'CAMPO_COBERTURA'
    CHA = 'CHA'
    PRECIPITACION = 'PRECIPITACION'
    RASTER = 'RASTER_PRECIPITACION'
    BANDA = 'BANDA_PRECIPITACION'
    # Capas de salida
    SALIDA_GEOQ = 'GEOQ'
    SALIDA_NC = 'NC'
    SALIDA_CE = 'CE'
    SALIDA_CF = 'CF'
    SALIDA_CIO = 'CIO'
    # Resumen numérico
    AREA_HA = 'AREA_HA'
    NC_PONDERADO = 'NC_PONDERADO'
    PP_MEDIA = 'PP_MEDIA_MM'
    Q_MEDIA = 'Q_MEDIA_MM'
    VOLUMEN = 'VOLUMEN_ESCURRIDO_M3'

    OPCIONES_CHA = [
        'CHA I - suelo seco',
        'CHA II - suelo medio',
        'CHA III - suelo húmedo / saturado',
    ]
    # Campos que GeoQ agrega a la capa resultado, en este orden.
    CAMPOS_CALCULADOS = ['PP(mm)', 'Cod_NC', 'NC', 'S', 'Io', 'CIo', 'Q(mm)',
                         'CE', 'F(mm)', 'CF']
    # Capas de un solo campo: (parámetro, campo, título, estilo)
    CAPAS_TEMATICAS = [
        (SALIDA_NC, 'NC', 'Número de Curva (NC)', 'NC.qml'),
        (SALIDA_CE, 'CE', 'Coeficiente de Escurrimiento CE (%)', 'CE.qml'),
        (SALIDA_CF, 'CF', 'Coeficiente de Infiltración CF (%)', 'CF.qml'),
        (SALIDA_CIO, 'CIo', 'Coeficiente de Abstracciones Iniciales CIo (%)',
         'CIo.qml'),
    ]

    def __init__(self):
        super().__init__()
        self._raster = None

    # ------------------------------------------------------------------
    # Identificación del algoritmo
    # ------------------------------------------------------------------
    def name(self):
        return 'escorrentia'

    def displayName(self):
        return self.tr('Escorrentía superficial (Número de Curva)')

    def shortDescription(self):
        return self.tr('Calcula la escorrentía superficial de una tormenta '
                       'con el método del Número de Curva.')

    def icon(self):
        return QIcon(RUTA_ICONO)

    def helpUrl(self):
        return URL_AYUDA

    def tr(self, texto):
        return QCoreApplication.translate('GeoQ', texto)

    def createInstance(self):
        return GeoQAlgorithm()

    def shortHelpString(self):
        return self.tr(
            '<p>GeoQ calcula la escorrentía superficial de una tormenta con '
            'el método del <b>Número de Curva (NC)</b> del Soil Conservation '
            'Service.</p>'
            '<h3>Datos de entrada</h3>'
            '<ul>'
            '<li><b>Límite del área de estudio</b>: polígono de la cuenca o '
            'zona a modelar. Los resultados quedan en su sistema de '
            'coordenadas.</li>'
            '<li><b>Grupo hidrológico de suelos</b>: capa de polígonos con '
            'un campo que indique el grupo: 1, 2, 3, 4 o bien A, B, C, D.</li>'
            '<li><b>Cobertura vegetal y uso del suelo</b>: capa de polígonos '
            'con un campo con el código de cobertura (10, 20 ... 580). La '
            'herramienta <i>Tabla de códigos y Número de Curva</i> de GeoQ '
            'muestra todos los códigos.</li>'
            '<li><b>Condición de Humedad Antecedente</b>: I (seca), II '
            '(media) o III (húmeda).</li>'
            '<li><b>Precipitación</b>: cargue <u>una sola</u> de las dos '
            'opciones: un valor único en mm para toda el área, o un ráster '
            'con la lluvia del evento en mm.</li>'
            '</ul>'
            '<h3>Resultados</h3>'
            '<ul>'
            '<li><b>GeoQ</b>: cruce de suelos y cobertura con los campos '
            'PP(mm), Cod_NC, NC, S, Io, Q(mm) y F(mm), y los coeficientes '
            'CE, CF y CIo (%).</li>'
            '<li><b>NC, CE, CF y CIo</b>: capas temáticas con su '
            'simbología.</li>'
            '<li>En la pestaña <i>Registro</i> se informa un resumen: '
            'superficie, NC ponderado, escorrentía media y volumen '
            'escurrido.</li>'
            '</ul>'
            '<p><b>S</b> e <b>Io</b> dependen solo del Número de Curva. Si la '
            'lluvia no supera a Io, toda queda retenida (Q = F = 0 y '
            'CIo = 100 %). Donde no llueve (PP = 0), Q, F y los tres '
            'coeficientes valen 0.</p>'
            '<p>Los polígonos con códigos que no figuran en las tablas se '
            'conservan con los resultados vacíos y se listan en el '
            'registro.</p>'
            '<p>Manual y datos de prueba: '
            '<a href="{0}">{0}</a></p>').format(URL_AYUDA)

    # ------------------------------------------------------------------
    # Parámetros
    # ------------------------------------------------------------------
    def initAlgorithm(self, config=None):
        poligonos = [QgsProcessing.SourceType.TypeVectorPolygon]

        self.addParameter(QgsProcessingParameterFeatureSource(
            self.LIMITE, self.tr('Límite del área de estudio'), poligonos))

        self.addParameter(QgsProcessingParameterFeatureSource(
            self.SUELOS, self.tr('Grupo hidrológico de suelos'), poligonos))
        campo = QgsProcessingParameterField(
            self.CAMPO_SUELOS,
            self.tr('Campo del grupo hidrológico (1 a 4, o A a D)'),
            defaultValue='Cod_Sue', parentLayerParameterName=self.SUELOS)
        campo.setHelp(self.tr('Campo de la capa de suelos con el grupo '
                              'hidrológico: 1, 2, 3, 4 o A, B, C, D.'))
        self.addParameter(campo)

        self.addParameter(QgsProcessingParameterFeatureSource(
            self.COBERTURA, self.tr('Cobertura vegetal y uso del suelo'),
            poligonos))
        campo = QgsProcessingParameterField(
            self.CAMPO_COBERTURA,
            self.tr('Campo del código de cobertura (10 a 580)'),
            defaultValue='Cod_Veg', parentLayerParameterName=self.COBERTURA)
        campo.setHelp(self.tr('Campo de la capa de cobertura con el código '
                              'estandarizado de GeoQ (10, 20 ... 580).'))
        self.addParameter(campo)

        self.addParameter(QgsProcessingParameterEnum(
            self.CHA, self.tr('Condición de Humedad Antecedente (CHA)'),
            options=self.OPCIONES_CHA, defaultValue=1))

        self.addParameter(QgsProcessingParameterNumber(
            self.PRECIPITACION,
            self.tr('Precipitación del evento: valor único (mm)'),
            type=QgsProcessingParameterNumber.Type.Double,
            optional=True, minValue=0.0))
        self.addParameter(QgsProcessingParameterRasterLayer(
            self.RASTER,
            self.tr('Precipitación del evento: ráster (mm)'), optional=True))
        banda = QgsProcessingParameterBand(
            self.BANDA, self.tr('Banda del ráster de precipitación'),
            defaultValue=1, parentLayerParameterName=self.RASTER,
            optional=True)
        banda.setFlags(banda.flags() | PARAMETRO_AVANZADO)
        self.addParameter(banda)

        self.addParameter(QgsProcessingParameterFeatureSink(
            self.SALIDA_GEOQ, self.tr('GeoQ'),
            QgsProcessing.SourceType.TypeVectorPolygon))
        for parametro, _campo, titulo, _estilo in self.CAPAS_TEMATICAS:
            self.addParameter(QgsProcessingParameterFeatureSink(
                parametro, self.tr(titulo),
                QgsProcessing.SourceType.TypeVectorPolygon,
                optional=True, createByDefault=True))

        self.addOutput(QgsProcessingOutputNumber(
            self.AREA_HA, self.tr('Superficie analizada (ha)')))
        self.addOutput(QgsProcessingOutputNumber(
            self.NC_PONDERADO, self.tr('NC ponderado por superficie')))
        self.addOutput(QgsProcessingOutputNumber(
            self.PP_MEDIA, self.tr('Precipitación media (mm)')))
        self.addOutput(QgsProcessingOutputNumber(
            self.Q_MEDIA, self.tr('Escorrentía media (mm)')))
        self.addOutput(QgsProcessingOutputNumber(
            self.VOLUMEN, self.tr('Volumen escurrido (m³)')))

    def checkParameterValues(self, parameters, context):
        valido, mensaje = super().checkParameterValues(parameters, context)
        if not valido:
            return valido, mensaje

        con_valor = _definido(parameters.get(self.PRECIPITACION))
        con_raster = _definido(parameters.get(self.RASTER))
        if con_valor and con_raster:
            return False, self.tr(
                'Se cargaron dos precipitaciones. Deje solo una: el valor '
                'único en mm o el ráster de precipitación.')
        if not con_valor and not con_raster:
            return False, self.tr(
                'Falta la precipitación del evento. Ingrese un valor único '
                'en mm o seleccione un ráster de precipitación.')
        if con_valor:
            valor = self.parameterAsDouble(
                parameters, self.PRECIPITACION, context)
            if valor <= 0:
                return False, self.tr(
                    'La precipitación del evento debe ser mayor que 0 mm.')
        return True, ''

    def prepareAlgorithm(self, parameters, context, feedback):
        # El ráster se prepara aquí (hilo principal de QGIS) y se guarda una
        # copia de su proveedor para leerla luego desde el hilo de proceso.
        self._raster = None
        capa = self.parameterAsRasterLayer(parameters, self.RASTER, context)
        if capa is not None:
            banda = self.parameterAsInt(parameters, self.BANDA, context) or 1
            if banda < 1 or banda > capa.bandCount():
                raise QgsProcessingException(self.tr(
                    'El ráster de precipitación no tiene la banda {}.'
                ).format(banda))
            if not capa.crs().isValid():
                raise QgsProcessingException(self.tr(
                    'El ráster de precipitación no tiene un sistema de '
                    'coordenadas definido.'))
            self._raster = {
                'proveedor': capa.dataProvider().clone(),
                'banda': banda,
                'crs': capa.crs(),
                'extension': capa.extent(),
                'columnas': capa.width(),
                'filas': capa.height(),
            }
        return True

    # ------------------------------------------------------------------
    # Proceso
    # ------------------------------------------------------------------
    def processAlgorithm(self, parameters, context, feedback):
        limite = self._fuente(parameters, self.LIMITE, context)
        suelos = self._fuente(parameters, self.SUELOS, context)
        cobertura = self._fuente(parameters, self.COBERTURA, context)
        crs = limite.sourceCrs()
        if not crs.isValid():
            raise QgsProcessingException(self.tr(
                'El límite del área de estudio no tiene un sistema de '
                'coordenadas definido.'))

        campo_sue = self._campo(parameters, self.CAMPO_SUELOS, self.SUELOS,
                                suelos, context)
        campo_veg = self._campo(parameters, self.CAMPO_COBERTURA,
                                self.COBERTURA, cobertura, context)
        cha = self.parameterAsEnum(parameters, self.CHA, context)
        pp_unica = None
        if self._raster is None:
            pp_unica = self.parameterAsDouble(
                parameters, self.PRECIPITACION, context)

        pasos = 6 if self._raster is None else 8
        avance = QgsProcessingMultiStepFeedback(pasos, feedback)

        # 1. Límite del área de estudio con geometrías corregidas
        id_limite = self._corregir(parameters[self.LIMITE], None, context,
                                   avance)
        avance.setCurrentStep(1)
        # 2. Suelos: corregir geometrías, reproyectar y recortar al límite
        id_suelos = self._corregir(parameters[self.SUELOS],
                                   crs if suelos.sourceCrs() != crs else None,
                                   context, avance)
        avance.setCurrentStep(2)
        id_suelos = self._ejecutar('native:clip', {
            'INPUT': id_suelos, 'OVERLAY': id_limite}, context, avance)
        avance.setCurrentStep(3)
        # 3. Cobertura: corregir geometrías y reproyectar
        id_cobertura = self._corregir(
            parameters[self.COBERTURA],
            crs if cobertura.sourceCrs() != crs else None, context, avance)
        avance.setCurrentStep(4)
        if avance.isCanceled():
            return {}

        # 4. Cruce de suelos y cobertura
        capa_suelos = self._capa(id_suelos, context)
        capa_cobertura = self._capa(id_cobertura, context)
        campos_suelos = capa_suelos.fields()
        campos_cobertura = capa_cobertura.fields()
        id_cruce = self._ejecutar('native:intersection', {
            'INPUT': id_suelos, 'OVERLAY': id_cobertura,
            'INPUT_FIELDS': [], 'OVERLAY_FIELDS': [],
            'OVERLAY_FIELDS_PREFIX': ''}, context, avance)
        avance.setCurrentStep(5)
        if avance.isCanceled():
            return {}

        # 5. Precipitación distribuida: píxeles del ráster como polígonos
        if self._raster is not None:
            id_pixeles = self._pixeles_a_poligonos(
                self._capa(id_limite, context).extent(), crs, context, avance)
            avance.setCurrentStep(6)
            id_cruce = self._ejecutar('native:intersection', {
                'INPUT': id_cruce, 'OVERLAY': id_pixeles,
                'INPUT_FIELDS': [], 'OVERLAY_FIELDS': [],
                'OVERLAY_FIELDS_PREFIX': ''}, context, avance)
            avance.setCurrentStep(7)
            if avance.isCanceled():
                return {}

        cruce = self._capa(id_cruce, context)
        if cruce.featureCount() == 0:
            raise QgsProcessingException(self.tr(
                'No hay superposición entre el límite del área de estudio, '
                'los suelos, la cobertura y la precipitación. Revise que las '
                'capas cubran la misma zona y tengan bien definido su '
                'sistema de coordenadas.'))

        # Posición de los campos de código dentro de la capa cruzada. El cruce
        # conserva primero los campos de suelos y luego los de cobertura.
        n_sue, n_veg = campos_suelos.count(), campos_cobertura.count()
        esperados = n_sue + n_veg + (0 if self._raster is None else 1)
        if cruce.fields().count() != esperados:
            raise QgsProcessingException(self.tr(
                'El cruce de capas devolvió una estructura de campos '
                'inesperada.'))
        idx_sue = campos_suelos.lookupField(campo_sue)
        idx_veg = n_sue + campos_cobertura.lookupField(campo_veg)
        idx_pp = None if self._raster is None else esperados - 1

        # Campos de salida: los atributos originales (sin los identificadores
        # internos "fid" ni nombres que GeoQ vaya a calcular) más los propios.
        reservados = {nombre.lower() for nombre in self.CAMPOS_CALCULADOS}
        omitir = set()
        if campos_suelos.lookupField('fid') >= 0:
            omitir.add(campos_suelos.lookupField('fid'))
        if campos_cobertura.lookupField('fid') >= 0:
            omitir.add(n_sue + campos_cobertura.lookupField('fid'))
        if idx_pp is not None:
            omitir.add(idx_pp)
        campos_salida = QgsFields()
        copiar = []
        for i, campo in enumerate(cruce.fields()):
            if i in omitir or campo.name().lower() in reservados:
                continue
            campos_salida.append(campo)
            copiar.append(i)
        campos_salida.append(campo_decimal('PP(mm)'))
        campos_salida.append(campo_entero('Cod_NC'))
        campos_salida.append(campo_entero('NC', 3))
        for nombre in self.CAMPOS_CALCULADOS[3:]:
            campos_salida.append(campo_decimal(nombre))

        tipo_geometria = cruce.wkbType()
        salida_geoq, id_geoq = self.parameterAsSink(
            parameters, self.SALIDA_GEOQ, context, campos_salida,
            tipo_geometria, crs)
        if salida_geoq is None:
            raise QgsProcessingException(
                self.invalidSinkError(parameters, self.SALIDA_GEOQ))
        tematicas = []  # (posición del valor, campos, sumidero)
        resultados = {self.SALIDA_GEOQ: id_geoq}
        for parametro, nombre, _titulo, estilo in self.CAPAS_TEMATICAS:
            campos = QgsFields()
            campos.append(campo_decimal(nombre, 6))
            sumidero, destino = self.parameterAsSink(
                parameters, parametro, context, campos, tipo_geometria, crs)
            if sumidero is None:
                continue
            tematicas.append(
                (self.CAMPOS_CALCULADOS.index(nombre), campos, sumidero))
            resultados[parametro] = destino
            if context.willLoadLayerOnCompletion(destino):
                detalles = context.layerToLoadOnCompletionDetails(destino)
                detalles.setPostProcessor(AplicarEstilo.nuevo(
                    os.path.join(CARPETA, 'estilos', estilo)))

        # 6. Cálculo del Número de Curva y del balance, en una sola pasada
        medidor = QgsDistanceArea()
        medidor.setSourceCrs(crs, context.transformContext())
        elipsoide = context.ellipsoid()
        if not elipsoide or elipsoide.upper() == 'NONE':
            elipsoide = crs.ellipsoidAcronym()
        if elipsoide:
            medidor.setEllipsoid(elipsoide)

        suma = {'area': 0.0, 'nc': 0.0, 'pp': 0.0, 'q': 0.0, 'f': 0.0,
                'io': 0.0}
        area_en_metros = True
        sin_codigo = {}
        sin_lluvia = 0
        total = cruce.featureCount()
        rapido = QgsFeatureSink.Flag.FastInsert
        for n, entidad in enumerate(cruce.getFeatures()):
            if avance.isCanceled():
                return {}
            atributos = entidad.attributes()
            geometria = entidad.geometry()
            area = medidor.measureArea(geometria)
            if not math.isfinite(area):
                # QGIS no reconoce el elipsoide de este sistema de
                # coordenadas: se mide sobre el plano de la proyección.
                medidor.setEllipsoid('NONE')
                area = medidor.measureArea(geometria)
                area_en_metros = not crs.isGeographic()

            pp = pp_unica
            if idx_pp is not None:
                pp = _a_numero(atributos[idx_pp])
            cod_sue = numero_curva.codigo_suelo(atributos[idx_sue])
            cod_veg = numero_curva.codigo_cobertura(atributos[idx_veg])

            calculados = [None] * len(self.CAMPOS_CALCULADOS)
            if pp is not None and pp >= 0:
                calculados[0] = round(pp, 2)
            else:
                pp = None
                sin_lluvia += 1
            if cod_sue is None or cod_veg is None:
                clave = (str(atributos[idx_sue]), str(atributos[idx_veg]))
                sin_codigo[clave] = sin_codigo.get(clave, 0) + 1
            else:
                nc = numero_curva.numero_curva(cod_sue, cod_veg, cha)
                calculados[1] = cod_sue + cod_veg
                calculados[2] = nc
                if pp is not None:
                    b = numero_curva.balance(nc, pp)
                    calculados[3:] = [round(b[c], 2) for c in (
                        'S', 'Io', 'CIo', 'Q', 'CE', 'F', 'CF')]
                    suma['area'] += area
                    suma['nc'] += nc * area
                    suma['pp'] += pp * area
                    suma['q'] += b['Q'] * area
                    suma['f'] += b['F'] * area
                    suma['io'] += min(b['Io'], pp) * area

            nueva = QgsFeature(campos_salida)
            nueva.setGeometry(geometria)
            nueva.setAttributes([atributos[i] for i in copiar] + calculados)
            if not salida_geoq.addFeature(nueva, rapido):
                raise QgsProcessingException(self.writeFeatureError(
                    salida_geoq, parameters, self.SALIDA_GEOQ))
            for posicion, campos, sumidero in tematicas:
                tematica = QgsFeature(campos)
                tematica.setGeometry(geometria)
                tematica.setAttributes([calculados[posicion]])
                sumidero.addFeature(tematica, rapido)
            if n % 200 == 0:
                avance.setProgress(100.0 * n / total)
        avance.setCurrentStep(pasos)

        self._informar_codigos(sin_codigo, sin_lluvia, feedback)
        resultados.update(
            self._informar_resumen(suma, cha, area_en_metros, feedback))
        return resultados

    # ------------------------------------------------------------------
    # Funciones auxiliares
    # ------------------------------------------------------------------
    def _fuente(self, parameters, nombre, context):
        fuente = self.parameterAsSource(parameters, nombre, context)
        if fuente is None:
            raise QgsProcessingException(
                self.invalidSourceError(parameters, nombre))
        return fuente

    def _campo(self, parameters, nombre, nombre_capa, fuente, context):
        campo = self.parameterAsString(parameters, nombre, context)
        if not campo or fuente.fields().lookupField(campo) < 0:
            raise QgsProcessingException(self.tr(
                'La capa "{}" no tiene el campo "{}". Seleccione el campo '
                'que contiene los códigos.').format(
                    self.parameterDefinition(nombre_capa).description(),
                    campo))
        return campo

    def _capa(self, identificador, context):
        capa = QgsProcessingUtils.mapLayerFromString(identificador, context)
        if capa is None:
            raise QgsProcessingException(self.tr(
                'No se pudo leer un resultado intermedio del proceso.'))
        return capa

    def _ejecutar(self, algoritmo, parametros, context, feedback):
        parametros = dict(parametros)
        parametros['OUTPUT'] = QgsProcessing.TEMPORARY_OUTPUT
        return processing.run(algoritmo, parametros, context=context,
                              feedback=feedback,
                              is_child_algorithm=True)['OUTPUT']

    def _corregir(self, entrada, crs_destino, context, feedback):
        """Corrige geometrías inválidas y, si hace falta, reproyecta."""
        salida = self._ejecutar('native:fixgeometries', {'INPUT': entrada},
                                context, feedback)
        if crs_destino is not None:
            salida = self._ejecutar('native:reprojectlayer', {
                'INPUT': salida, 'TARGET_CRS': crs_destino},
                context, feedback)
        self._indexar(salida, context, feedback)
        return salida

    def _indexar(self, identificador, context, feedback):
        """Crea el índice espacial: acelera el recorte y los cruces."""
        processing.run('native:createspatialindex', {'INPUT': identificador},
                       context=context, feedback=feedback,
                       is_child_algorithm=True)

    def _pixeles_a_poligonos(self, extension, crs, context, feedback):
        """Convierte en polígonos los píxeles del ráster que tocan el área.

        Solo se leen los píxeles dentro de la extensión del límite, en lugar
        de vectorizar el ráster completo.
        """
        r = self._raster
        if r['crs'] != crs:
            transformacion = QgsCoordinateTransform(
                crs, r['crs'], context.transformContext())
            extension = transformacion.transformBoundingBox(extension)
        total = r['extension']
        ancho = total.width() / r['columnas']
        alto = total.height() / r['filas']
        # Ventana de píxeles (con uno de margen) que cubre el área de estudio
        col0 = max(0, int(math.floor(
            (extension.xMinimum() - total.xMinimum()) / ancho)) - 1)
        col1 = min(r['columnas'], int(math.ceil(
            (extension.xMaximum() - total.xMinimum()) / ancho)) + 1)
        fila0 = max(0, int(math.floor(
            (total.yMaximum() - extension.yMaximum()) / alto)) - 1)
        fila1 = min(r['filas'], int(math.ceil(
            (total.yMaximum() - extension.yMinimum()) / alto)) + 1)
        if col1 <= col0 or fila1 <= fila0:
            raise QgsProcessingException(self.tr(
                'El ráster de precipitación no cubre el área de estudio.'))
        columnas = col1 - col0
        if columnas * (fila1 - fila0) > PIXELES_AVISO:
            feedback.pushWarning(self.tr(
                'El área de estudio abarca {} píxeles del ráster de '
                'precipitación: el proceso puede demorar. Considere usar un '
                'ráster de menor resolución.').format(
                    columnas * (fila1 - fila0)))

        campos = QgsFields()
        campos.append(campo_decimal('PP_RASTER', 20, 6))
        sumidero, destino = QgsProcessingUtils.createFeatureSink(
            'memory:', context, campos, Qgis.WkbType.Polygon, r['crs'])
        x0 = total.xMinimum() + col0 * ancho
        rapido = QgsFeatureSink.Flag.FastInsert
        for inicio in range(fila0, fila1, FILAS_POR_BLOQUE):
            if feedback.isCanceled():
                break
            filas = min(FILAS_POR_BLOQUE, fila1 - inicio)
            y_superior = total.yMaximum() - inicio * alto
            bloque = r['proveedor'].block(
                r['banda'],
                QgsRectangle(x0, y_superior - filas * alto,
                             x0 + columnas * ancho, y_superior),
                columnas, filas)
            for fila in range(filas):
                y = y_superior - fila * alto
                for columna in range(columnas):
                    if bloque.isNoData(fila, columna):
                        continue
                    valor = bloque.value(fila, columna)
                    if not math.isfinite(valor):
                        continue
                    x = x0 + columna * ancho
                    pixel = QgsFeature(campos)
                    pixel.setGeometry(QgsGeometry.fromRect(
                        QgsRectangle(x, y - alto, x + ancho, y)))
                    pixel.setAttributes([valor])
                    sumidero.addFeature(pixel, rapido)
            feedback.setProgress(
                100.0 * (inicio + filas - fila0) / (fila1 - fila0))
        del sumidero
        self._indexar(destino, context, feedback)
        return destino

    def _informar_codigos(self, sin_codigo, sin_lluvia, feedback):
        if sin_codigo:
            feedback.pushWarning(self.tr(
                'ATENCIÓN: {} polígonos tienen códigos que no figuran en '
                'las tablas de GeoQ y quedaron sin resultados. '
                'Combinaciones encontradas (suelo / cobertura):').format(
                    sum(sin_codigo.values())))
            for (sue, veg), cantidad in sorted(sin_codigo.items())[:25]:
                feedback.pushWarning('   {} / {}  ->  {} {}'.format(
                    sue, veg, cantidad, self.tr('polígonos')))
            if len(sin_codigo) > 25:
                feedback.pushWarning('   ...')
        if sin_lluvia:
            feedback.pushWarning(self.tr(
                'ATENCIÓN: {} polígonos tienen un valor de precipitación '
                'negativo o no numérico y quedaron sin resultados.'
            ).format(sin_lluvia))

    def _informar_resumen(self, suma, cha, area_en_metros, feedback):
        area = suma['area']
        if area <= 0:
            feedback.pushWarning(self.tr(
                'Ningún polígono tiene códigos válidos: no se pudo calcular '
                'el Número de Curva.'))
            return {}
        pp = suma['pp'] / area
        q = suma['q'] / area
        f = suma['f'] / area
        io = suma['io'] / area
        volumen = suma['q'] / 1000.0  # mm x m² = litros; / 1000 = m³

        def porcentaje(valor):
            return 100.0 * valor / pp if pp > 0 else 0.0

        resumen = {
            self.NC_PONDERADO: suma['nc'] / area,
            self.PP_MEDIA: pp,
            self.Q_MEDIA: q,
        }
        feedback.pushInfo('')
        feedback.pushInfo(self.tr('RESUMEN GeoQ - {}').format(
            self.OPCIONES_CHA[cha]))
        if area_en_metros:
            resumen[self.AREA_HA] = area / 10000.0
            resumen[self.VOLUMEN] = volumen
            feedback.pushInfo('- {}: {:.2f} ha'.format(
                self.tr('Superficie analizada'), area / 10000.0))
        for etiqueta, valor in (
                (self.tr('Precipitación media'), '{:.2f} mm'.format(pp)),
                (self.tr('NC ponderado por superficie'),
                 '{:.1f}'.format(suma['nc'] / area)),
                (self.tr('Escorrentía media (Q)'),
                 '{:.2f} mm  ({:.1f} %)'.format(q, porcentaje(q))),
                (self.tr('Infiltración media (F)'),
                 '{:.2f} mm  ({:.1f} %)'.format(f, porcentaje(f))),
                (self.tr('Abstracciones iniciales medias (Io)'),
                 '{:.2f} mm  ({:.1f} %)'.format(io, porcentaje(io)))):
            feedback.pushInfo('- {}: {}'.format(etiqueta, valor))
        if area_en_metros:
            feedback.pushInfo('- {}: {:.0f} m³  ({:.3f} hm³)'.format(
                self.tr('Volumen escurrido'), volumen, volumen / 1e6))
        else:
            feedback.pushWarning(self.tr(
                'No se pudo medir la superficie en este sistema de '
                'coordenadas: no se informan la superficie ni el volumen.'))
        feedback.pushInfo('')
        return resumen
