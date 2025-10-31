from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import *
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LogoutView
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.views.generic.edit import UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.views.generic import DetailView
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from datetime import datetime

#-------////----------INDEX--------////------------------#

def index(request):
    return render (request, "aplicacion/index.html")

#-------////----------FIN INDEX--------////------------------#

def staff(request):
    return render (request, "aplicacion/staff.html")

#-------////----------TURNOS--------////------------------#

def turnos(request):
    return render (request, "aplicacion/turnos.html")

#-------////----------FIN TURNOS--------////------------------#

#-------////----------CREAR PACIENTE--------////------------------#

def crear_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'aplicacion/index.html')
    else:
        form = PacienteForm()
    return render(request, 'aplicacion/crear_paciente.html', {'form': form})

#-------////----------FIN CREAR PACIENTE--------////------------------#

#-------////----------ACTUALIZAR HISTORIA CLINICA--------////------------------#

class HistoriaClinicaUpdate(LoginRequiredMixin, UpdateView):
    model = historiaclinica
    form_class = HistoriaClinicaForm
    template_name = 'aplicacion/crear_hc.html'
    success_url = reverse_lazy('inicio')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def form_valid(self, form):
        historia = form.save(commit=False)
        historia.fecha_actualizacion = timezone.now().date()
        historia.save()
        form.save_m2m()  # Guardar relaciones ManyToMany
        
        # Procesar el seguimiento si existe
        descripcion_seguimiento = self.request.POST.get('descripcion_seguimiento')
        fecha_seguimiento = self.request.POST.get('fecha_seguimiento')
        
        if descripcion_seguimiento and descripcion_seguimiento.strip():
            try:
                seguimiento = SeguimientoConsulta.objects.create(
                    historia_clinica=historia,
                    descripcion=descripcion_seguimiento
                )
                
                if fecha_seguimiento:
                    seguimiento.fecha = datetime.strptime(fecha_seguimiento, '%Y-%m-%d').date()
                    seguimiento.save()
                
                messages.success(self.request, 'Historia clínica actualizada y seguimiento agregado correctamente.')
            except Exception as e:
                messages.warning(self.request, f'Historia clínica actualizada, pero hubo un error con el seguimiento: {str(e)}')
        else:
            messages.success(self.request, 'Historia clínica actualizada correctamente.')
        
        return redirect(self.success_url)

#-------////----------FIN ACTUALIZAR HISTORIA CLINICA--------////------------------#

#-------////----------LOGIN--------////------------------#

def login_request(request):
    if request.method == "POST":
        miForm = AuthenticationForm(request, data=request.POST)
        if miForm.is_valid():
            usuario = miForm.cleaned_data.get('username')
            clave = miForm.cleaned_data.get('password')
            user = authenticate(username=usuario, password=clave)
            if user is not None:
                login(request, user)
                return render(request, "aplicacion/index.html", {"mensaje": f"Bienvenido {usuario}"})
            else:
                return render(request, "aplicacion/login.html", {"form":miForm, "mensaje": "Datos Inválidos"})
        else:
            return render(request, "aplicacion/login.html", {"form":miForm, "mensaje": "Datos Inválidos"})

    miForm = AuthenticationForm()
    return render(request, "aplicacion/login.html", {"form":miForm})

#-------////----------FIN LOGIN--------////------------------#

#-------////----------SI ES ADMIN--------////------------------#

def is_admin(user):
    return user.is_authenticated and user.is_superuser

#-------////----------FIN SI ES ADMIN--------////------------------#

#-------////----------CREAR HISTORIA CLINICA--------////------------------#

@user_passes_test(is_admin)
def crear_historia_clinica(request, paciente_id):
    paciente = get_object_or_404(PerfilPaciente, id_usuario=paciente_id)
    
    if request.method == 'POST':
        form = HistoriaClinicaForm(request.POST, request.FILES)
        
        if form.is_valid():
            historia = form.save(commit=False)
            historia.perfil_paciente = paciente
            historia.save()
            form.save_m2m()  # Guardar relaciones ManyToMany
            
            # Procesar el seguimiento si existe
            descripcion_seguimiento = request.POST.get('descripcion_seguimiento')
            fecha_seguimiento = request.POST.get('fecha_seguimiento')
            
            if descripcion_seguimiento and descripcion_seguimiento.strip():
                try:
                    seguimiento = SeguimientoConsulta.objects.create(
                        historia_clinica=historia,
                        descripcion=descripcion_seguimiento
                    )
                    
                    if fecha_seguimiento:
                        seguimiento.fecha = datetime.strptime(fecha_seguimiento, '%Y-%m-%d').date()
                        seguimiento.save()
                    
                    messages.success(request, 'Historia clínica y seguimiento guardados correctamente.')
                except Exception as e:
                    messages.warning(request, f'Historia clínica guardada, pero hubo un error con el seguimiento: {str(e)}')
            else:
                messages.success(request, 'Historia clínica guardada correctamente.')
            
            return redirect('inicio')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = HistoriaClinicaForm(initial={'perfil_paciente': paciente})
    
    return render(request, 'aplicacion/crear_hc.html', {'form': form, 'paciente': paciente})

#-------////----------FIN CREAR HISTORIA CLINICA--------////------------------#

#-------////----------BUSCAR PACIENTE--------////------------------#

@user_passes_test(is_admin)
def buscar_paciente(request):
    return render (request, "aplicacion/buscar_paciente.html")

@user_passes_test(is_admin)
def buscar_paciente2(request):
    nombre = request.GET.get('nombre', '').strip()
    apellido = request.GET.get('apellido', '').strip()
    
    if nombre or apellido:
        paciente = PerfilPaciente.objects.all()
        
        if nombre:
            paciente = paciente.filter(nombre__icontains=nombre)
        
        if apellido:
            paciente = paciente.filter(apellido__icontains=apellido)
        
        return render(request, "aplicacion/listadopacientes.html", {"paciente": paciente})
    
    return redirect('lista_pacientes')

class PacienteList(LoginRequiredMixin,ListView):
    model = PerfilPaciente
    context_object_name = 'paciente_list'

#-------////----------FIN BUSCAR PACIENTE--------////------------------#

#-------////----------ELIMINAR HISTORIA CLINICA--------////------------------#

@user_passes_test(is_admin)
def delete_historia(request, pk):
    historia = get_object_or_404(historiaclinica, id=pk)
    historia.delete()
    messages.success(request, "Historia clínica eliminada correctamente.")
    return redirect('inicio')

#-------////----------FIN ELIMINAR HISTORIA CLINICA--------////------------------#

#-------////----------ELIMINAR PACIENTE--------////------------------#

@user_passes_test(is_admin)
def delete_paciente(request, pk):
    paciente = get_object_or_404(PerfilPaciente, id_usuario=pk)
    paciente.delete()
    messages.success(request, "Paciente eliminado correctamente.")
    return redirect('inicio')

#-------////----------FIN ELIMINAR PACIENTE--------////------------------#

#-------////----------DETALLE PACIENTE--------////------------------#

class PacienteDetail(LoginRequiredMixin, DetailView):
    model = PerfilPaciente

#-------////----------FIN DETALLE PACIENTE--------////------------------#

#-------////----------LISTA PACIENTES--------////------------------#

@user_passes_test(is_admin)
def lista_pacientes(request):
    pacientes = PerfilPaciente.objects.all()
    return render(request, 'aplicacion/index.html', {'pacientes': pacientes})

#-------////----------FIN LISTA PACIENTES--------////------------------#

#-------////----------ELIMINAR SEGUIMIENTO--------////------------------#

@user_passes_test(is_admin)
@require_POST
def eliminar_seguimiento(request, seguimiento_id):
    try:
        seguimiento = get_object_or_404(SeguimientoConsulta, id=seguimiento_id)
        seguimiento.delete()
        return JsonResponse({'success': True, 'message': 'Seguimiento eliminado correctamente.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

#-------////----------FIN ELIMINAR SEGUIMIENTO--------////------------------#

#-------////----------EDITAR PACIENTE--------////------------------

@user_passes_test(is_admin)
def editar_paciente(request, pk):
    paciente = get_object_or_404(PerfilPaciente, pk=pk)
    
    if request.method == 'POST':
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil del paciente actualizado correctamente.')
            return redirect('lista_pacientes')  # o la URL que prefieras
    else:
        form = PacienteForm(instance=paciente)
    
    return render(request, 'aplicacion/editar_paciente.html', {'form': form, 'paciente': paciente})

#-------////----------FIN EDITAR PACIENTE--------////------------------#