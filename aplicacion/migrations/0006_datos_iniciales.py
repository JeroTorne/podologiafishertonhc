"""Carga las opciones fijas de enfermedades, alergias y patologías.

Antes esto vivía a nivel de módulo en forms.py, así que se ejecutaba cada vez
que se importaba ese archivo y, sobre una base vacía, hacía fallar al propio
`migrate`. Acá corre una sola vez y de forma idempotente.
"""

from django.db import migrations

ENFERMEDADES = [
    'cardiopatias',
    'cirugias',
    'fumador',
    'hpv',
    'otras',
]

ALERGIAS = [
    'comidas',
    'estacional',
    'insectos',
    'medicamentos',
]

PATOLOGIAS_PIE = [
    'ampollas',
    'amputaciones',
    'grietas',
    'helomas',
    'hiperqueratosis',
    'onicocriptosis',
    'onicofosis',
    'onicomicosis',
    'osteopatias',
    'ulceras',
]


def cargar(apps, schema_editor):
    tablas = [
        ('EnfermedadesL', ENFERMEDADES),
        ('Alergia', ALERGIAS),
        ('PatologiasPieDerecho', PATOLOGIAS_PIE),
        ('PatologiasPieIzquierdo', PATOLOGIAS_PIE),
    ]
    for nombre_modelo, valores in tablas:
        modelo = apps.get_model('aplicacion', nombre_modelo)
        for valor in valores:
            modelo.objects.get_or_create(nombre=valor)


def borrar(apps, schema_editor):
    # No se borra nada al revertir: las historias clínicas ya cargadas apuntan
    # a estas filas y perderlas se llevaría puestos los datos de los pacientes.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('aplicacion', '0005_alter_seguimientoconsulta_options_and_more'),
    ]

    operations = [
        migrations.RunPython(cargar, borrar),
    ]
