# GeoQ

Automatización del procesamiento de cálculo de la escorrentía superficial bajo entorno S.I.G. en QGis 3.18®.

## Descripción

La modelización de fenómenos hidrológicos permite calcular o cuantifica la cantidad de precipitación de una tormenta que se infiltra o escurre superficialmente, teniendo en cuenta sus características de uso y cobertura del suelo y textura edáficas. GeoQ realiza esta modelación implementado la metodología del Número de Curva (NC) mencionado por el Soil Conservation Service.

## Insumos
Descargue y descomprima el archivo GeoQ.zip en la raíz C://
En la carpeta encontrara archivos de simbología necesaria para los resultados y las tablas de consulta necesarias para el calculo de Numero de Curva (La tabla, según sea el caso, debe ser cargada al proyecto de QGis al momento de ejecutar el complemento)

## Datos necesarios

Se requiere de un valor de precipitación medio en milímetros para la zona de estudio
Capa vectorial de uso y cobertura del suelo
Capa vectorial de grupo hidrológico del suelo

_Las capas vectoriales debes están estandarizadas con los códigos que se mencionan en el archivo Manual complemento GeoQ.docx_

Si desea realizar alguna prueba del complemento con datos estandarizados, el archivo Test_data.zip contiene capas vectoriales en formato GeoPackage de suelos y vegetación pertenecientes a la cuenca del río Napaleufou, ubicada en la provincia de Buenos Aires - Argentina.

## Instalacion
El complemento esta diseñado para corren en QGis (versión 3.18 en adelante). Por el momento no se encuentra en el repositorio oficial del software, por tal razón se debe descargar el contenido del repositorio Github, comprimido en ZIP (en la esquina superior derecha seleccionar Code – Download ZIP).
Para instalar en complemento utilizando este archivo, se ingresar a el Administrados de complementos de QGis y dirigirse a la opción [Instalar a partir de ZIP](https://gis.stackexchange.com/questions/302196/downloading-and-saving-plugins-for-qgis-3-4)

## Resultados
Las casillas GeoQ y los Coeficientes, en la interfaz del complemento, se sugiere que se creen y nombren archivos para estos en el equipo, _de lo contrario se generaran capas temporales sin nombres relacionados al proceso_ en el proyecto de QGIs

## Menciones
Este complemento se desarrollo en el marco de una beca doctoral del suministrada por [La Comisión de Investigaciones Científicas]( https://www.cic.gba.gob.ar/) de la provincia de Buenos Aires - Argentina, en el [Centro de Estudios Integrales de la Dinámica Exógena – UNLP]( https://ceide.unlp.edu.ar/), enfocada en la catedra de [Manejo Integral de Cuencas Hidrográficas]( http://maestriacuencashidrograficas.agro.unlp.edu.ar/), por el becario [Mg. Fabio Alejandro Montealegre Medina](https://ceide.unlp.edu.ar/personal/monteaelegre-medina-fabio-alejandro/) y dirigido por la [Dr. Fernanda Julia Gaspari](https://ceide.unlp.edu.ar/personal/dra-fernanda-julia-gaspari/)
