from django.urls import path
from . import views
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views

app_name = 'clinic'

# -----------------------------
# Autenticação e Assinaturas
# -----------------------------
urlpatterns = [
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('registrar_teste/', views.registrar_teste, name='registrar_teste'),
    path('assinatura-expirada/', views.assinatura_expirada,
         name='assinatura_expirada'),


    # -----------------------------
    # Dashboard e Recursos do App
    # -----------------------------
    path('bem-vindo/', views.onboarding, name='onboarding'),
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/data/', views.dashboard_data, name='dashboard_data'),

    # Dentistas
    path('dentistas/', views.dentistas_list, name='dentistas_list'),
    path('dentistas/novo/', views.dentista_create, name='dentista_create'),
    path("dentistas/<int:id>/editar/", views.dentista_edit, name="dentista_edit"),
    path("dentistas/<int:id>/excluir/",
         views.dentista_delete, name="dentista_delete"),
    path('dentista/principal/', views.dentista_principal,
         name='dentista_principal'),

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
    path("consultas/ajax/create/", views.consulta_create_ajax,
         name="consulta_create_ajax"),

    # Procedimentos
    path('procedimentos/', views.procedimentos_list, name='procedimentos_list'),
    path('procedimentos/novo/', views.procedimento_create,
         name='procedimento_create'),
    path('procedimentos/<int:id>/valor/',
         views.procedimento_valor, name='procedimento_valor'),
    path('procedimentos/<int:id>/editar/',
         views.procedimento_edit, name='procedimento_edit'),
    path('procedimentos/<int:pk>/excluir/',
         views.procedimento_delete, name='procedimento_delete'),

    # 📅 Novo calendário
    path("consultas/calendario/", views.consultas_calendar,
         name="consultas_calendar"),
    path("consultas/calendario/nova/",
         views.consulta_create_ajax, name="consulta_create_ajax"),

    # Chatbot
    path('api/chat/', views.chat_odontoia_api, name='chat_api'),
    path('api/chat/diag/', views.chat_diag, name='chat_diag'),


    # 🔹 Novo: recuperação de senha
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='clinic/password_reset.html'
    ), name='password_reset'),

    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='clinic/password_reset_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='clinic/password_reset_confirm.html'
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='clinic/password_reset_complete.html'
    ), name='password_reset_complete'),
    path('password_reset_request/', __import__('clinic.views')
         .views.password_reset_request, name='password_reset_request'),

    path("password-reset-request/", views.password_reset_request,
         name="password_reset_request"),

    # Pagamentos
    path('pagamento/checkout/<str:plano>/',
         views.criar_pagamento, name='criar_pagamento'),
    path('pagamento/sucesso/', views.pagamento_sucesso, name='pagamento_sucesso'),
    path('pagamento/falha/', views.pagamento_falha, name='pagamento_falha'),
    path('webhook/mercadopago/', views.mercadopago_webhook,
         name='mercadopago_webhook'),

    # Checkout
    path('checkout/<str:plano>/', views.checkout_publico, name='checkout_publico'),

    # Financeiro
    path('financeiro/', views.financeiro_home, name='financeiro_home'),
    path('financeiro/resumo/', views.financeiro_resumo, name='financeiro_resumo'),
    
    # Finanças
    path('financeiro/dashboard/', views.financeiro_dashboard,
         name='financeiro_dashboard'),
    path("financeiro/receitas/", views.receitas_list, name="receitas_list"),
    path("financeiro/receitas/nova/", views.receita_create, name="receita_create"),
    path("financeiro/receitas/<int:pk>/editar/",
         views.receita_update, name="receita_update"),
    path("financeiro/receitas/<int:pk>/deletar/",
         views.receita_delete, name="receita_delete"),

    path("financeiro/despesas/", views.despesas_list, name="despesas_list"),
    path("financeiro/despesas/nova/", views.despesa_create, name="despesa_create"),
    path("financeiro/despesas/<int:pk>/editar/",
         views.despesa_update, name="despesa_update"),
    path("financeiro/despesas/<int:pk>/deletar/",
         views.despesa_delete, name="despesa_delete"),
    path('financeiro/exportar/pdf/', views.financeiro_export_pdf, name='financeiro_export_pdf'),
    path('financeiro/exportar/excel/', views.financeiro_export_excel, name='financeiro_export_excel'),


    # IA e Insights
    path("ia-insights/", views.ia_insights, name="ia_insights"),
    
    # Configurações da Clínica
     path('configuracoes/clinica/', views.clinica_config, name='clinica_config'),
]
