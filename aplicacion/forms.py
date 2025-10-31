from django import forms
from .models import *

class PacienteForm(forms.ModelForm):
    class Meta:
        model = PerfilPaciente
        fields = ['nombre', 'apellido', 'dni', 'fecha_nacimiento', 'telefono', 'domicilio', 'localidad', 'numero_calzado','altura', 'peso','motivo_consulta','actividad_fisica','plantillas']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
            'dni': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'DNI'}),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Fecha de Nacimiento', 
                'type': 'date'
            }, format='%Y-%m-%d'),    
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(+549) 11 1234-5678', 'type': 'tel'}),
            'domicilio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Domicilio'}),
            'localidad': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Localidad'}),
            'numero_calzado': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Número de calzado'}),
            'altura': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Altura en cm'}),
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Peso en kg'}),
            'motivo_consulta': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Motivo de la consulta', 'rows': 3}),
            'actividad_fisica': forms.Select(attrs={'class': 'form-control pie-select'}),
            'plantillas': forms.Select(attrs={'class': 'form-control pie-select'}),

        }

class HistoriaClinicaForm(forms.ModelForm):
    class Meta:
        model = historiaclinica
        fields = [
            'perfil_paciente',
            'alergias',
            'antecedentes_familiares',
            'enfermedades',
            'observaciones',
            'archivos',
            'tipo_pie_derecho',
            'tipo_pie_izquierdo',
            'diabetes',
            'medicamentos_diabetes',
            'colesterol',
            'medicamentos_colesterol',
            'anticoagulante',
            'anticoagulante_medicamentos',
            'hipertension',
            'hipertension_medicamentos',
            'enfermedades_respiratorias',
            'enfermedades_reumatologicas',
            'enfermedades_vasculares',
            'enfermedades_neuropatias',
            'patologias_pie_derecho',
            'patologias_pie_izquierdo',
            'seguimiento_consulta',
        ]

        widgets = {
            'antecedentes_familiares': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'enfermedades': forms.CheckboxSelectMultiple(attrs={
                'class': 'enfermedades-columns'
            }),
            'alergias': forms.CheckboxSelectMultiple(attrs={
                'class': 'enfermedades-columns'
            }),
            'patologias_pie_derecho': forms.CheckboxSelectMultiple(attrs={'class': 'enfermedades-columns'}),
            'patologias_pie_izquierdo': forms.CheckboxSelectMultiple(attrs={'class': 'enfermedades-columns'}),
            'tipo_pie_derecho': forms.Select(attrs={'class': 'form-control pie-select'}),
            'tipo_pie_izquierdo': forms.Select(attrs={'class': 'form-control pie-select'}),
            'diabetes': forms.Select(attrs={'class': 'form-control pie-select'}),
            'medicamentos_diabetes': forms.Select(attrs={'class': 'form-control pie-select'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'colesterol': forms.Select(attrs={'class': 'form-control pie-select'}),
            'medicamentos_colesterol': forms.Select(attrs={'class': 'form-control pie-select'}),
            'anticoagulante': forms.Select(attrs={'class': 'form-control pie-select'}),
            'anticoagulante_medicamentos': forms.Select(attrs={'class': 'form-control pie-select'}),
            'hipertension': forms.Select(attrs={'class': 'form-control pie-select'}),
            'hipertension_medicamentos': forms.Select(attrs={'class': 'form-control pie-select'}),
            'enfermedades_respiratorias': forms.Select(attrs={'class': 'form-control pie-select'}),
            'enfermedades_reumatologicas': forms.Select(attrs={'class': 'form-control pie-select'}),
            'enfermedades_vasculares': forms.Select(attrs={'class': 'form-control pie-select'}),
            'enfermedades_neuropatias': forms.Select(attrs={'class': 'form-control pie-select'}),
            'seguimiento_consulta': forms.CheckboxSelectMultiple(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['perfil_paciente'].widget.attrs['readonly'] = True
        self.fields['perfil_paciente'].widget.attrs['class'] = 'form-control'
        self.fields['perfil_paciente'].widget.attrs['placeholder'] = 'Paciente'
        self.fields['archivos'].widget.attrs.update({
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.flv,.mp4'
        })

enfermedades = [
    'cardiopatias',
    'cirugias',
    'fumador',
    'hpv',
    'otras',
]
for enfermedad in enfermedades:
    EnfermedadesL.objects.get_or_create(nombre=enfermedad)

alergias = [
    'comidas',
    'estacional',
    'insectos',
    'medicamentos',
]
for alergia in alergias:
    Alergia.objects.get_or_create(nombre=alergia)

patologias_pie_derecho = [
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
for patologia in patologias_pie_derecho:
    PatologiasPieDerecho.objects.get_or_create(nombre=patologia)

patologias_pie_izquierdo = [
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
for patologia in patologias_pie_izquierdo:
    PatologiasPieIzquierdo.objects.get_or_create(nombre=patologia)

class SeguimientoConsultaForm(forms.ModelForm):
    class Meta:
        model = SeguimientoConsulta
        fields = ['descripcion']
        widgets = {
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del seguimiento'
            })
        }

