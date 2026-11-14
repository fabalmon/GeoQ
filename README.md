# GeoQ

Automatización del cálculo de la escorrentía superficial con el método del Número de Curva, bajo entorno QGIS.

## Descripción

La modelización de fenómenos hidrológicos permite calcular o cuantificar la cantidad de precipitación de una tormenta que se infiltra o escurre superficialmente, teniendo en cuenta sus características de uso y cobertura del suelo y textura edáfica. GeoQ realiza esta modelación hidrológica superficial implementando la metodología del Número de Curva (NC) del Soil Conservation Service de Estados Unidos.

## Requisitos

- QGIS 3.34 o posterior, incluido **QGIS 4** (Qt6).
- No necesita bibliotecas adicionales.

## Instalación

**Desde QGIS (recomendado):** menú *Complementos → Administrar e instalar complementos*, buscar **GeoQ** e instalar. El complemento está publicado en el [repositorio oficial de complementos de QGIS](https://plugins.qgis.org/plugins/GeoQ-main/).

**Desde un archivo ZIP:** descargar `GeoQ-main.zip` desde la sección [Releases](https://github.com/fabalmon/GeoQ/releases) de este repositorio y, en QGIS, usar *Complementos → Administrar e instalar complementos → Instalar a partir de ZIP*.

> El botón *Code → Download ZIP* de GitHub descarga todo el repositorio (manual, datos de prueba, etc.) y **no** sirve para instalar el complemento.

## Datos necesarios

1. **Límite del área de estudio**: capa de polígonos (cuenca, parcela, etc.). Los resultados quedan en su sistema de coordenadas.
2. **Grupo hidrológico de suelos**: capa de polígonos con un campo que indique el grupo hidrológico: `1`, `2`, `3`, `4` o bien `A`, `B`, `C`, `D` (por defecto, el campo `Cod_Sue`).
3. **Cobertura vegetal y uso del suelo**: capa de polígonos con un campo con el código de cobertura estandarizado, de `10` a `580` (por defecto, el campo `Cod_Veg`).
4. **Condición de Humedad Antecedente (CHA)**: I (seca), II (media) o III (húmeda).
5. **Precipitación del evento**, de una sola de estas dos formas:
   - un valor único en milímetros para toda el área, o
   - un ráster con la lluvia del evento en milímetros.

Los códigos de suelo y de cobertura se detallan en el [manual](docs/) y en la herramienta **Tabla de códigos y Número de Curva**, incluida en el complemento.

Para probar el complemento, `Test_data.zip` contiene capas en formato GeoPackage de suelos y vegetación de la cuenca del río Napaleofú (provincia de Buenos Aires, Argentina).

## Uso

GeoQ se abre desde el botón de la barra de herramientas, desde el menú *Complementos → GeoQ* o desde la *Caja de herramientas de Procesos → GeoQ*.

## Resultados

Al ejecutar el modelo se cargan en el proyecto:

- **GeoQ**: cruce de suelos y cobertura con los campos `PP(mm)`, `Cod_NC`, `NC`, `S` (retención potencial), `Io` (abstracciones iniciales), `Q(mm)` (escorrentía), `F(mm)` (infiltración) y los coeficientes `CE`, `CF` y `CIo` en porcentaje.
- **Número de Curva (NC)**, **Coeficiente de Escurrimiento CE (%)**, **Coeficiente de Infiltración CF (%)** y **Coeficiente de Abstracciones Iniciales CIo (%)**, cada una con su simbología.

En la pestaña *Registro* se informa además un resumen del área de estudio: superficie, NC ponderado, escorrentía e infiltración medias y volumen escurrido.

## Documentación

- Manual: carpeta [`docs`](docs/).
- Video tutorial: <https://youtu.be/iXmaXzW4_aQ>

## Desarrollo

| Carpeta | Contenido |
|---|---|
| `geoq/` | El complemento (lo único que se instala en QGIS). |
| `geoq/numero_curva.py` | Tabla de Número de Curva y fórmulas del método. |
| `geoq/estilos/` | Simbología de las capas resultado. |
| `tests/` | Pruebas automáticas. |
| `scripts/empaquetar.py` | Genera `dist/GeoQ-main.zip`, listo para instalar o subir a plugins.qgis.org. |
| `docs/` | Manual del complemento. |

Para probar cambios, enlazar la carpeta `geoq` dentro de la carpeta de complementos del perfil de QGIS con el nombre `GeoQ-main` y recargar con el complemento *Plugin Reloader*.

Pruebas (con el Python de QGIS): `python -m pytest tests`

## Menciones

Este complemento se desarrolló en el marco de una beca doctoral suministrada por la [Comisión de Investigaciones Científicas](https://www.cic.gba.gob.ar/) de la provincia de Buenos Aires - Argentina, en el [Centro de Estudios Integrales de la Dinámica Exógena – UNLP](https://ceide.unlp.edu.ar/), enfocada en la cátedra de [Manejo Integral de Cuencas Hidrográficas](http://maestriacuencashidrograficas.agro.unlp.edu.ar/), por el becario [Mg. Fabio Alejandro Montealegre Medina](https://ceide.unlp.edu.ar/personal/monteaelegre-medina-fabio-alejandro/) y dirigido por la [Dra. Fernanda Julia Gaspari](https://ceide.unlp.edu.ar/personal/dra-fernanda-julia-gaspari/).

## Licencia

GNU General Public License, versión 2 o posterior. Ver [LICENSE](LICENSE).
