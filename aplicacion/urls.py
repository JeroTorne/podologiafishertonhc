from django.urls import path
from .views import *
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('', index, name='inicio'),

    path('staff/', staff, name='staff'),

    path('turnos/', turnos , name='turnos'),   

    path( 'crear_hc/', crear_historia_clinica, name='crear_historia_clinica' ),

    path( 'crear_paciente/', crear_paciente, name='crear_paciente' ),

    path('login/', login_request, name='login'),

    path('logout/', LogoutView.as_view(template_name="aplicacion/index.html"), name='logout'),

    #-------////----------BUSCAR PACIENTE--------////------------------# 

    path('buscar_paciente/', buscar_paciente, name='buscar_paciente'),

    path('buscar_paciente2/', buscar_paciente2, name='buscar_paciente2'),

    path('perfilpaciente_list.html', PacienteList.as_view() , name='lista_pacientes'),

    path('update_historia/<int:pk>/', HistoriaClinicaUpdate.as_view(), name='update_historia'),

    path('delete_historia/<int:pk>/', delete_historia, name='delete_historia'),
    
    path('detail_historia/<int:pk>/', PacienteDetail.as_view(), name="detail_historia"),

    path('delete_paciente/<int:pk>/', delete_paciente, name='delete_paciente'),
    
    path('detail_paciente/<int:pk>/', PacienteDetail.as_view(), name="detail_paciente"),

    path('crear_historia_clinica/<int:paciente_id>/', crear_historia_clinica, name='crear_historia_clinica'),

    #-------////----------FIN BUSCAR PACIENTE--------////------------------#
    
    #-------////----------SEGUIMIENTOS--------////------------------#
    
    path('eliminar-seguimiento/<int:seguimiento_id>/', eliminar_seguimiento, name='eliminar_seguimiento'),
    
    #-------////----------FIN SEGUIMIENTOS--------////------------------#
]