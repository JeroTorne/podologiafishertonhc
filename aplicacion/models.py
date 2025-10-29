from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class ActividadFisica(models.Model):
    TIPO_ACTIVIDAD_CHOICES = [
        ('ninguna', 'Ninguna'),
        ('baile', 'Baile'),
        ('bicicleta', 'Bicicleta'),
        ('caminata', 'Caminata'),
        ('futbol', 'Futbol'),
        ('gimnasio', 'Gimnasio'),
        ('golf', 'Golf'),
        ('hockey', 'Hockey'),
        ('kinesio', 'Kinesio'),
        ('patin', 'Patin'),
        ('pilates', 'Pilates'),
        ('rugby', 'Rugby'),
        ('yoga', 'Yoga'),
        ('zumba', 'Zumba'),
    ]

    tipo_actividad = models.CharField(
        max_length=20,
        choices=TIPO_ACTIVIDAD_CHOICES
    )

    def __str__(self):
        return self.get_tipo_actividad_display()

class plantillas(models.Model):
    TIPO_PLANTILLAS_CHOICES = [
        ('si', 'Sí'),
        ('no', 'No'),
    ]

    tipo_plantillas = models.CharField(
        max_length=10,
        choices=TIPO_PLANTILLAS_CHOICES
    )

    def __str__(self):
        return self.get_tipo_plantillas_display()

class PerfilPaciente(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    dni = models.CharField(max_length=20, unique=True)
    fecha_nacimiento = models.DateField()
    telefono = models.CharField(max_length=20, unique=True)
    domicilio = models.CharField(max_length=100, blank=True, null=True)
    localidad = models.CharField(max_length=50, blank=True, null=True)
    numero_calzado = models.IntegerField(blank=True, null=True)
    altura = models.IntegerField(blank=True, null=True)  # en cm
    peso = models.IntegerField(blank=True, null=True)    # en kg
    motivo_consulta = models.TextField(blank=True, null=True)
    actividad_fisica = models.CharField(max_length=20,
                                        choices=ActividadFisica.TIPO_ACTIVIDAD_CHOICES,
                                        default='ninguna')
    plantillas = models.CharField(max_length=10,
                                   choices=plantillas.TIPO_PLANTILLAS_CHOICES,
                                   default='no')
    def __str__(self):
        return f"{self.nombre}, {self.apellido}"
    class Meta:
        verbose_name = 'Perfil Paciente'
        verbose_name_plural = 'Perfiles Pacientes'



# -------------------->ENFERMEDADES<----------------------

class EnfermedadesL(models.Model):
    ENFERMEDADES_CHOICES = [
        ('cardiopatias', 'Cardiopatías'),
        ('cirugias', 'Cirugías'),
        ('fumador', 'Fumador'),
        ('hpv', 'HPV'),
        ('otras', 'Otras'),
    ]
    
    nombre = models.CharField(
        max_length=100,
        choices=ENFERMEDADES_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()


# -------------------->FIN ENFERMEDADES<----------------------

# -------------------->ALERGIAS<----------------------

class Alergia(models.Model):
    ALERGIAS_CHOICES = [
        ('comidas', 'Comidas'),
        ('estacional', 'Estacional'),
        ('insectos', 'Insectos'),
        ('medicamentos', 'Medicamentos'),
    ]
    
    nombre = models.CharField(
        max_length=100,
        choices=ALERGIAS_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()


# -------------------->FIN ALERGIAS<----------------------


# ------------------->COLESTEROL<----------------------

class Colesterol(models.Model):
    COLESTEROL_CHOICES = [
        ('no', 'No'),
        ('si', 'Sí'),
    ]
    nombre = models.CharField(
        max_length=100,
        choices=COLESTEROL_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()

class ColesterolMedicamentos(models.Model):
    MEDICAMENTO_COLESTEROL_CHOICES = [
        ('ninguno', 'Ninguno'),
        ('atrorvastatina', 'Atorvastatina'),
        ('colesevelam', 'Colesevelam'),
        ('colestiramina', 'Colestiramina'),
        ('colestipol', 'Colestipol'),
        ('fluvastatina', 'Fluvastatina'),        
        ('lovastatina', 'Lovastatina'),
        ('pravastatina', 'Pravastatina'),
        ('rosuvastatina', 'Rosuvastatina'),
    ]

    nombre = models.CharField(
        max_length=100,
        choices=MEDICAMENTO_COLESTEROL_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()

# ------------------->FIN COLESTEROL<----------------------



# ------------------->DIABETES<------------------------

class DiabetesTipo(models.Model):
    TIPO_DIABETES_CHOICES = [
        ('no', 'No'),
        ('tipo_1', 'Tipo 1'),
        ('tipo_2', 'Tipo 2'),
        ('gestacional', 'Gestacional'),
        ('prediabetes', 'Prediabetes'),
    ]

    nombre = models.CharField(
        max_length=100,
        choices=TIPO_DIABETES_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()
    
class MedicamentosDiabetes(models.Model):
    MEDICAMENTOS_DIABETES_CHOICES = [
        ('ninguno', 'Ninguno'),
        ('agonistas', 'Agonistas Receptor GLP-1'),
        ('glibenclamida', 'Glibenclamida'),
        ('inhibidores_DDP-4', 'Inhibidores DDP-4'),
        ('inhibidores_SGLT2', 'Inhibidores SGLT2'),
        ('insulina', 'Insulina'),
        ('liraglutida', 'Liraglutida'),
        ('metformina', 'Metformina'),
        ('miglitinidas', 'Miglitinidas'),
        ('saxagliptina', 'Saxagliptina'),
        ('sitagliptina', 'Sitagliptina'),
        ('sulfonilureas', 'Sulfonilureas'),
    ]

    nombre = models.CharField(
        max_length=100,
        choices=MEDICAMENTOS_DIABETES_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()

# ------------------->FIN DIABETES<------------------------




# -------------------->ANTICOAGULANTES<----------------------


class Anticoagulante(models.Model):
    TIPO_ANTICOAGULANTE_CHOICES = [
        ('no', 'No'),
        ('si', 'Si'),
    ]

    nombre = models.CharField(
        max_length=100,
        choices=TIPO_ANTICOAGULANTE_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()
    
class AnticoagulanteMedicamentos(models.Model):
    TIPO_ANTICOAGULANTEMEDICAMENTOS_CHOICES = [
        ('ninguno', 'Ninguno'),
        ('acetilsalicilico', 'Acetilsalicílico'),
        ('aspirina', 'Aspirina'),
        ('heparina', 'Heparina'),
    ]

    nombre = models.CharField(
        max_length=100,
        choices=TIPO_ANTICOAGULANTEMEDICAMENTOS_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()    

# -------------------->FIN ANTICOAGULANTES<----------------------

# -------------------->HIPERTENSION<-----------------------------

class Hipertension(models.Model):
    HIPERTENSION_CHOICES= [
        ('no', 'No'),
        ('si', 'Si'),
    ]
    nombre = models.CharField(
        max_length=100,
        choices=HIPERTENSION_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()
    
class HipertensionMedicamentos(models.Model):
    HIPERTENSION_MEDICAMENTOS_CHOICES = [
        ('ninguno', 'Ninguno'),
        ('Atenolol', 'Atenolol'),
        ('Benazepril', 'Benazepril'),
        ('Bisoprolol', 'Bisoprolol'),
        ('Captopril', 'Captopril'),
        ('Carvedilol', 'Carvedilol'),
        ('Cobis5', 'Cobis5'),
        ('Enalapril', 'Enalapril'),
        ('Fosinopril', 'Fosinopril'),
        ('Lisinopril', 'Lisinopril'),
        ('Lozertan', 'Lozertan'),
        ('Perindopril', 'Perindopril'),
        ('Quinapril', 'Quinapril'),
        ('Ramipril', 'Ramipril'),
        ('Trandolapril', 'Trandolapril'),
        ('Valsartan', 'Valsartan'),
        ('Vasetextend', 'Vasetextend'),
    ]
    nombre = models.CharField(
        max_length=100,
        choices=HIPERTENSION_MEDICAMENTOS_CHOICES
    )
    def __str__(self):
        return self.get_nombre_display()

# -------------------->FIN HIPERTENSION<-------------------------


# -------------------->ENFERMEDADES RESPIRATORIAS<---------------

class EnfermedadesRespiratorias(models.Model):

    TIPO_ENFERMEDAD_RESPIRATORIA_CHOICES = [
        ('no', 'No'),
        ('asma', 'Asma'),
        ('bronquitis', 'Bronquitis'),
        ('enfisema', 'Enfisema'),
        ('epoc', 'EPOC'),
        ('hipertension_pulmonar', 'Hipertensión Pulmonar'),
        ('neumonia', 'Neumonía'),
        ('rinitis', 'Rinitis'),
        ('tuberculosis', 'Tuberculosis'),
    ]

    nombre = models.CharField(
        max_length=100,
        choices=TIPO_ENFERMEDAD_RESPIRATORIA_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()


# -------------------->FIN ENFERMEDADES RESPIRATORIAS<---------------


# -------------------->ENFERMEDADES REUMATOLOGICAS<---------------


class EnfermedadesReumatologicas(models.Model):

    TIPO_ENFERMEDAD_REUMATOLOGICA_CHOICES = [
        ('no', 'No'),
        ('artritis_idiopatica_juvenil', 'Artritis Idiopática Juvenil'),
        ('artritis_reumatoidea', 'Artritis Reumatoidea'),
        ('artrosis', 'Artrosis'),
        ('esclerosis_sistemica', 'Esclerosis Sistémica'),
        ('espondilitis_anquilosante', 'Espondilitis Anquilosante'),
        ('fibromialgia', 'Fibromialgia'),
        ('gota', 'Gota'),
        ('lumbago_y_ciatico', 'Lumbago y Ciático'),
        ('lupus', 'Lupus'),
        ('osteoporosis', 'Osteoporosis'),
        ('psoriasis', 'Psoriasis'),
        ('sjogren', 'Sjögren'),
        ('uveitis', 'Uveitis'),
    ]
    nombre = models.CharField(
        max_length=100,
        choices=TIPO_ENFERMEDAD_REUMATOLOGICA_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()


# -------------------->FIN ENFERMEDADES REUMATOLOGICAS<---------------

# -------------------->ENFERMEDADES VASCULARES<---------------


class EnfermedadesVasculares(models.Model):

    TIPO_ENFERMEDAD_VASCULAR_CHOICES = [
        ('no', 'No'),
        ('acv', 'ACV'),
        ('aneurisma', 'Aneurisma'),
        ('eap', 'EAP'),
        ('edema', 'Edema'),
        ('trombosis', 'Trombosis'),
        ('varices', 'Varices'),
    ]

    nombre = models.CharField(
        max_length=100,
        choices=TIPO_ENFERMEDAD_VASCULAR_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()

# -------------------->FIN ENFERMEDADES VASCULARES<---------------


# -------------------->ENFERMEDADES NEUROPATIAS<---------------


class EnfermedadesNeuropatias(models.Model):

    TIPO_ENFERMEDAD_NEUROPATIA_CHOICES = [
        ('no', 'No'),
        ('si', 'Sí'),
    ]

    nombre = models.CharField(
        max_length=100,
        choices=TIPO_ENFERMEDAD_NEUROPATIA_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()
# -------------------->FIN ENFERMEDADES NEUROPATIAS<---------------

# ---------------------->TIPO DE PIE<-----------------------------

class TipoPie(models.Model):

    TIPO_PIE_CHOICES = [
        ('normal', 'Normal'),
        ('cavo', 'Pie Cavo'),
        ('plano', 'Pie Plano'),
        ('varo', 'Pie Varo'),
        ('valgo', 'Pie Valgo'),
        ]

    nombre = models.CharField(
        max_length=100,
        choices=TIPO_PIE_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()
    
# ---------------------->FIN TIPO DE PIE<-----------------------------

# ---------------------->PATOLOGIAS PIE DERECHO<-----------------------------

class PatologiasPieDerecho(models.Model):

    PATOLOGIAS_PIE_DERECHO_CHOICES = [
        ('ninguna', 'Ninguna'),
        ('ampollas', 'Ampollas'),
        ('amputaciones', 'Amputaciones'),
        ('grietas', 'Grietas'),
        ('helomas', 'Helomas'),
        ('hiperqueratosis', 'Hiperqueratosis'),
        ('onicocriptosis', 'Onicocriptosis'),
        ('onicofosis', 'Onicofosis'),
        ('onicomicosis', 'Onicomicosis'),
        ('osteopatias', 'Osteopatías'),
        ('ulceras', 'Ulceras'),
    ]

    nombre = models.CharField(
        max_length=100,
        choices=PATOLOGIAS_PIE_DERECHO_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()


# ---------------------->FIN PATOLOGIAS PIE DERECHO<-----------------------------

# ---------------------->PATOLOGIAS PIE IZQUIERDO<-----------------------------

class PatologiasPieIzquierdo(models.Model):

    PATOLOGIAS_PIE_IZQUIERDO_CHOICES = [
        ('ninguna', 'Ninguna'),
        ('ampollas', 'Ampollas'),
        ('amputaciones', 'Amputaciones'),
        ('grietas', 'Grietas'),
        ('helomas', 'Helomas'),
        ('hiperqueratosis', 'Hiperqueratosis'),
        ('onicocriptosis', 'Onicocriptosis'),
        ('onicofosis', 'Onicofosis'),
        ('onicomicosis', 'Onicomicosis'),
        ('osteopatias', 'Osteopatías'),
        ('ulceras', 'Ulceras'),
    ]

    nombre = models.CharField(
        max_length=100,
        choices=PATOLOGIAS_PIE_IZQUIERDO_CHOICES
    )

    def __str__(self):
        return self.get_nombre_display()


# ---------------------->FIN PATOLOGIAS PIE IZQUIERDO<-----------------------------

# -------------------->SEGUIMIENTO CONSULTA<----------------------
class SeguimientoConsulta(models.Model):
    historia_clinica = models.ForeignKey('historiaclinica', on_delete=models.CASCADE, related_name='seguimientos')
    fecha = models.DateField(default=timezone.now)  # Permite editar la fecha
    descripcion = models.TextField()

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Seguimiento de Consulta'
        verbose_name_plural = 'Seguimientos de Consulta'

    def __str__(self):
        return f"Seguimiento del {self.fecha.strftime('%d/%m/%Y')}"
# -------------------->FIN SEGUIMIENTO CONSULTA<----------------------




class historiaclinica(models.Model):

    perfil_paciente = models.ForeignKey(PerfilPaciente, on_delete=models.CASCADE, null=True, related_name="historiaclinica_set")

    antecedentes_familiares = models.TextField(blank=True, null=True)

    fecha_consulta = models.DateField(auto_now_add=True)

    fecha_actualizacion = models.DateField(null=True, blank=True)

    enfermedades = models.ManyToManyField(EnfermedadesL, blank=True)

    patologias_pie_derecho = models.ManyToManyField(PatologiasPieDerecho, blank=True)

    patologias_pie_izquierdo = models.ManyToManyField(PatologiasPieIzquierdo, blank=True)

    observaciones = models.TextField(blank=True, null=True)

    diabetes = models.CharField(
        max_length=20,
        choices=DiabetesTipo.TIPO_DIABETES_CHOICES,
        default='no',
    )

    medicamentos_diabetes = models.CharField(
        max_length=100,
        choices=MedicamentosDiabetes.MEDICAMENTOS_DIABETES_CHOICES,
        default='ninguno',
    )

    tipo_pie_derecho = models.CharField(
        max_length=20,
        choices=TipoPie.TIPO_PIE_CHOICES,
        default='normal',
    )

    tipo_pie_izquierdo = models.CharField(
        max_length=20,
        choices=TipoPie.TIPO_PIE_CHOICES,
        default='normal'
    )

    alergias = models.ManyToManyField(Alergia, blank=True)

    colesterol = models.CharField(
        max_length=20,
        choices=Colesterol.COLESTEROL_CHOICES,
        default='no',
    )

    medicamentos_colesterol = models.CharField(
        max_length=100,
        choices=ColesterolMedicamentos.MEDICAMENTO_COLESTEROL_CHOICES,
        default='ninguno',
    )

    anticoagulante = models.CharField(
        max_length=20,
        choices=Anticoagulante.TIPO_ANTICOAGULANTE_CHOICES,
        default='no',
    )

    anticoagulante_medicamentos = models.CharField(
        max_length=100,
        choices=AnticoagulanteMedicamentos.TIPO_ANTICOAGULANTEMEDICAMENTOS_CHOICES,
        default='ninguno',
    )

    hipertension = models.CharField(
        max_length=20,
        choices=Hipertension.HIPERTENSION_CHOICES,
        default='no',
    )

    hipertension_medicamentos = models.CharField(
        max_length=100,
        choices=HipertensionMedicamentos.HIPERTENSION_MEDICAMENTOS_CHOICES,
        default='ninguno',
    )

    enfermedades_respiratorias = models.CharField(
        max_length=100,
        choices=EnfermedadesRespiratorias.TIPO_ENFERMEDAD_RESPIRATORIA_CHOICES,
        default='no',
    )

    enfermedades_reumatologicas = models.CharField(
        max_length=100,
        choices=EnfermedadesReumatologicas.TIPO_ENFERMEDAD_REUMATOLOGICA_CHOICES,
        default='no',
    )

    enfermedades_vasculares = models.CharField(
        max_length=100,
        choices=EnfermedadesVasculares.TIPO_ENFERMEDAD_VASCULAR_CHOICES,
        default='no',
    )

    enfermedades_neuropatias = models.CharField(
        max_length=20,
        choices=EnfermedadesNeuropatias.TIPO_ENFERMEDAD_NEUROPATIA_CHOICES,
        default='no',
    )

    seguimiento_consulta = models.ManyToManyField(SeguimientoConsulta, blank=True)

    archivos = models.FileField(upload_to='archivos/', blank=True, null=True)

    def __str__(self):
        return f"Historia Clínica de {self.perfil_paciente.nombre} {self.perfil_paciente.apellido}"