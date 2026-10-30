"""Entrevista por voz para la historia clínica.

La idea: la podóloga aprieta un botón, la pantalla le va mostrando (y leyendo en
voz alta) una pregunta por vez, ella dicta la respuesta del paciente y acá se
traduce ese texto hablado a los valores que espera el formulario.

El guion se arma a partir de los choices de models.py, así que si mañana se
agrega un medicamento o una patología al modelo, la entrevista lo toma sola.

No hace falta ninguna API paga: la transcripción la hace el navegador y el
reconocimiento de la respuesta es la comparación de texto que está acá abajo.
Si en algún momento se quiere sumar un modelo de lenguaje para los casos que no
se entienden, está el hook de n8n al final del archivo.
"""

import difflib
import re
import unicodedata
from datetime import date

from django.conf import settings

from .models import (
    ActividadFisica,
    Alergia,
    AnticoagulanteMedicamentos,
    ColesterolMedicamentos,
    DiabetesTipo,
    EnfermedadesL,
    EnfermedadesNeuropatias,
    EnfermedadesRespiratorias,
    EnfermedadesReumatologicas,
    EnfermedadesVasculares,
    Hipertension,
    HipertensionMedicamentos,
    MedicamentosDiabetes,
    PatologiasPieDerecho,
    PatologiasPieIzquierdo,
    TipoPie,
    Colesterol,
    Anticoagulante,
    plantillas,
)

# Palabras que significan "no tiene nada de esto".
NEGATIVAS = {
    'no', 'ninguno', 'ninguna', 'ningun', 'nada', 'negativo', 'nunca',
    'tampoco', 'niega', 'nop',
}

# Palabras que significan "sí tiene", para los campos de sí/no.
AFIRMATIVAS = {
    'si', 'sip', 'claro', 'correcto', 'afirmativo', 'exacto', 'positivo',
    'obvio', 'tiene', 'toma', 'padece', 'sufre', 'efectivamente',
}

# Comandos que no son respuestas sino instrucciones para la entrevista.
COMANDOS = {
    'siguiente': ('siguiente', 'continuar', 'proxima', 'proximo', 'adelante', 'dale'),
    'atras': ('atras', 'volver', 'anterior', 'retroceder'),
    'repetir': ('repetir', 'repeti', 'de nuevo', 'otra vez', 'no entendi'),
    'saltear': ('saltear', 'saltar', 'omitir', 'pasar'),
    'terminar': ('terminar', 'terminamos', 'finalizar', 'cerrar', 'basta'),
    # Sin "otro" ni "otra" a secas: chocarían con la opción "Otras" de
    # enfermedades, que es una respuesta válida y no un comando.
    'otro': ('no esta en la lista', 'ninguno de esos', 'ninguna de esas',
             'anotar aparte', 'no figura'),
    # Para volver a abrir la entrevista entera desde el dictado suelto.
    'empezar': ('empezar entrevista', 'empezar la entrevista',
                'empezar historia clinica', 'arrancar entrevista',
                'abrir entrevista', 'empezar de nuevo'),
}

ETIQUETAS_DICTADO = {
    'observaciones': 'Observaciones',
    'antecedentes_familiares': 'Antecedentes familiares',
    'motivo_consulta': 'Motivo de consulta',
    'descripcion_seguimiento': 'Seguimiento',
}


def etiqueta_de(campo):
    return ETIQUETAS_DICTADO.get(campo, campo)

# Cómo puede llegar a decirlo en voz alta, más allá de la etiqueta del modelo.
# La clave es el slug guardado en la base.
SINONIMOS = {
    # sí / no
    'si': tuple(AFIRMATIVAS),
    # alergias
    'comidas': ('comida', 'alimento', 'alimentos', 'alimentaria', 'alimenticia'),
    'estacional': ('polen', 'primavera', 'estacionales'),
    'insectos': ('insecto', 'picadura', 'picaduras', 'abeja', 'avispa'),
    'medicamentos': ('medicamento', 'remedio', 'remedios', 'farmaco', 'farmacos',
                     'medicacion'),
    # enfermedades generales
    'cardiopatias': ('cardiopatia', 'corazon', 'cardiaco', 'cardiaca', 'cardiacas',
                     'del corazon', 'cardiovascular'),
    'cirugias': ('cirugia', 'operacion', 'operaciones', 'operado', 'operada',
                 'operaron', 'operaba', 'intervencion', 'quirurgica'),
    'fumador': ('fuma', 'fumadora', 'tabaquismo', 'cigarrillo', 'cigarrillos',
                'tabaco'),
    'hpv': ('papiloma', 'verruga', 'verrugas', 'virus del papiloma'),
    'otras': ('otra', 'otro', 'otros'),
    # diabetes
    'tipo_1': ('tipo 1', 'tipo uno', 'uno', 'insulinodependiente',
               'insulino dependiente'),
    'tipo_2': ('tipo 2', 'tipo dos', 'dos'),
    'gestacional': ('embarazo', 'del embarazo'),
    'prediabetes': ('pre diabetes', 'pre diabetica', 'prediabetica'),
    'metformina': ('glucofage',),
    # tipo de pie
    'normal': ('sano', 'sanos', 'sin alteraciones', 'bien', 'normales'),
    'cavo': ('pie cavo', 'cava'),
    'plano': ('pie plano', 'planos'),
    'varo': ('pie varo',),
    'valgo': ('pie valgo',),
    # patologías del pie
    'ampollas': ('ampolla', 'flictena'),
    'amputaciones': ('amputacion', 'amputado', 'amputada'),
    'grietas': ('grieta', 'fisura', 'fisuras', 'talon agrietado'),
    'helomas': ('heloma', 'callo', 'callos', 'ojo de gallo', 'ojo de pollo'),
    'hiperqueratosis': ('queratosis', 'dureza', 'durezas', 'piel dura',
                        'hiperqueratosica'),
    'onicocriptosis': ('una encarnada', 'unas encarnadas', 'unero', 'encarnada',
                       'encarnadas', 'clavada'),
    'onicomicosis': ('hongo', 'hongos', 'micosis'),
    'osteopatias': ('osteopatia', 'hueso', 'huesos', 'oseo'),
    'ulceras': ('ulcera', 'llaga', 'llagas', 'herida abierta'),
    # respiratorias
    'epoc': ('e pe o ce',),
    'hipertension_pulmonar': ('pulmonar',),
    'neumonia': ('neumonias', 'pulmonia'),
    # reumatológicas
    'artritis_reumatoidea': ('artritis', 'reumatoidea', 'reuma'),
    'artritis_idiopatica_juvenil': ('idiopatica', 'juvenil'),
    'lumbago_y_ciatico': ('lumbago', 'ciatico', 'ciatica', 'lumbalgia'),
    'esclerosis_sistemica': ('esclerosis',),
    'espondilitis_anquilosante': ('espondilitis',),
    # vasculares
    'acv': ('a ce uve', 'derrame', 'accidente cerebrovascular', 'ictus'),
    'eap': ('e a pe', 'arteriopatia'),
    'edema': ('edemas', 'hinchazon', 'hinchado', 'hinchada', 'retencion'),
    'trombosis': ('trombo', 'trombos'),
    'varices': ('varice', 'varicosas', 'variz'),
}


def _normalizar(texto):
    """Pasa a minúsculas, saca tildes y deja solo letras, números y espacios."""
    texto = unicodedata.normalize('NFKD', texto or '')
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    texto = texto.lower()
    # La descomposición de arriba ya convirtió la ñ en n, así que acá alcanza
    # con quedarse con el alfabeto básico.
    texto = re.sub(r'[^a-z0-9\s]', ' ', texto)
    return re.sub(r'\s+', ' ', texto).strip()


def _frases_de(opcion):
    """Todas las formas de nombrar una opción, de la más larga a la más corta."""
    frases = {_normalizar(opcion['texto']),
              _normalizar(opcion['slug'].replace('_', ' '))}
    frases.update(_normalizar(s) for s in SINONIMOS.get(opcion['slug'], ()))
    return sorted((f for f in frases if f), key=len, reverse=True)


def _peso_coincidencia(texto, opcion):
    """Cuánto pesa la mención de una opción en lo dicho. Cero si no aparece."""
    for frase in _frases_de(opcion):
        if re.search(r'\b' + re.escape(frase) + r'\b', texto):
            return len(frase)
    return 0


def _es_negativa(opcion):
    return opcion['slug'] in ('no', 'ninguno', 'ninguna')


def _opcion_negativa(paso):
    for opcion in paso['opciones']:
        if _es_negativa(opcion):
            return opcion
    return None


# Con el micrófono siempre abierto, lo que se charla con el paciente se puede
# colar como respuesta. Con el activador puesto, solo cuenta lo que arranca
# con una de estas palabras: así cada dato cargado es deliberado.
ACTIVADORES = (
    'anota', 'anotar', 'anotale', 'anotalo', 'anotame',
    'pone', 'poner', 'ponele', 'escribi', 'cargale', 'marca', 'marcar',
)


def quitar_activador(texto):
    """Devuelve lo que viene después de la palabra clave.

    None si no la dijo, que es la señal para ignorar la frase entera. Se corta
    sobre el texto original, no sobre el normalizado, para no perderle los
    acentos ni las mayúsculas a los nombres propios.
    """
    palabras = (texto or '').strip().split()
    if not palabras:
        return None
    if _normalizar(palabras[0]) not in ACTIVADORES:
        return None
    return ' '.join(palabras[1:]).lstrip(' ,.:;')


# Cómo se puede nombrar cada campo de texto al dictar suelto, después de
# terminar la entrevista. El primero de la lista es el destino por defecto.
DESTINOS_DICTADO = (
    ('observaciones', ('observaciones', 'observacion', 'la observacion',
                       'las observaciones')),
    ('antecedentes_familiares', ('antecedentes familiares', 'antecedentes',
                                 'los antecedentes')),
    ('motivo_consulta', ('motivo de consulta', 'motivo de la consulta',
                         'motivo', 'el motivo')),
    ('descripcion_seguimiento', ('seguimiento', 'el seguimiento',
                                 'la evolucion', 'evolucion')),
)

# Preposiciones y artículos que se cuelan entre la palabra clave y el campo:
# "anotá EN LAS observaciones que...".
_RELLENO = ('en', 'a', 'la', 'las', 'el', 'los', 'que', 'de')


def interpretar_dictado(texto, campos_posibles):
    """Reparte un dictado suelto al campo que corresponda.

    "anotá en observaciones que le duele el talón" devuelve
    ("observaciones", "le duele el talón"). Sin palabra clave devuelve None,
    porque en este modo el micrófono queda abierto escuchando la consulta
    entera y solo nos interesa lo que se dicta a propósito. Si no se nombra
    ningún campo, va al primero de DESTINOS_DICTADO que exista en la página.
    """
    resto = quitar_activador(texto)
    if resto is None:
        return None

    palabras = resto.split()
    disponibles = [(campo, alias) for campo, alias in DESTINOS_DICTADO
                   if campo in campos_posibles]
    if not disponibles:
        return None

    # Buscamos el nombre del campo saltando las palabras de relleno.
    for campo, alias in disponibles:
        for nombre in sorted(alias, key=len, reverse=True):
            largo = len(nombre.split())
            for salto in range(0, 4):
                if len(palabras) < salto + largo:
                    continue
                previas = [_normalizar(p) for p in palabras[:salto]]
                if any(p not in _RELLENO for p in previas):
                    continue
                candidato = ' '.join(_normalizar(p)
                                     for p in palabras[salto:salto + largo])
                if candidato == nombre:
                    dicho = ' '.join(palabras[salto + largo:])
                    return campo, _sacar_relleno_inicial(dicho)

    # No nombró ningún campo: va al cajón de siempre.
    return disponibles[0][0], _sacar_relleno_inicial(resto)


def _sacar_relleno_inicial(texto):
    """Saca el "que" de "anotá en observaciones QUE le duele el talón"."""
    palabras = texto.split()
    while palabras and _normalizar(palabras[0]) in ('que', 'lo', 'siguiente'):
        palabras.pop(0)
    return ' '.join(palabras).lstrip(' ,.:;')


def detectar_comando(texto):
    """Devuelve el comando de navegación dicho, o None si es una respuesta común."""
    t = _normalizar(texto)
    for comando, frases in COMANDOS.items():
        for frase in frases:
            if t == frase or t == frase + ' por favor':
                return comando
    return None


# ---------------------------------------------------------------------------
# Números y fechas dichos en voz alta
# ---------------------------------------------------------------------------

PALABRAS_NUMERO = {
    # "primero" es el único ordinal que se usa para los días: "el primero de
    # enero", pero "el dos de enero".
    'cero': 0, 'un': 1, 'uno': 1, 'una': 1, 'primero': 1,
    'dos': 2, 'tres': 3, 'cuatro': 4,
    'cinco': 5, 'seis': 6, 'siete': 7, 'ocho': 8, 'nueve': 9, 'diez': 10,
    'once': 11, 'doce': 12, 'trece': 13, 'catorce': 14, 'quince': 15,
    'dieciseis': 16, 'diecisiete': 17, 'dieciocho': 18, 'diecinueve': 19,
    'veinte': 20, 'veintiuno': 21, 'veintiun': 21, 'veintidos': 22,
    'veintitres': 23, 'veinticuatro': 24, 'veinticinco': 25, 'veintiseis': 26,
    'veintisiete': 27, 'veintiocho': 28, 'veintinueve': 29,
    'treinta': 30, 'cuarenta': 40, 'cincuenta': 50, 'sesenta': 60,
    'setenta': 70, 'ochenta': 80, 'noventa': 90,
    'cien': 100, 'ciento': 100, 'doscientos': 200, 'trescientos': 300,
    'cuatrocientos': 400, 'quinientos': 500, 'seiscientos': 600,
    'setecientos': 700, 'ochocientos': 800, 'novecientos': 900,
}

MESES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4, 'mayo': 5, 'junio': 6,
    'julio': 7, 'agosto': 8, 'septiembre': 9, 'setiembre': 9, 'octubre': 10,
    'noviembre': 11, 'diciembre': 12,
}


def _numero_en_palabras(texto):
    """Convierte "treinta y ocho" en 38, o devuelve None si no hay número."""
    total = 0
    parcial = 0
    hubo = False
    for palabra in texto.split():
        if palabra == 'y':
            continue
        if palabra == 'mil':
            total += (parcial or 1) * 1000
            parcial = 0
            hubo = True
        elif palabra in PALABRAS_NUMERO:
            parcial += PALABRAS_NUMERO[palabra]
            hubo = True
    return total + parcial if hubo else None


def _numero_de(texto):
    """Saca un número de lo dicho, venga en cifras o en palabras."""
    cifras = re.findall(r'\d+', texto)
    if cifras:
        return int(''.join(cifras))
    return _numero_en_palabras(texto)


def _interpretar_numero(paso, texto):
    t = _normalizar(texto)

    # "un metro sesenta" o "uno sesenta" son 160 cm, no 1 ni 160 sueltos.
    if paso.get('es_altura'):
        metros = re.search(r'\b(un|uno|1)\s+(metro|metros)?\s*(.*)$', t)
        if metros:
            resto = _numero_de(metros.group(3) or '')
            if resto is not None and resto < 100:
                return _resultado_numero(paso, 100 + resto)

    numero = _numero_de(t)
    if numero is None:
        return {'valores': [], 'textos': [], 'confianza': 'nula', 'candidatos': []}
    return _resultado_numero(paso, numero)


def _resultado_numero(paso, numero):
    # Fuera de rango no lo descartamos, pero pedimos que lo confirme: puede ser
    # un error de transcripción tanto como un dato raro pero real.
    minimo, maximo = paso.get('rango', (None, None))
    razonable = ((minimo is None or numero >= minimo)
                 and (maximo is None or numero <= maximo))
    return {
        'valores': [str(numero)],
        'textos': [str(numero)],
        'confianza': 'alta' if razonable else 'media',
        'candidatos': [],
    }


def _interpretar_fecha(paso, texto):
    """Entiende "2 de mayo de 1960", "dos de mayo del sesenta" y "2/5/1960"."""
    t = _normalizar(texto)
    dia = mes = anio = None

    for nombre, numero in MESES.items():
        if re.search(r'\b' + nombre + r'\b', t):
            antes, _, despues = t.partition(nombre)
            mes = numero
            dia = _numero_de(antes)
            anio = _numero_de(despues)
            break

    if mes is None:
        # Sin nombre de mes, esperamos tres números: día, mes y año.
        sueltos = [int(n) for n in re.findall(r'\d+', t)]
        if len(sueltos) == 3:
            dia, mes, anio = sueltos

    if not (dia and mes and anio):
        return {'valores': [], 'textos': [], 'confianza': 'nula', 'candidatos': []}

    # "del sesenta" es 1960; nadie que venga a la consulta nació en el año 60.
    if anio < 100:
        anio += 2000 if anio <= 25 else 1900

    try:
        fecha = date(anio, mes, dia)
    except ValueError:
        return {'valores': [], 'textos': [], 'confianza': 'nula', 'candidatos': []}

    hoy = date.today()
    sensata = date(hoy.year - 120, 1, 1) <= fecha <= hoy
    return {
        'valores': [fecha.isoformat()],
        'textos': [fecha.strftime('%d/%m/%Y')],
        'confianza': 'alta' if sensata else 'media',
        'candidatos': [],
    }


def _interpretar_frase(texto):
    """Textos cortos de una sola tirada: nombres, domicilios, localidades."""
    limpio = re.sub(r'\s+', ' ', (texto or '').strip().rstrip('.,'))
    if not limpio:
        return {'valores': [], 'textos': [], 'confianza': 'nula', 'candidatos': []}
    # El dictado suele venir todo en minúscula y son nombres propios.
    bonito = ' '.join(p[:1].upper() + p[1:] for p in limpio.split())
    return {'valores': [bonito], 'textos': [bonito], 'confianza': 'alta',
            'candidatos': []}


def interpretar(paso, texto):
    """Traduce lo dicho a los valores que espera el campo del formulario.

    La confianza es 'alta' cuando la opción se nombró textualmente, 'media'
    cuando hubo que acercarse por parecido y 'nula' cuando no se entendió: en
    ese último caso vienen candidatos para elegir a mano.
    """
    if paso['tipo'] == 'texto':
        limpio = (texto or '').strip()
        return {
            'valores': [limpio] if limpio else [],
            'textos': [limpio] if limpio else [],
            'confianza': 'alta' if limpio else 'nula',
            'candidatos': [],
        }

    if paso['tipo'] == 'frase':
        return _interpretar_frase(texto)

    if paso['tipo'] == 'numero':
        return _interpretar_numero(paso, texto)

    if paso['tipo'] == 'fecha':
        return _interpretar_fecha(paso, texto)

    t = _normalizar(texto)
    if not t:
        return {'valores': [], 'textos': [], 'confianza': 'nula', 'candidatos': []}

    # Primero buscamos menciones concretas: "tipo 2", "metformina", "hongos".
    # Las negativas quedan afuera para que "no, tipo 2" se resuelva como tipo 2.
    encontradas = []
    for opcion in paso['opciones']:
        if _es_negativa(opcion):
            continue
        peso = _peso_coincidencia(t, opcion)
        if peso:
            encontradas.append((peso, opcion))

    if encontradas:
        encontradas.sort(key=lambda par: par[0], reverse=True)
        if paso['tipo'] == 'opciones':
            elegidas = [opcion for _, opcion in encontradas]
        else:
            elegidas = [encontradas[0][1]]
        return {
            'valores': [o['valor'] for o in elegidas],
            'textos': [o['texto'] for o in elegidas],
            'confianza': 'alta',
            'candidatos': [],
        }

    # Sin menciones concretas: ¿dijo que no tiene nada?
    if set(t.split()) & NEGATIVAS:
        negativa = _opcion_negativa(paso)
        if negativa:
            return {
                'valores': [negativa['valor']],
                'textos': [negativa['texto']],
                'confianza': 'alta',
                'candidatos': [],
            }
        # En los campos de selección múltiple, "ninguna" es no tildar nada.
        return {'valores': [], 'textos': ['Ninguna'], 'confianza': 'alta',
                'candidatos': []}

    # Último intento antes de rendirse: parecido aproximado con las etiquetas.
    etiquetas = {_normalizar(o['texto']): o for o in paso['opciones']}
    parecidas = difflib.get_close_matches(t, list(etiquetas), n=3, cutoff=0.6)
    if parecidas:
        return {
            'valores': [etiquetas[parecidas[0]]['valor']],
            'textos': [etiquetas[parecidas[0]]['texto']],
            'confianza': 'media',
            'candidatos': [etiquetas[p] for p in parecidas],
        }

    delegado = _consultar_n8n(paso, texto)
    if delegado is not None:
        return delegado

    cercanas = sorted(
        paso['opciones'],
        key=lambda o: difflib.SequenceMatcher(None, t, _normalizar(o['texto'])).ratio(),
        reverse=True,
    )
    return {'valores': [], 'textos': [], 'confianza': 'nula',
            'candidatos': cercanas[:3]}


# ---------------------------------------------------------------------------
# El guion de la entrevista
# ---------------------------------------------------------------------------

def _paso_opcion(campo, etiqueta, pregunta, choices, omitir_si=None):
    """Un campo de una sola respuesta (los Select del formulario)."""
    return {
        'campo': campo,
        'etiqueta': etiqueta,
        'pregunta': pregunta,
        'tipo': 'opcion',
        'opciones': [{'valor': valor, 'texto': texto, 'slug': valor}
                     for valor, texto in choices],
        'omitir_si': omitir_si,
    }


def _paso_opciones(campo, etiqueta, pregunta, modelo):
    """Un campo de varias respuestas (los ManyToMany con checkboxes).

    El checkbox espera la pk de la fila, no el slug, así que las opciones salen
    de la base y no de los choices.
    """
    return {
        'campo': campo,
        'etiqueta': etiqueta,
        'pregunta': pregunta,
        'tipo': 'opciones',
        'opciones': [{'valor': str(obj.pk), 'texto': obj.get_nombre_display(),
                      'slug': obj.nombre}
                     for obj in modelo.objects.all()],
        'omitir_si': None,
    }


def _paso_texto(campo, etiqueta, pregunta):
    return {
        'campo': campo,
        'etiqueta': etiqueta,
        'pregunta': pregunta,
        'tipo': 'texto',
        'opciones': [],
        'omitir_si': None,
    }


def _paso_simple(campo, etiqueta, pregunta, tipo, **extra):
    """Campos de una sola respuesta corta: frases, números y fechas."""
    paso = {
        'campo': campo,
        'etiqueta': etiqueta,
        'pregunta': pregunta,
        'tipo': tipo,
        'opciones': [],
        'omitir_si': None,
    }
    paso.update(extra)
    return paso


def construir_guion():
    """El orden en que se hacen las preguntas durante la consulta.

    Primero el interrogatorio (que es lo que se charla sentados) y después la
    revisación de los pies, que es cuando tiene las manos ocupadas.
    """
    return [
        _paso_opciones(
            'alergias', 'Alergias',
            '¿Es alérgico a algo? Podés nombrar varias: comidas, estacional, '
            'insectos o medicamentos.',
            Alergia),
        _paso_opciones(
            'enfermedades', 'Enfermedades',
            '¿Tiene cardiopatías, cirugías previas, HPV, o es fumador?',
            EnfermedadesL),
        _paso_opcion(
            'diabetes', 'Diabetes',
            '¿Tiene diabetes? Si tiene, decime de qué tipo.',
            DiabetesTipo.TIPO_DIABETES_CHOICES),
        _paso_opcion(
            'medicamentos_diabetes', 'Medicación para la diabetes',
            '¿Qué medicación toma para la diabetes?',
            MedicamentosDiabetes.MEDICAMENTOS_DIABETES_CHOICES,
            omitir_si={'campo': 'diabetes', 'valores': ['no']}),
        _paso_opcion(
            'colesterol', 'Colesterol',
            '¿Tiene colesterol alto?',
            Colesterol.COLESTEROL_CHOICES),
        _paso_opcion(
            'medicamentos_colesterol', 'Medicación para el colesterol',
            '¿Qué medicación toma para el colesterol?',
            ColesterolMedicamentos.MEDICAMENTO_COLESTEROL_CHOICES,
            omitir_si={'campo': 'colesterol', 'valores': ['no']}),
        _paso_opcion(
            'hipertension', 'Hipertensión',
            '¿Es hipertenso?',
            Hipertension.HIPERTENSION_CHOICES),
        _paso_opcion(
            'hipertension_medicamentos', 'Medicación para la presión',
            '¿Qué medicación toma para la presión?',
            HipertensionMedicamentos.HIPERTENSION_MEDICAMENTOS_CHOICES,
            omitir_si={'campo': 'hipertension', 'valores': ['no']}),
        _paso_opcion(
            'anticoagulante', 'Anticoagulantes',
            '¿Toma anticoagulantes?',
            Anticoagulante.TIPO_ANTICOAGULANTE_CHOICES),
        _paso_opcion(
            'anticoagulante_medicamentos', 'Cuál anticoagulante',
            '¿Cuál anticoagulante toma?',
            AnticoagulanteMedicamentos.TIPO_ANTICOAGULANTEMEDICAMENTOS_CHOICES,
            omitir_si={'campo': 'anticoagulante', 'valores': ['no']}),
        _paso_opcion(
            'enfermedades_respiratorias', 'Enfermedades respiratorias',
            '¿Tiene alguna enfermedad respiratoria? Asma, bronquitis, EPOC...',
            EnfermedadesRespiratorias.TIPO_ENFERMEDAD_RESPIRATORIA_CHOICES),
        _paso_opcion(
            'enfermedades_reumatologicas', 'Enfermedades reumatológicas',
            '¿Tiene artrosis, artritis, gota o alguna otra reumatológica?',
            EnfermedadesReumatologicas.TIPO_ENFERMEDAD_REUMATOLOGICA_CHOICES),
        _paso_opcion(
            'enfermedades_vasculares', 'Enfermedades vasculares',
            '¿Tiene problemas de circulación? Várices, edemas, trombosis...',
            EnfermedadesVasculares.TIPO_ENFERMEDAD_VASCULAR_CHOICES),
        _paso_opcion(
            'enfermedades_neuropatias', 'Neuropatías',
            '¿Tiene neuropatías? Hormigueo o pérdida de sensibilidad en los pies.',
            EnfermedadesNeuropatias.TIPO_ENFERMEDAD_NEUROPATIA_CHOICES),
        _paso_opcion(
            'tipo_pie_derecho', 'Tipo de pie derecho',
            'Pie derecho: ¿normal, cavo, plano, varo o valgo?',
            TipoPie.TIPO_PIE_CHOICES),
        _paso_opciones(
            'patologias_pie_derecho', 'Patologías del pie derecho',
            '¿Qué encontrás en el pie derecho? Podés nombrar varias.',
            PatologiasPieDerecho),
        _paso_opcion(
            'tipo_pie_izquierdo', 'Tipo de pie izquierdo',
            'Pie izquierdo: ¿normal, cavo, plano, varo o valgo?',
            TipoPie.TIPO_PIE_CHOICES),
        _paso_opciones(
            'patologias_pie_izquierdo', 'Patologías del pie izquierdo',
            '¿Qué encontrás en el pie izquierdo? Podés nombrar varias.',
            PatologiasPieIzquierdo),
        _paso_texto(
            'antecedentes_familiares', 'Antecedentes familiares',
            '¿Hay antecedentes familiares para anotar? Dictámelo como quieras.'),
        _paso_texto(
            'observaciones', 'Observaciones',
            'Por último, las observaciones de la consulta.'),
    ]


def construir_guion_paciente():
    """Los datos del paciente, en el orden en que se piden en la recepción."""
    return [
        _paso_simple('nombre', 'Nombre', '¿Cuál es el nombre?', 'frase'),
        _paso_simple('apellido', 'Apellido', '¿Y el apellido?', 'frase'),
        _paso_simple('dni', 'DNI', '¿Me decís el DNI?', 'numero',
                     rango=(1000000, 99999999)),
        _paso_simple('fecha_nacimiento', 'Fecha de nacimiento',
                     '¿Fecha de nacimiento? Por ejemplo, 2 de mayo de 1960.',
                     'fecha'),
        _paso_simple('telefono', 'Teléfono', '¿Un teléfono de contacto?',
                     'numero', rango=(10000000, 99999999999)),
        _paso_simple('domicilio', 'Domicilio', '¿Domicilio?', 'frase'),
        _paso_simple('localidad', 'Localidad', '¿De qué localidad?', 'frase'),
        _paso_simple('numero_calzado', 'Número de calzado',
                     '¿Qué número de calzado usa?', 'numero', rango=(15, 55)),
        _paso_simple('altura', 'Altura', '¿Cuánto mide, en centímetros?',
                     'numero', rango=(50, 230), es_altura=True),
        _paso_simple('peso', 'Peso', '¿Y cuánto pesa, en kilos?', 'numero',
                     rango=(2, 300)),
        _paso_texto('motivo_consulta', 'Motivo de consulta',
                    '¿Por qué viene a la consulta?'),
        _paso_opcion('actividad_fisica', 'Actividad física',
                     '¿Hace alguna actividad física?',
                     ActividadFisica.TIPO_ACTIVIDAD_CHOICES),
        _paso_opcion('plantillas', 'Plantillas', '¿Usa plantillas?',
                     plantillas.TIPO_PLANTILLAS_CHOICES),
    ]


GUIONES = {
    'historia': construir_guion,
    'paciente': construir_guion_paciente,
}


def construir(nombre):
    return GUIONES.get(nombre, construir_guion)()


def buscar_paso(campo, guion='historia'):
    for paso in construir(guion):
        if paso['campo'] == campo:
            return paso
    return None


# ---------------------------------------------------------------------------
# Hook opcional para n8n
# ---------------------------------------------------------------------------

def _consultar_n8n(paso, texto):
    """Le pide una mano a n8n con lo que no se pudo interpretar acá.

    Solo se usa si está definida N8N_ENTREVISTA_URL en el .env. Sin esa
    variable la entrevista funciona igual, sin salir a internet ni gastar
    un peso. Lo que devuelve n8n se valida contra las opciones reales del
    campo, así que nunca puede meter un valor que el formulario no acepte.
    """
    url = getattr(settings, 'N8N_ENTREVISTA_URL', '')
    if not url:
        return None

    try:
        import requests
        respuesta = requests.post(
            url,
            json={
                'campo': paso['campo'],
                'pregunta': paso['pregunta'],
                'texto': texto,
                'tipo': paso['tipo'],
                'opciones': [{'valor': o['valor'], 'texto': o['texto']}
                             for o in paso['opciones']],
            },
            timeout=8,
        )
        respuesta.raise_for_status()
        datos = respuesta.json()
    except Exception:
        # Si n8n está caído o tarda, la entrevista sigue como si no existiera.
        return None

    validos = {o['valor']: o['texto'] for o in paso['opciones']}
    valores = [v for v in datos.get('valores', []) if v in validos]
    if not valores:
        return None
    if paso['tipo'] == 'opcion':
        valores = valores[:1]
    return {
        'valores': valores,
        'textos': [validos[v] for v in valores],
        'confianza': 'media',
        'candidatos': [],
    }
