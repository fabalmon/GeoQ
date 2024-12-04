# GeoQ
Automatización del procesamiento de cálculo de la escorrentía superficial bajo entorno QGis.

## Descripción
La modelización de fenómenos hidrológicos permite calcular o cuantificar la cantidad de precipitación de una tormenta que se infiltra o escurre superficialmente, teniendo en cuenta sus características de uso y cobertura del suelo y textura edáfica. GeoQ realiza esta modelación hidrológica superficial implementado la metodología del Número de Curva (NC) del Soil Conservation Service de Estados Unidos.

## Datos necesarios
Se requiere de un valor de precipitación de un evento (en milímetros) o una archivo raster que represente la tormenta analizada para la zona de estudio, una capa vectorial de uso y cobertura del suelo y otra del grupo hidrológico edáfico.

_Las capas vectoriales debes están estandarizadas según los códigos que se mencionan en el archivo Manual complemento GeoQ 2.8.docx_

Si desea realizar alguna prueba del complemento con datos estandarizados, el archivo Test_data.zip contiene capas vectoriales en formato GeoPackage de suelos y vegetación pertenecientes a la cuenca del río Napaleoufú, ubicada en la provincia de Buenos Aires, Argentina.

## Instalación
El complemento esta diseñado para corren en QGis (versión 3.18 en adelante).
GeoQ se puede instalar desde la Barra de Complementos –   , desde el ítem Administrar e instalar complementos. Luego seleccionar el complemento GeoQ y proceder a la instalación del complemento.
El complemento también se encuentra en el repositorio oficial de complementos de QGis https://github.com/fabalmon/GeoQ.git. La herramienta está disponible en este repositorio en formato zip. En la opción “Code” en la esquina superior derecha del repositorio, debe seleccionar “Download ZIP” para así obtener el archivo ZIP¨ del complemento a subir a QGIS. Posteriormente, subir manualmente al programa el archivo Zip e instalar desde este tipo de archivo, en el software geográfico QGis (en versiones 3.18 en adelante) e instale el complemento denominado GeoQ, en la barra de herramientas Administrar e instalar complementos   por medio de la opción “Instalar a partir de ZIP”, allí se debe seleccionar el archivo ZIP descargado de la página GibHub y oprimir “Instalar complemento”. 

Para instalar en complemento utilizando este archivo, se ingresar a el Administrador de complementos de QGis y dirigirse a la opción [Instalar a partir de ZIP](https://gis.stackexchange.com/questions/302196/downloading-and-saving-plugins-for-qgis-3-4).

## Resultados
Una vez se ejecutado el modelo GeoQ, las capas resultado se cargarán automáticamente en el proyecto de QGis en el que se está trabajando. Estas nuevas capas shp son: GeoQ, Numero de Curva (NC), Coeficiente de Escurrimiento (CE) (%), Coeficiente de Infiltración (CF) (%) y Coeficiente de Abstracciones (CIo) (%).


## Menciones
Este complemento se desarrolló en el marco de una beca doctoral del suministrada por la [Comisión de Investigaciones Científicas]( https://www.cic.gba.gob.ar/) de la provincia de Buenos Aires - Argentina, en el [Centro de Estudios Integrales de la Dinámica Exógena – UNLP]( https://ceide.unlp.edu.ar/), enfocada en la catedra de [Manejo Integral de Cuencas Hidrográficas]( http://maestriacuencashidrograficas.agro.unlp.edu.ar/), por el becario [Mg. Fabio Alejandro Montealegre Medina](https://ceide.unlp.edu.ar/personal/monteaelegre-medina-fabio-alejandro/) y dirigido por la [Dr. Fernanda Julia Gaspari](https://ceide.unlp.edu.ar/personal/dra-fernanda-julia-gaspari/)
