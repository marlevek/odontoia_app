from django.urls import path
from . import views


app_name = 'clinic'

urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
     
    path('', views.dashboard, name='dashboard'),
    path('dashboard/data/', views.dashboard_data, name='dashboard_data'),

    # Pacientes
    path('pacientes/', views.pacientes_list, name='pacientes_list'),
    path("pacientes/novo/", views.paciente_create, name="paciente_create"),
    path("pacientes/<int:pk>/editar/",
         views.paciente_update, name="paciente_update"),
    path("pacientes/<int:pk>/excluir/",
         views.paciente_delete, name="paciente_delete"),

    # Consultas
    path("consultas/", views.consultas_list, name="consultas_list"),
    path("consultas/nova/", views.consulta_create, name="consulta_create"),
    path("consultas/calendario/update/",
         views.consulta_update_ajax, name="consulta_update_ajax"),
    path("consultas/<int:pk>/excluir/",
         views.consulta_delete, name="consulta_delete"),
    path('consultas/<int:pk>/editar/',
         views.consulta_update, name='consulta_update'),
    path("consultas/ajax/create/", views.consulta_create_ajax, name="consulta_create_ajax"),


    # 📅 Novo calendário
    path("consultas/calendario/", views.consultas_calendar,
         name="consultas_calendar"),
    path("consultas/calendario/nova/",
         views.consulta_create_ajax, name="consulta_create_ajax"),


]
