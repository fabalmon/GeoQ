# -*- coding: utf-8 -*-
"""Pruebas del algoritmo de GeoQ dentro de QGIS (requieren PyQGIS).

Se ejecutan con el Python de QGIS:  python -m pytest tests

``referencia_v2_8.json`` guarda los resultados de GeoQ 2.8 con los mismos
datos: la versión actual debe reproducirlos, salvo por las correcciones
hechas a propósito (ver ``_cambio_esperado``).
"""

import json
import os

import pytest

pytest.importorskip('qgis.core')

CAMPOS = ('NC', 'S', 'Io', 'CIo', 'Q(mm)', 'CE', 'F(mm)', 'CF')
ALGORITMO = 'geoq:escorrentia'

with open(os.path.join(os.path.dirname(__file__), 'referencia_v2_8.json'),
          encoding='utf-8') as _archivo:
    REFERENCIA = json.load(_archivo)

CASOS = {
    'valor_cha1': dict(limite='limite', pp=80.1, cha=0),
    'valor_cha2': dict(limite='limite', pp=80.1, cha=1),
    'valor_cha3': dict(limite='limite', pp=80.1, cha=2),
    'valor_limite_wgs84': dict(limite='limite_wgs84', pp=35.0, cha=1),
    'raster_cha2': dict(limite='limite', raster='raster', cha=1),
}


def _nulo(valor):
    return valor is None or (hasattr(valor, 'isNull') and valor.isNull())


def _parametros(datos, limite='limite', pp=None, raster=None, cha=1, **otros):
    parametros = {
        'LIMITE': datos[limite],
        'SUELOS': datos['suelos'], 'CAMPO_SUELOS': 'Cod_Sue',
        'COBERTURA': datos['cobertura'], 'CAMPO_COBERTURA': 'Cod_Veg',
        'CHA': cha,
        'PRECIPITACION': pp,
        'RASTER_PRECIPITACION': datos[raster] if raster else None,
        'GEOQ': 'TEMPORARY_OUTPUT', 'NC': 'TEMPORARY_OUTPUT',
        'CE': 'TEMPORARY_OUTPUT', 'CF': 'TEMPORARY_OUTPUT',
        'CIO': 'TEMPORARY_OUTPUT',
    }
    parametros.update(otros)
    return parametros


def _ejecutar(parametros, feedback=None):
    import processing
    return processing.run(ALGORITMO, parametros, feedback=feedback)


def _resumir(capa):
    """Agrupa la capa GeoQ por combinación Cod_NC | PP(mm)."""
    nombres = capa.fields().names()
    grupos = {}
    for entidad in capa.getFeatures():
        atributos = dict(zip(nombres, entidad.attributes()))
        clave = '{}|{:.2f}'.format(atributos['Cod_NC'],
                                   float(atributos['PP(mm)']))
        grupo = grupos.setdefault(clave, {'area': 0.0})
        grupo['area'] += entidad.geometry().area()
        for campo in CAMPOS:
            valor = atributos[campo]
            valor = None if _nulo(valor) else float(valor)
            assert grupo.setdefault(campo, valor) == valor
    return grupos


def _cambio_esperado(clave, campo, antes):
    """Diferencias buscadas respecto de GeoQ 2.8."""
    cod_nc, pp = clave.split('|')
    # Valores de Número de Curva corregidos en la versión 2.9
    if cod_nc in ('443', '444', '554'):
        return True
    # Con lluvia 0 la versión 2.8 dejaba CE vacío; ahora vale 0
    return float(pp) == 0 and campo == 'CE' and antes is None


@pytest.mark.parametrize('caso', sorted(CASOS))
def test_reproduce_geoq_2_8(qgis, datos, caso):
    referencia = REFERENCIA[caso]
    resultado = _ejecutar(_parametros(datos, **CASOS[caso]))
    grupos = _resumir(resultado['GEOQ'])
    assert sorted(grupos) == sorted(referencia)
    for clave, antes in referencia.items():
        ahora = grupos[clave]
        # (la referencia guarda las superficies en m² con 2 decimales)
        assert ahora['area'] == pytest.approx(
            antes['area'], rel=1e-6, abs=0 if 'wgs84' in caso else 0.006)
        for campo in CAMPOS:
            if _cambio_esperado(clave, campo, antes[campo]):
                continue
            # 2.8 redondeaba los pasos intermedios: tolerancia de 0,02
            assert ahora[campo] == pytest.approx(antes[campo], abs=0.021), (
                clave, campo)
    # Las capas temáticas tienen una entidad por polígono de GeoQ
    total = resultado['GEOQ'].featureCount()
    for salida, campo in (('NC', 'NC'), ('CE', 'CE'), ('CF', 'CF'),
                          ('CIO', 'CIo')):
        assert resultado[salida].featureCount() == total
        assert resultado[salida].fields().names() == [campo]


def test_valores_corregidos_en_el_resultado(qgis, datos):
    """El código 554 (suelos pedregosos, grupo D) usa los valores nuevos."""
    for cha, esperado in ((0, 82), (1, 92), (2, 97)):
        grupos = _resumir(_ejecutar(_parametros(
            datos, pp=80.1, cha=cha))['GEOQ'])
        assert grupos['554|80.10']['NC'] == esperado


def test_coeficientes_suman_100(qgis, datos):
    capa = _ejecutar(_parametros(datos, raster='raster'))['GEOQ']
    nombres = capa.fields().names()
    for entidad in capa.getFeatures():
        a = dict(zip(nombres, entidad.attributes()))
        assert a['CE'] + a['CF'] + a['CIo'] == pytest.approx(100, abs=0.02)
        assert a['Q(mm)'] + a['F(mm)'] <= a['PP(mm)'] + 0.02


def test_limite_multiparte(qgis, datos):
    """Un límite multiparte da lo mismo que sus partes por separado."""
    simple = _ejecutar(_parametros(datos, pp=80.1))
    multiparte = _ejecutar(_parametros(
        datos, limite='limite_multiparte', pp=80.1))
    assert multiparte['AREA_HA'] == pytest.approx(simple['AREA_HA'], rel=1e-9)
    assert multiparte['VOLUMEN_ESCURRIDO_M3'] == pytest.approx(
        simple['VOLUMEN_ESCURRIDO_M3'], rel=1e-9)


def test_resumen(qgis, datos):
    resultado = _ejecutar(_parametros(datos, pp=80.1))
    capa = resultado['GEOQ']
    area = sum(e.geometry().area() for e in capa.getFeatures())
    assert resultado['AREA_HA'] == pytest.approx(area / 10000, rel=1e-3)
    assert resultado['PP_MEDIA_MM'] == pytest.approx(80.1)
    assert 0 < resultado['Q_MEDIA_MM'] < 80.1
    assert 0 < resultado['NC_PONDERADO'] <= 100
    assert resultado['VOLUMEN_ESCURRIDO_M3'] == pytest.approx(
        resultado['Q_MEDIA_MM'] / 1000 * resultado['AREA_HA'] * 10000)
    # El límite en coordenadas geográficas mide la misma superficie
    geografico = _ejecutar(_parametros(datos, limite='limite_wgs84', pp=80.1))
    assert geografico['AREA_HA'] == pytest.approx(
        resultado['AREA_HA'], rel=1e-3)


def test_grupo_hidrologico_con_letras(qgis, datos):
    """El campo GH (A, B, C, D) equivale al campo Cod_Sue (1 a 4)."""
    numeros = _ejecutar(_parametros(datos, pp=80.1))
    letras = _ejecutar(_parametros(datos, pp=80.1, CAMPO_SUELOS='GH'))
    assert _resumir(letras['GEOQ']) == _resumir(numeros['GEOQ'])


def test_campos_con_otro_nombre(qgis, datos):
    """Se pueden usar campos de código con nombres repetidos en ambas capas.

    Las capas de prueba tienen "COD" (suelos) y "cod" (vegetación), con los
    mismos códigos que Cod_Sue y Cod_Veg.
    """
    habitual = _ejecutar(_parametros(datos, pp=80.1))
    otros = _ejecutar(_parametros(
        datos, pp=80.1, CAMPO_SUELOS='COD', CAMPO_COBERTURA='cod'))
    assert _resumir(otros['GEOQ']) == _resumir(habitual['GEOQ'])


def test_campo_inexistente(qgis, datos):
    from qgis.core import QgsProcessingException
    with pytest.raises(QgsProcessingException):
        _ejecutar(_parametros(datos, pp=80.1, CAMPO_SUELOS='no_existe'))


@pytest.mark.parametrize('precipitacion', [
    dict(),                              # ninguna
    dict(pp=80.1, raster='raster'),      # las dos
    dict(pp=0),                          # lluvia nula
])
def test_precipitacion_mal_cargada(qgis, datos, precipitacion):
    from qgis.core import QgsProcessingException
    with pytest.raises(QgsProcessingException):
        _ejecutar(_parametros(datos, **precipitacion))


def test_codigos_desconocidos(qgis, datos, tmp_path):
    """Los códigos fuera de tabla quedan sin resultado y se informan."""
    import shutil
    from qgis.core import QgsProcessingFeedback, QgsVectorLayer

    copia = str(tmp_path / 'cobertura.gpkg')
    shutil.copy(datos['cobertura'], copia)
    capa = QgsVectorLayer(copia, 'cobertura', 'ogr')
    indice = capa.fields().lookupField('Cod_Veg')
    capa.startEditing()
    for entidad in capa.getFeatures():
        if entidad['Cod_Veg'] == 170:
            capa.changeAttributeValue(entidad.id(), indice, 999)
    assert capa.commitChanges()

    class Registro(QgsProcessingFeedback):
        avisos = []

        def pushWarning(self, mensaje):
            self.avisos.append(mensaje)

    registro = Registro()
    resultado = _ejecutar(
        _parametros(datos, pp=80.1, COBERTURA=copia), registro)
    nombres = resultado['GEOQ'].fields().names()
    vacios = 0
    for entidad in resultado['GEOQ'].getFeatures():
        a = dict(zip(nombres, entidad.attributes()))
        if a['Cod_Veg'] == 999:
            vacios += 1
            assert _nulo(a['NC']) and _nulo(a['Q(mm)']) and _nulo(a['CE'])
            assert a['PP(mm)'] == pytest.approx(80.1)
        else:
            assert not _nulo(a['NC'])
    assert vacios > 0
    assert any('999' in aviso for aviso in registro.avisos)


@pytest.mark.parametrize('extension', ['gpkg', 'shp'])
def test_guardar_en_archivo(qgis, datos, tmp_path, extension):
    from qgis.core import QgsVectorLayer
    salidas = {clave: str(tmp_path / '{}.{}'.format(clave, extension))
               for clave in ('GEOQ', 'NC', 'CE', 'CF', 'CIO')}
    resultado = _ejecutar(_parametros(datos, raster='raster', **salidas))
    memoria = _ejecutar(_parametros(datos, raster='raster'))['GEOQ']
    for clave, ruta in salidas.items():
        capa = QgsVectorLayer(resultado[clave], clave, 'ogr')
        assert capa.isValid()
        assert capa.featureCount() == memoria.featureCount()
    capa = QgsVectorLayer(resultado['GEOQ'], 'GeoQ', 'ogr')
    for campo in ('PP(mm)', 'Cod_NC') + CAMPOS:
        assert campo in capa.fields().names()


def test_capas_tematicas_opcionales(qgis, datos):
    parametros = _parametros(datos, pp=80.1)
    for clave in ('NC', 'CE', 'CF', 'CIO'):
        del parametros[clave]
    resultado = _ejecutar(parametros)
    assert resultado['GEOQ'].featureCount() > 0
    assert 'NC' not in resultado and 'CE' not in resultado


def test_estilos(qgis, datos):
    """Cada capa temática tiene su archivo de estilo y se puede cargar."""
    from geoq.geoq_algorithm import CARPETA, AplicarEstilo, GeoQAlgorithm
    resultado = _ejecutar(_parametros(datos, pp=80.1))
    for parametro, campo, _titulo, estilo in GeoQAlgorithm.CAPAS_TEMATICAS:
        ruta = os.path.join(CARPETA, 'estilos', estilo)
        assert os.path.isfile(ruta)
        capa = resultado[parametro]
        AplicarEstilo.para(ruta).postProcessLayer(capa, None, None)
        assert capa.renderer().type() == 'graduatedSymbol'
        assert capa.renderer().classAttribute() == campo


def test_raster_fuera_del_area(qgis, datos, tmp_path):
    """Un ráster que no cubre el área de estudio da un error claro."""
    from osgeo import gdal
    from qgis.core import QgsProcessingException
    ruta = str(tmp_path / 'lejos.tif')
    gdal.Translate(ruta, datos['raster'],
                   outputBounds=[10.0, 50.0, 10.4, 49.72])
    with pytest.raises(QgsProcessingException):
        _ejecutar(_parametros(datos, RASTER_PRECIPITACION=ruta))


def test_tabla_de_codigos(qgis):
    import processing
    tabla = processing.run('geoq:tablanc', {'TABLA': 'TEMPORARY_OUTPUT'})[
        'TABLA']
    assert tabla.featureCount() == 58
    assert tabla.fields().names()[:3] == ['Cod_Veg', 'Cobertura', 'Uso_suelo']
    fila = next(e for e in tabla.getFeatures() if e['Cod_Veg'] == 10)
    assert [fila['A_II'], fila['B_II'], fila['C_II'], fila['D_II']] == [
        77, 86, 91, 94]


def test_complemento_se_carga(qgis):
    """classFactory y el proveedor funcionan con una interfaz simulada."""
    from unittest import mock
    from qgis.core import QgsApplication
    import geoq

    registro = QgsApplication.processingRegistry()
    assert registro.algorithmById('geoq:escorrentia') is not None
    assert registro.algorithmById('geoq:tablanc') is not None

    interfaz = mock.MagicMock()
    interfaz.mainWindow.return_value = None
    complemento = geoq.classFactory(interfaz)
    with mock.patch.object(complemento, 'initProcessing'):
        complemento.initGui()
    assert interfaz.addPluginToMenu.call_count == 2
    assert interfaz.addToolBarIcon.call_count == 1
    complemento.unload()
    assert interfaz.removePluginMenu.call_count == 2
