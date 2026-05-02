from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Página inicial
    path('', views.home_view, name='home'),
    
    # Autenticação
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Assinatura vencida
    path('assinatura-vencida/', views.assinatura_vencida, name='assinatura_vencida'),
    
    # Super Admin
    path('super-admin/', views.super_admin_dashboard, name='super_admin_dashboard'),
    path('super-admin/empresas/', views.empresas_list, name='empresas_list'),
    path('super-admin/empresas/criar/', views.empresa_create, name='empresa_create'),
    path('super-admin/empresas/<int:pk>/editar/', views.empresa_edit, name='empresa_edit'),
    path('super-admin/empresas/<int:pk>/excluir/', views.empresa_delete, name='empresa_delete'),
    path('super-admin/empresas/<int:pk>/assinatura/', views.empresa_assinatura, name='empresa_assinatura'),
    path('super-admin/agendamentos/', views.agendamentos_all, name='agendamentos_all'),
    path('super-admin/anuncios/', views.anuncios_list, name='anuncios_list'),
    path('super-admin/anuncios/criar/', views.anuncio_create, name='anuncio_create'),
    path('super-admin/anuncios/<int:pk>/editar/', views.anuncio_edit, name='anuncio_edit'),
    path('super-admin/anuncios/<int:pk>/excluir/', views.anuncio_delete, name='anuncio_delete'),
    
    # Cliente - Serviços
    path('servicos/', views.servicos_list, name='servicos_list'),
    path('servicos/criar/', views.servico_create, name='servico_create'),
    path('servicos/<int:pk>/editar/', views.servico_edit, name='servico_edit'),
    path('servicos/<int:pk>/excluir/', views.servico_delete, name='servico_delete'),
    
    # Cliente - Profissionais
    path('profissionais/', views.profissionais_list, name='profissionais_list'),
    path('profissionais/criar/', views.profissional_create, name='profissional_create'),
    path('profissionais/<int:pk>/editar/', views.profissional_edit, name='profissional_edit'),
    path('profissionais/<int:pk>/excluir/', views.profissional_delete, name='profissional_delete'),
    
    # Cliente - Horários
    path('horarios/', views.horarios_list, name='horarios_list'),
    path('horarios/criar/', views.horario_create, name='horario_create'),
    path('horarios/<int:pk>/editar/', views.horario_edit, name='horario_edit'),
    path('horarios/<int:pk>/excluir/', views.horario_delete, name='horario_delete'),
    
    # Cliente - Agendamentos
    path('agendamentos/', views.agendamentos_list, name='agendamentos_list'),
    path('agendamentos/criar/', views.agendamento_create, name='agendamento_create'),
    path('agendamentos/<int:pk>/editar/', views.agendamento_edit, name='agendamento_edit'),
    path('agendamentos/<int:pk>/excluir/', views.agendamento_delete, name='agendamento_delete'),
    
    # Cliente Dashboard
    path('cliente/', views.cliente_dashboard, name='cliente_dashboard'),
    
    # Público
    path('agendamento-publico/', views.agendamento_publico, name='agendamento_publico'),
    path('agendamento-publico/<str:empresa_slug>/', views.agendamento_publico, name='agendamento_publico_empresa'),
    path('agendamento-publico/<str:empresa_slug>/horarios/', views.api_horarios_publicos, name='api_horarios_publicos'),
    path('agendamento-publico/<str:empresa_slug>/sobre/', views.empresa_detalhes, name='empresa_detalhes'),
    path('agendamento-publico/<str:empresa_slug>/sucesso/', views.agendamento_publico_sucesso, name='agendamento_publico_sucesso'),
    
    # API
    path('api/anuncios/', views.api_anuncios, name='api_anuncios'),
]

