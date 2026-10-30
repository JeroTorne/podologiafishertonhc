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

from django.conf import settings

from .models import (
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
}

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


def detectar_comando(texto):
    """Devuelve el comando de navegación dicho, o None si es una respuesta común."""
    t = _normalizar(texto)
    for comando, frases in COMANDOS.items():
        for frase in frases:
            if t == frase or t == frase + ' por favor':
                return comando
    return None


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


def buscar_paso(campo):
    for paso in construir_guion():
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
