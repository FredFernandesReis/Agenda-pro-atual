from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Empresa, Assinatura, Servico, Profissional, HorarioAtendimento, Agendamento, Anuncio


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'tipo', 'is_active', 'date_joined']
    list_filter = ['tipo', 'is_active', 'is_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informações Adicionais', {'fields': ('tipo', 'telefone')}),
    )


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'usuario', 'telefone', 'email', 'ativo', 'criado_em']
    list_filter = ['ativo', 'criado_em']
    search_fields = ['nome', 'cnpj', 'email']


@admin.register(Assinatura)
class AssinaturaAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'ativa', 'data_vencimento', 'esta_vencida', 'criado_em']
    list_filter = ['ativa', 'data_vencimento']
    search_fields = ['empresa__nome']


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'preco', 'duracao', 'ativo']
    list_filter = ['ativo', 'empresa']
    search_fields = ['nome', 'empresa__nome']


@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    list_display = ['nome', 'empresa', 'telefone', 'ativo']
    list_filter = ['ativo', 'empresa']
    search_fields = ['nome', 'empresa__nome']


@admin.register(HorarioAtendimento)
class HorarioAtendimentoAdmin(admin.ModelAdmin):
    list_display = ['empresa', 'dia_semana', 'hora_inicio', 'hora_fim', 'ativo']
    list_filter = ['ativo', 'dia_semana', 'empresa']


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ['cliente_nome', 'empresa', 'servico', 'profissional', 'data', 'hora', 'status']
    list_filter = ['status', 'data', 'empresa']
    search_fields = ['cliente_nome', 'cliente_telefone', 'cliente_email']
    date_hierarchy = 'data'


@admin.register(Anuncio)
class AnuncioAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo', 'ativo', 'esta_ativo', 'data_inicio', 'data_fim']
    list_filter = ['ativo', 'tipo', 'data_inicio']
    search_fields = ['titulo', 'mensagem']
    
    # Campos não editáveis
    readonly_fields = ['data_inicio']
    
    fieldsets = (
        ('Informações', {
            'fields': ('titulo', 'mensagem', 'tipo')
        }),
        ('Configurações', {
            'fields': ('ativo', 'data_inicio', 'data_fim')
        }),
    )
