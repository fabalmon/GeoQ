# -*- coding: utf-8 -*-
"""Tablas y fórmulas del método del Número de Curva (NC) usadas por GeoQ.

Este módulo no depende de QGIS: contiene únicamente los datos (tabla de NC
y descripción de las coberturas) y las ecuaciones del método del Soil
Conservation Service. Así se puede revisar, corregir y probar por separado
del resto del complemento.

Copyright (C) 2024 Fabio A. Montealegre M. & Fernanda J. Gaspari
Licencia GNU GPL versión 2 o posterior.
"""

import math

# Condiciones de Humedad Antecedente, en el orden de las columnas de TABLA_NC.
CHA = ('I', 'II', 'III')

# Grupos hidrológicos de suelo y su código (Cod_Sue) - Tabla 1 del manual.
GRUPOS_HIDROLOGICOS = {'A': 1, 'B': 2, 'C': 3, 'D': 4}

# Número de Curva según cobertura (Cod_Veg), grupo hidrológico y CHA.
# Cada fila tiene 12 valores, en este orden:
#
#   Cod_Veg: (A-I, A-II, A-III,  B-I, B-II, B-III,
#             C-I, C-II, C-III,  D-I, D-II, D-III)
#
# Para corregir un valor basta con editar la fila correspondiente.
TABLA_NC = {
    10: (58, 77, 89, 72, 86, 93, 81, 91, 96, 87, 94, 97),
    20: (52, 72, 86, 64, 81, 91, 75, 88, 94, 81, 91, 96),
    30: (46, 67, 82, 60, 78, 89, 70, 85, 93, 77, 89, 95),
    40: (49, 70, 84, 61, 79, 90, 69, 84, 92, 75, 88, 94),
    50: (44, 65, 81, 56, 75, 87, 66, 82, 91, 72, 86, 93),
    60: (45, 66, 82, 54, 74, 87, 63, 80, 90, 66, 82, 91),
    70: (41, 62, 79, 51, 71, 85, 60, 78, 89, 64, 81, 91),
    80: (44, 65, 81, 57, 76, 88, 69, 84, 92, 75, 88, 94),
    90: (42, 63, 80, 56, 75, 87, 67, 83, 92, 74, 87, 94),
    100: (42, 63, 80, 54, 74, 87, 66, 82, 91, 70, 85, 93),
    110: (40, 61, 78, 53, 73, 86, 64, 81, 91, 69, 84, 92),
    120: (40, 61, 78, 52, 72, 86, 61, 79, 90, 66, 82, 91),
    130: (38, 59, 77, 49, 70, 84, 60, 78, 89, 64, 81, 91),
    140: (45, 66, 82, 58, 77, 89, 69, 84, 92, 75, 88, 94),
    150: (37, 58, 76, 52, 72, 86, 64, 81, 91, 70, 85, 93),
    160: (43, 64, 80, 56, 75, 87, 67, 83, 92, 70, 85, 93),
    170: (34, 55, 74, 48, 69, 84, 60, 78, 89, 67, 83, 92),
    180: (42, 63, 80, 53, 73, 86, 63, 80, 90, 67, 83, 92),
    190: (30, 51, 71, 46, 67, 82, 57, 76, 88, 63, 80, 90),
    200: (28, 48, 68, 46, 67, 82, 58, 77, 89, 67, 83, 92),
    210: (18, 35, 55, 35, 56, 75, 49, 70, 84, 58, 77, 89),
    220: (15, 30, 50, 28, 48, 68, 44, 65, 81, 53, 73, 86),
    230: (26, 45, 65, 45, 66, 82, 58, 77, 89, 67, 83, 92),
    240: (19, 36, 56, 39, 60, 78, 53, 73, 86, 61, 79, 90),
    250: (12, 25, 43, 34, 55, 74, 49, 70, 84, 58, 77, 89),
    260: (35, 56, 75, 56, 75, 87, 72, 86, 93, 81, 91, 96),
    270: (26, 46, 66, 47, 68, 83, 60, 78, 89, 69, 84, 92),
    280: (19, 36, 56, 39, 60, 78, 49, 70, 84, 57, 76, 88),
    290: (13, 26, 45, 31, 52, 71, 42, 63, 80, 48, 69, 84),
    300: (7, 15, 29, 25, 44, 64, 33, 54, 73, 40, 61, 78),
    310: (15, 30, 50, 37, 58, 76, 51, 71, 85, 60, 78, 89),
    320: (47, 68, 83, 61, 79, 90, 72, 86, 93, 77, 89, 95),
    330: (29, 49, 69, 48, 69, 84, 61, 79, 90, 69, 84, 92),
    340: (21, 39, 60, 40, 61, 78, 54, 74, 87, 63, 80, 90),
    350: (27, 47, 67, 46, 67, 82, 64, 81, 91, 75, 88, 94),
    360: (12, 25, 43, 38, 59, 77, 56, 75, 87, 67, 83, 92),
    370: (3, 6, 13, 18, 35, 55, 49, 70, 84, 61, 79, 90),
    380: (33, 54, 73, 49, 70, 84, 63, 80, 90, 70, 85, 93),
    390: (58, 77, 89, 70, 85, 93, 79, 90, 95, 83, 92, 96),
    400: (95, 98, 99, 95, 98, 99, 95, 98, 99, 95, 98, 99),
    410: (100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100, 100),
    420: (27, 47, 67, 45, 66, 82, 58, 77, 89, 67, 83, 92),
    430: (37, 57, 73, 52, 72, 86, 66, 82, 91, 72, 86, 93),
    440: (40, 61, 78, 56, 75, 87, 67, 77, 84, 74, 83, 91),
    450: (37, 57, 73, 52, 72, 86, 64, 81, 91, 72, 86, 93),
    460: (30, 51, 71, 47, 68, 83, 63, 79, 90, 69, 84, 92),
    470: (20, 37, 57, 39, 60, 78, 53, 73, 86, 61, 79, 90),
    480: (22, 42, 61, 40, 62, 78, 57, 75, 91, 64, 81, 91),
    490: (29, 49, 69, 45, 65, 83, 56, 75, 87, 61, 79, 90),
    500: (18, 35, 55, 38, 59, 77, 52, 72, 86, 61, 79, 90),
    510: (29, 49, 69, 47, 68, 83, 60, 78, 89, 69, 84, 92),
    520: (42, 63, 80, 58, 77, 89, 70, 85, 93, 75, 88, 94),
    530: (65, 83, 95, 84, 93, 97, 84, 93, 97, 84, 93, 97),
    540: (65, 83, 95, 84, 93, 97, 84, 93, 97, 84, 93, 97),
    550: (80, 91, 96, 80, 91, 96, 81, 91, 96, 82, 92, 97),
    560: (77, 89, 97, 82, 92, 98, 88, 94, 98, 87, 95, 99),
    570: (29, 49, 69, 48, 69, 84, 61, 79, 90, 69, 84, 92),
    580: (15, 30, 50, 37, 58, 76, 51, 71, 85, 60, 78, 89),
}

# Descripción de cada código de cobertura (Tabla 2 del manual):
#   Cod_Veg: (Cobertura del Suelo de la República Argentina - PNECO 1643,
#             Vegetación y/o uso del suelo - Mintegui Aguirre y López Unzú)
# Referencias del manual: R laboreo sin prácticas de conservación; C curvas
# de nivel; C-T curvas de nivel y terrazas abiertas; condición de
# infiltración MP muy pobre, P pobre, M mala, B buena, MB muy buena.
_NO_ALINEADOS = 'Cultivos no alineados o surcos pequeños'
_INUNDABLES = 'en áreas regularmente inundadas/anegadas o acuáticas'
COBERTURAS = {
    10: ('Áreas naturales desnudas consolidadas', 'Barbecho'),
    20: ('Herbáceas cerradas ' + _INUNDABLES, 'Cultivos alineados R P'),
    30: ('Cultivos de herbáceas graminoides', 'Cultivos alineados R B'),
    40: ('', 'Cultivos alineados C P'),
    50: ('', 'Cultivos alineados C B'),
    60: ('', 'Cultivos alineados C-T P'),
    70: ('', 'Cultivos alineados C-T B'),
    80: ('', _NO_ALINEADOS + ' R P'),
    90: ('Cultivos de herbáceas (no determinado)', _NO_ALINEADOS + ' R B'),
    100: ('', _NO_ALINEADOS + ' C P'),
    110: ('', _NO_ALINEADOS + ' C B'),
    120: ('', _NO_ALINEADOS + ' C-T P'),
    130: ('', _NO_ALINEADOS + ' C-T B'),
    140: ('', 'Cultivos densos leguminosas R P'),
    150: ('Cultivos de herbáceas no graminoides',
          'Cultivos densos leguminosas R B'),
    160: ('', 'Cultivos densos leguminosas C P'),
    170: ('', 'Cultivos densos leguminosas C B'),
    180: ('', 'Cultivos densos leguminosas C-T P'),
    190: ('', 'Cultivos densos leguminosas C-T B'),
    200: ('', 'Matorral, mezcla matorral y maleza. Cubierta 50%'),
    210: ('', 'Matorral, mezcla matorral y maleza. Cubierta 50-75%'),
    220: ('', 'Matorral, mezcla matorral y maleza. Cubierta >75%'),
    230: ('Arbustal abierto', 'Montes con pastos P'),
    240: ('Arbustal disperso', 'Montes con pastos R'),
    250: ('Arbustal cerrado', 'Montes con pastos B'),
    260: ('Bosques abiertos ' + _INUNDABLES, 'Bosques MP'),
    270: ('Bosques abiertos', 'Bosques P'),
    280: ('Bosques abiertos, con arbustos', 'Bosques R'),
    290: ('Bosques cerrados ' + _INUNDABLES, 'Bosques B'),
    300: ('Bosques cerrados', 'Bosques MB'),
    310: ('Áreas terrestres cultivadas y/o manejadas', 'Prados permanentes'),
    320: ('Pastizal abierto (herbáceas graminoides)', 'Pastizal P'),
    330: ('Pastizal disperso', 'Pastizal R'),
    340: ('Pastizal cerrado (herbáceas graminoides)', 'Pastizal B'),
    350: ('', 'Pastizal C P'),
    360: ('', 'Pastizal C R'),
    370: ('', 'Pastizal C B'),
    380: ('Áreas urbanas de baja densidad', 'Residencial baja densidad'),
    390: ('Áreas urbanas densamente pobladas', 'Residencial alta densidad'),
    400: ('Rocas, fragmentos', 'Superficies impermeables'),
    410: ('Cuerpos de agua en movimiento (cañadas) o estacionarios (bañado). '
          'Nieve o hielo', 'Espejos de agua - humedales'),
    420: ('Árboles dispersos ' + _INUNDABLES, ''),
    430: ('Arbustal cerrado a abierto ' + _INUNDABLES, ''),
    440: ('Áreas urbanas de densidad media', ''),
    450: ('Áreas urbanas dispersas - semiurbanas', ''),
    460: ('Áreas urbanas vegetadas', ''),
    470: ('Cultivos de arbustos bajo riego', ''),
    480: ('Cultivos de arbustos en secano', ''),
    490: ('Cultivos de especies arbóreas (no determinado)', ''),
    500: ('Cultivos de especies arbóreas bajo riego', ''),
    510: ('Cultivos de especies arbóreas en secano', ''),
    520: ('Dunas / desiertos naturales', ''),
    530: ('Salares (GH D - áreas/rocas impermeables)', ''),
    540: ('Salinas (GH D - áreas/rocas impermeables)', ''),
    550: ('Suelos pedregosos', ''),
    560: ('Superficies artificiales y áreas asociadas. Superficies '
          'construidas (no determinado) - Distritos urbanos comerciales', ''),
    570: ('Superficies no construidas', ''),
    580: ('Vegas de ríos en condiciones óptimas', ''),
}


def _a_entero(valor):
    """Convierte un atributo (número o texto) en entero, o None."""
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        return valor
    if not isinstance(valor, float):
        try:
            valor = float(str(valor).strip().replace(',', '.'))
        except ValueError:
            return None
    if not math.isfinite(valor) or valor != int(valor):
        return None
    return int(valor)


def codigo_suelo(valor):
    """Devuelve el código de grupo hidrológico (1 a 4) o None si no es válido.

    Acepta tanto el código numérico (1, 2, 3, 4) como la letra del grupo
    hidrológico (A, B, C, D).
    """
    if isinstance(valor, str):
        letra = valor.strip().upper()
        if letra in GRUPOS_HIDROLOGICOS:
            return GRUPOS_HIDROLOGICOS[letra]
    codigo = _a_entero(valor)
    return codigo if codigo in (1, 2, 3, 4) else None


def codigo_cobertura(valor):
    """Devuelve el código de cobertura (Cod_Veg) o None si no es válido."""
    codigo = _a_entero(valor)
    return codigo if codigo in TABLA_NC else None


def numero_curva(cod_sue, cod_veg, cha):
    """Número de Curva para un grupo de suelo, una cobertura y una CHA.

    :param cod_sue: código de grupo hidrológico, 1 (A) a 4 (D).
    :param cod_veg: código de cobertura (10, 20, ... 580).
    :param cha: índice de la CHA: 0 (I), 1 (II) o 2 (III).
    """
    return TABLA_NC[cod_veg][(cod_sue - 1) * 3 + cha]


def balance(nc, pp):
    """Aplica el método del Número de Curva a una precipitación.

    :param nc: Número de Curva (mayor que 0 y hasta 100).
    :param pp: precipitación del evento, en mm.
    :returns: diccionario con S, Io, Q y F en mm, y los coeficientes CIo, CE
        y CF en porcentaje de la precipitación (CIo + CE + CF = 100).

    S e Io dependen solo del Número de Curva (son la capacidad de retención
    del complejo suelo-cobertura), por lo que se informan siempre.

    Si la precipitación no supera las abstracciones iniciales (PP <= Io) no
    hay escorrentía ni infiltración: Q = F = 0 y toda la lluvia queda
    retenida (CIo = 100). Si no hay lluvia (PP = 0) no hay nada que repartir
    y los tres coeficientes valen 0.
    """
    s = 254.0 * (100.0 / nc - 1.0)
    io = 0.2 * s
    if pp <= 0:
        q = f = ce = cf = cio = 0.0
    elif pp <= io:
        q = f = ce = cf = 0.0
        cio = 100.0
    else:
        q = (pp - io) ** 2 / (pp + 0.8 * s)
        f = s * (pp - io) / (pp - io + s)
        ce = q / pp * 100.0
        cf = f / pp * 100.0
        cio = io / pp * 100.0
    return {'S': s, 'Io': io, 'CIo': cio, 'Q': q, 'CE': ce, 'F': f, 'CF': cf}
