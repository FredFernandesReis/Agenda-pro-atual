from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse
from datetime import datetime, timedelta
from .models import User, Empresa, Assinatura, Servico, Profissional, HorarioAtendimento, Agendamento, Anuncio
from .forms import (
    LoginForm, EmpresaForm, EmpresaPerfilForm, AssinaturaForm, ServicoForm, ProfissionalForm,
    HorarioAtendimentoForm, HorarioBulkForm, AgendamentoForm, AgendamentoPublicoForm,
)
from .whatsapp_service import WhatsAppService
from functools import wraps


def empresa_required(view_func):
    """Decorator para verificar se o usuário tem empresa associada"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.user.is_super_admin():
            return view_func(request, *args, **kwargs)
        
        try:
            empresa = request.user.empresa
        except (Empresa.DoesNotExist, AttributeError):
            messages.error(request, 'Você não possui uma empresa associada. Entre em contato com o administrador.')
            return redirect('logout')
        
        return view_func(request, *args, **kwargs)
    return wrapper


def home_view(request):
    """View da página inicial - redireciona conforme autenticação"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('login')


def login_view(request):
    """View de login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, 'Usuário ou senha incorretos.')
    else:
        form = LoginForm()
    
    return render(request, 'core/login.html', {'form': form})


@login_required
def dashboard(request):
    """Dashboard principal - redireciona conforme tipo de usuário"""
    if request.user.is_super_admin():
        return redirect('super_admin_dashboard')
    else:
        return redirect('cliente_dashboard')


@login_required
def super_admin_dashboard(request):
    """Dashboard do Super Admin"""
    if not request.user.is_super_admin():
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')
    
    total_empresas = Empresa.objects.count()
    empresas_ativas = Empresa.objects.filter(assinatura__ativa=True).count()
    total_agendamentos = Agendamento.objects.count()
    agendamentos_hoje = Agendamento.objects.filter(data=timezone.now().date()).count()
    
    empresas = Empresa.objects.select_related('assinatura').all()[:10]
    agendamentos_recentes = Agendamento.objects.select_related('empresa', 'servico', 'profissional').all()[:10]
    
    context = {
        'total_empresas': total_empresas,
        'empresas_ativas': empresas_ativas,
        'total_agendamentos': total_agendamentos,
        'agendamentos_hoje': agendamentos_hoje,
        'empresas': empresas,
        'agendamentos_recentes': agendamentos_recentes,
    }
    
    return render(request, 'core/super_admin/dashboard.html', context)


@login_required
@empresa_required
def cliente_dashboard(request):
    """Dashboard do Cliente"""
    if request.user.is_super_admin():
        return redirect('super_admin_dashboard')
    
    empresa = request.user.empresa
    
    # Estatísticas
    total_servicos = Servico.objects.filter(empresa=empresa).count()
    total_profissionais = Profissional.objects.filter(empresa=empresa).count()
    total_agendamentos = Agendamento.objects.filter(empresa=empresa).count()
    agendamentos_hoje = Agendamento.objects.filter(empresa=empresa, data=timezone.now().date()).count()
    agendamentos_pendentes = Agendamento.objects.filter(empresa=empresa, status='pendente').count()
    
    # Agendamentos recentes
    agendamentos_recentes = Agendamento.objects.filter(
        empresa=empresa
    ).select_related('servico', 'profissional').order_by('-data', '-hora')[:10]
    
    # Próximos agendamentos
    proximos_agendamentos = Agendamento.objects.filter(
        empresa=empresa,
        data__gte=timezone.now().date(),
        status__in=['pendente', 'confirmado']
    ).select_related('servico', 'profissional').order_by('data', 'hora')[:5]
    
    context = {
        'empresa': empresa,
        'total_servicos': total_servicos,
        'total_profissionais': total_profissionais,
        'total_agendamentos': total_agendamentos,
        'agendamentos_hoje': agendamentos_hoje,
        'agendamentos_pendentes': agendamentos_pendentes,
        'agendamentos_recentes': agendamentos_recentes,
        'proximos_agendamentos': proximos_agendamentos,
    }
    
    return render(request, 'core/cliente/dashboard.html', context)


@login_required
def assinatura_vencida(request):
    """Tela de assinatura vencida"""
    return render(request, 'core/assinatura_vencida.html')


# ========== SUPER ADMIN - GERENCIAMENTO DE EMPRESAS ==========

@login_required
def empresas_list(request):
    """Lista de empresas (Super Admin)"""
    if not request.user.is_super_admin():
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')
    
    empresas = Empresa.objects.select_related('assinatura', 'usuario').all()
    
    # Filtros
    busca = request.GET.get('busca', '')
    if busca:
        empresas = empresas.filter(
            Q(nome__icontains=busca) | 
            Q(cnpj__icontains=busca) | 
            Q(email__icontains=busca)
        )
    
    return render(request, 'core/super_admin/empresas_list.html', {'empresas': empresas, 'busca': busca})


@login_required
def empresa_create(request):
    """Criar empresa (Super Admin)"""
    if not request.user.is_super_admin():
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            # Criar usuário
            username = form.cleaned_data['username']
            email = (form.cleaned_data.get('email') or '').strip()
            password = form.cleaned_data.get('password') or User.objects.make_random_password()
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                tipo='cliente'
            )
            
            # Criar empresa
            empresa = form.save(commit=False)
            empresa.usuario = user
            empresa.save()
            
            # Criar assinatura (inativa por padrão)
            Assinatura.objects.create(empresa=empresa, ativa=False)
            
            messages.success(request, f'Empresa {empresa.nome} criada com sucesso!')
            return redirect('empresas_list')
    else:
        form = EmpresaForm()
    
    return render(request, 'core/super_admin/empresa_form.html', {'form': form})


@login_required
def empresa_edit(request, pk):
    """Editar empresa (Super Admin)"""
    if not request.user.is_super_admin():
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')
    
    empresa = get_object_or_404(Empresa, pk=pk)
    
    if request.method == 'POST':
        form = EmpresaForm(request.POST, instance=empresa)
        if form.is_valid():
            # Atualizar dados da empresa
            empresa = form.save()
            
            # Atualizar usuário se fornecido
            if form.cleaned_data.get('username'):
                empresa.usuario.username = form.cleaned_data['username']
            if form.cleaned_data.get('email'):
                empresa.usuario.email = form.cleaned_data['email']
            if form.cleaned_data.get('password'):
                empresa.usuario.set_password(form.cleaned_data['password'])
            empresa.usuario.save()
            
            messages.success(request, 'Empresa atualizada com sucesso!')
            return redirect('empresas_list')
    else:
        form = EmpresaForm(instance=empresa)
        form.fields['username'].initial = empresa.usuario.username
        form.fields['email'].initial = empresa.email
    
    return render(request, 'core/super_admin/empresa_form.html', {'form': form, 'empresa': empresa})


@login_required
def empresa_delete(request, pk):
    """Excluir empresa (Super Admin)"""
    if not request.user.is_super_admin():
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')
    
    empresa = get_object_or_404(Empresa, pk=pk)
    
    if request.method == 'POST':
        empresa.usuario.delete()  # Isso também deleta a empresa e assinatura (CASCADE)
        messages.success(request, 'Empresa excluída com sucesso!')
        return redirect('empresas_list')
    
    return render(request, 'core/super_admin/empresa_delete.html', {'empresa': empresa})


@login_required
def empresa_assinatura(request, pk):
    """Gerenciar assinatura da empresa (Super Admin)"""
    if not request.user.is_super_admin():
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')
    
    empresa = get_object_or_404(Empresa, pk=pk)
    assinatura = empresa.assinatura
    
    if request.method == 'POST':
        form = AssinaturaForm(request.POST, instance=assinatura)
        if form.is_valid():
            form.save()
            messages.success(request, 'Assinatura atualizada com sucesso!')
            return redirect('empresas_list')
    else:
        form = AssinaturaForm(instance=assinatura)
    
    return render(request, 'core/super_admin/empresa_assinatura.html', {
        'form': form,
        'empresa': empresa,
        'assinatura': assinatura
    })


@login_required
def agendamentos_all(request):
    """Todos os agendamentos (Super Admin)"""
    if not request.user.is_super_admin():
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')
    
    agendamentos = Agendamento.objects.select_related('empresa', 'servico', 'profissional').all()
    
    # Filtros
    empresa_id = request.GET.get('empresa')
    if empresa_id:
        agendamentos = agendamentos.filter(empresa_id=empresa_id)
    
    status = request.GET.get('status')
    if status:
        agendamentos = agendamentos.filter(status=status)
    
    data = request.GET.get('data')
    if data:
        agendamentos = agendamentos.filter(data=data)
    
    empresas = Empresa.objects.all()
    
    return render(request, 'core/super_admin/agendamentos_all.html', {
        'agendamentos': agendamentos,
        'empresas': empresas,
    })


# ========== SUPER ADMIN - GERENCIAMENTO DE ANÚNCIOS ==========

@login_required
def anuncios_list(request):
    """Lista de anúncios (Super Admin)"""
    if not request.user.is_super_admin():
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')
    
    anuncios = Anuncio.objects.all()
    return render(request, 'core/super_admin/anuncios_list.html', {'anuncios': anuncios})


@login_required
def anuncio_create(request):
    """Criar anúncio (Super Admin)"""
    if not request.user.is_super_admin():
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        mensagem = request.POST.get('mensagem')
        tipo = request.POST.get('tipo', 'info')
        ativo = request.POST.get('ativo') == 'on'
        data_fim = request.POST.get('data_fim') or None
        
        if titulo and mensagem:
            Anuncio.objects.create(
                titulo=titulo,
                mensagem=mensagem,
                tipo=tipo,
                ativo=ativo,
                data_fim=data_fim
            )
            messages.success(request, 'Anúncio criado com sucesso!')
            return redirect('anuncios_list')
        else:
            messages.error(request, 'Preencha todos os campos obrigatórios.')
    
    return render(request, 'core/super_admin/anuncio_form.html', {'anuncio': None})


@login_required
def anuncio_edit(request, pk):
    """Editar anúncio (Super Admin)"""
    if not request.user.is_super_admin():
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')
    
    anuncio = get_object_or_404(Anuncio, pk=pk)
    
    if request.method == 'POST':
        anuncio.titulo = request.POST.get('titulo')
        anuncio.mensagem = request.POST.get('mensagem')
        anuncio.tipo = request.POST.get('tipo', 'info')
        anuncio.ativo = request.POST.get('ativo') == 'on'
        data_fim = request.POST.get('data_fim') or None
        if data_fim:
            from django.utils.dateparse import parse_datetime
            anuncio.data_fim = parse_datetime(data_fim)
        else:
            anuncio.data_fim = None
        anuncio.save()
        
        messages.success(request, 'Anúncio atualizado com sucesso!')
        return redirect('anuncios_list')
    
    return render(request, 'core/super_admin/anuncio_form.html', {'anuncio': anuncio})


@login_required
def anuncio_delete(request, pk):
    """Excluir anúncio (Super Admin)"""
    if not request.user.is_super_admin():
        messages.error(request, 'Acesso negado.')
        return redirect('dashboard')
    
    anuncio = get_object_or_404(Anuncio, pk=pk)
    
    if request.method == 'POST':
        anuncio.delete()
        messages.success(request, 'Anúncio excluído com sucesso!')
        return redirect('anuncios_list')
    
    return render(request, 'core/super_admin/anuncio_delete.html', {'anuncio': anuncio})


# ========== CLIENTE - PERFIL DA BARBEARIA ==========

@login_required
@empresa_required
def perfil_empresa(request):
    """Permite ao cliente editar o perfil/identidade visual da barbearia."""
    empresa = request.user.empresa

    if request.method == 'POST':
        form = EmpresaPerfilForm(request.POST, request.FILES, instance=empresa)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil da barbearia atualizado com sucesso!')
            return redirect('perfil_empresa')
    else:
        form = EmpresaPerfilForm(instance=empresa)

    return render(request, 'core/cliente/perfil_empresa.html', {'form': form, 'empresa': empresa})


# ========== CLIENTE - GERENCIAMENTO DE SERVIÇOS ==========

@login_required
@empresa_required
def servicos_list(request):
    """Lista de serviços"""
    empresa = request.user.empresa
    servicos = Servico.objects.filter(empresa=empresa)
    return render(request, 'core/cliente/servicos_list.html', {'servicos': servicos})


@login_required
@empresa_required
def servico_create(request):
    """Criar serviço"""
    empresa = request.user.empresa
    
    if request.method == 'POST':
        form = ServicoForm(request.POST)
        if form.is_valid():
            servico = form.save(commit=False)
            servico.empresa = empresa
            servico.save()
            messages.success(request, 'Serviço criado com sucesso!')
            return redirect('servicos_list')
    else:
        form = ServicoForm()
    
    return render(request, 'core/cliente/servico_form.html', {'form': form})


@login_required
@empresa_required
def servico_edit(request, pk):
    """Editar serviço"""
    empresa = request.user.empresa
    servico = get_object_or_404(Servico, pk=pk, empresa=empresa)
    
    if request.method == 'POST':
        form = ServicoForm(request.POST, instance=servico)
        if form.is_valid():
            form.save()
            messages.success(request, 'Serviço atualizado com sucesso!')
            return redirect('servicos_list')
    else:
        form = ServicoForm(instance=servico)
    
    return render(request, 'core/cliente/servico_form.html', {'form': form, 'servico': servico})


@login_required
@empresa_required
def servico_delete(request, pk):
    """Excluir serviço"""
    empresa = request.user.empresa
    servico = get_object_or_404(Servico, pk=pk, empresa=empresa)
    
    if request.method == 'POST':
        servico.delete()
        messages.success(request, 'Serviço excluído com sucesso!')
        return redirect('servicos_list')
    
    return render(request, 'core/cliente/servico_delete.html', {'servico': servico})


# ========== CLIENTE - GERENCIAMENTO DE PROFISSIONAIS ==========

@login_required
@empresa_required
def profissionais_list(request):
    """Lista de profissionais"""
    empresa = request.user.empresa
    profissionais = Profissional.objects.filter(empresa=empresa).annotate(
        total_horarios=Count('horarios_atendimento')
    )
    return render(request, 'core/cliente/profissionais_list.html', {'profissionais': profissionais})


@login_required
@empresa_required
def profissional_create(request):
    """Criar profissional"""
    empresa = request.user.empresa
    
    if request.method == 'POST':
        form = ProfissionalForm(request.POST)
        if form.is_valid():
            profissional = form.save(commit=False)
            profissional.empresa = empresa
            profissional.save()
            form.save_m2m()  # Salvar especialidades
            messages.success(request, 'Profissional criado com sucesso!')
            return redirect('profissionais_list')
    else:
        form = ProfissionalForm()
        form.fields['especialidades'].queryset = Servico.objects.filter(empresa=empresa)
    
    return render(request, 'core/cliente/profissional_form.html', {'form': form})


@login_required
@empresa_required
def profissional_edit(request, pk):
    """Editar profissional"""
    empresa = request.user.empresa
    profissional = get_object_or_404(Profissional, pk=pk, empresa=empresa)
    
    if request.method == 'POST':
        form = ProfissionalForm(request.POST, instance=profissional)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profissional atualizado com sucesso!')
            return redirect('profissionais_list')
    else:
        form = ProfissionalForm(instance=profissional)
        form.fields['especialidades'].queryset = Servico.objects.filter(empresa=empresa)
    
    return render(request, 'core/cliente/profissional_form.html', {'form': form, 'profissional': profissional})


@login_required
@empresa_required
def profissional_delete(request, pk):
    """Excluir profissional"""
    empresa = request.user.empresa
    profissional = get_object_or_404(Profissional, pk=pk, empresa=empresa)
    
    if request.method == 'POST':
        profissional.delete()
        messages.success(request, 'Profissional excluído com sucesso!')
        return redirect('profissionais_list')
    
    return render(request, 'core/cliente/profissional_delete.html', {'profissional': profissional})


# ========== CLIENTE - GERENCIAMENTO DE HORÁRIOS ==========

@login_required
@empresa_required
def horarios_list(request):
    """Lista de horários de atendimento"""
    empresa = request.user.empresa
    horarios = HorarioAtendimento.objects.filter(
        empresa=empresa
    ).select_related('profissional').order_by('dia_semana', 'hora_inicio')
    profissionais = Profissional.objects.filter(empresa=empresa, ativo=True).order_by('nome')

    profissional_id = request.GET.get('profissional')
    if profissional_id == 'geral':
        horarios = horarios.filter(profissional__isnull=True)
    elif profissional_id:
        horarios = horarios.filter(profissional_id=profissional_id)

    return render(request, 'core/cliente/horarios_list.html', {
        'horarios': horarios,
        'profissionais': profissionais,
        'profissional_filtro': profissional_id,
    })


@login_required
@empresa_required
def horario_create(request):
    """Criar horário de atendimento"""
    empresa = request.user.empresa
    
    if request.method == 'POST':
        form = HorarioAtendimentoForm(request.POST)
        form.fields['profissional'].queryset = Profissional.objects.filter(empresa=empresa, ativo=True)
        if form.is_valid():
            horario = form.save(commit=False)
            horario.empresa = empresa
            horario.save()
            messages.success(request, 'Horário criado com sucesso!')
            return redirect('horarios_list')
    else:
        form = HorarioAtendimentoForm(
            initial={'profissional': request.GET.get('profissional') or None}
        )
        form.fields['profissional'].queryset = Profissional.objects.filter(empresa=empresa, ativo=True)
    
    return render(request, 'core/cliente/horario_form.html', {'form': form})


@login_required
@empresa_required
def horario_bulk_create(request):
    """Cria o mesmo intervalo de horário em vários dias da semana de uma vez."""
    empresa = request.user.empresa

    if request.method == 'POST':
        form = HorarioBulkForm(request.POST)
        form.fields['profissional'].queryset = Profissional.objects.filter(empresa=empresa, ativo=True)
        if form.is_valid():
            profissional = form.cleaned_data['profissional']
            dias = form.cleaned_data['dias_semana']
            hi = form.cleaned_data['hora_inicio']
            hf = form.cleaned_data['hora_fim']
            intervalo = form.cleaned_data['intervalo_minutos']
            criados = 0
            for dia in dias:
                HorarioAtendimento.objects.create(
                    empresa=empresa,
                    profissional=profissional,
                    dia_semana=int(dia),
                    hora_inicio=hi,
                    hora_fim=hf,
                    intervalo_minutos=intervalo,
                    ativo=True,
                )
                criados += 1
            messages.success(
                request,
                f'{criados} horário(s) cadastrado(s) com sucesso para {profissional.nome}.',
            )
            return redirect('horarios_list')
    else:
        form = HorarioBulkForm(
            initial={'profissional': request.GET.get('profissional') or None}
        )
        form.fields['profissional'].queryset = Profissional.objects.filter(empresa=empresa, ativo=True)

    return render(request, 'core/cliente/horario_bulk_form.html', {'form': form})


@login_required
@empresa_required
def horario_edit(request, pk):
    """Editar horário de atendimento"""
    empresa = request.user.empresa
    horario = get_object_or_404(HorarioAtendimento, pk=pk, empresa=empresa)
    
    if request.method == 'POST':
        form = HorarioAtendimentoForm(request.POST, instance=horario)
        form.fields['profissional'].queryset = Profissional.objects.filter(empresa=empresa, ativo=True)
        if form.is_valid():
            form.save()
            messages.success(request, 'Horário atualizado com sucesso!')
            return redirect('horarios_list')
    else:
        form = HorarioAtendimentoForm(instance=horario)
        form.fields['profissional'].queryset = Profissional.objects.filter(empresa=empresa, ativo=True)
    
    return render(request, 'core/cliente/horario_form.html', {'form': form, 'horario': horario})


@login_required
@empresa_required
def horario_delete(request, pk):
    """Excluir horário de atendimento"""
    empresa = request.user.empresa
    horario = get_object_or_404(HorarioAtendimento, pk=pk, empresa=empresa)
    
    if request.method == 'POST':
        horario.delete()
        messages.success(request, 'Horário excluído com sucesso!')
        return redirect('horarios_list')
    
    return render(request, 'core/cliente/horario_delete.html', {'horario': horario})


# ========== CLIENTE - GERENCIAMENTO DE AGENDAMENTOS ==========

@login_required
@empresa_required
def agendamentos_list(request):
    """Lista de agendamentos"""
    empresa = request.user.empresa
    agendamentos = Agendamento.objects.filter(empresa=empresa).select_related('servico', 'profissional')
    
    # Filtros
    status = request.GET.get('status')
    if status:
        agendamentos = agendamentos.filter(status=status)
    
    data = request.GET.get('data')
    if data:
        agendamentos = agendamentos.filter(data=data)
    
    profissional_id = request.GET.get('profissional')
    if profissional_id:
        agendamentos = agendamentos.filter(profissional_id=profissional_id)
    
    profissionais = Profissional.objects.filter(empresa=empresa, ativo=True)
    
    return render(request, 'core/cliente/agendamentos_list.html', {
        'agendamentos': agendamentos.order_by('-data', '-hora'),
        'profissionais': profissionais,
        'status': status or '',
        'data': data or '',
        'profissional_id': profissional_id or '',
    })


@login_required
@empresa_required
def agendamento_create(request):
    """Criar agendamento"""
    empresa = request.user.empresa
    
    if request.method == 'POST':
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            agendamento = form.save(commit=False)
            agendamento.empresa = empresa
            agendamento.save()
            
            # Enviar mensagem WhatsApp se configurado
            if agendamento.status == 'confirmado':
                WhatsAppService.enviar_confirmacao(agendamento)
            
            messages.success(request, 'Agendamento criado com sucesso!')
            return redirect('agendamentos_list')
    else:
        form = AgendamentoForm()
        form.fields['servico'].queryset = Servico.objects.filter(empresa=empresa, ativo=True)
        form.fields['profissional'].queryset = Profissional.objects.filter(empresa=empresa, ativo=True)
    
    return render(request, 'core/cliente/agendamento_form.html', {'form': form})


@login_required
@empresa_required
def agendamento_edit(request, pk):
    """Editar agendamento"""
    empresa = request.user.empresa
    agendamento = get_object_or_404(Agendamento, pk=pk, empresa=empresa)
    status_anterior = agendamento.status
    
    if request.method == 'POST':
        form = AgendamentoForm(request.POST, instance=agendamento)
        if form.is_valid():
            agendamento = form.save()
            
            # Enviar mensagem se mudou para confirmado
            if status_anterior != 'confirmado' and agendamento.status == 'confirmado':
                WhatsAppService.enviar_confirmacao(agendamento)
            
            messages.success(request, 'Agendamento atualizado com sucesso!')
            return redirect('agendamentos_list')
    else:
        form = AgendamentoForm(instance=agendamento)
        form.fields['servico'].queryset = Servico.objects.filter(empresa=empresa, ativo=True)
        form.fields['profissional'].queryset = Profissional.objects.filter(empresa=empresa, ativo=True)
    
    return render(request, 'core/cliente/agendamento_form.html', {'form': form, 'agendamento': agendamento})


@login_required
@empresa_required
def agendamento_delete(request, pk):
    """Excluir agendamento"""
    empresa = request.user.empresa
    agendamento = get_object_or_404(Agendamento, pk=pk, empresa=empresa)
    
    if request.method == 'POST':
        agendamento.delete()
        messages.success(request, 'Agendamento excluído com sucesso!')
        return redirect('agendamentos_list')
    
    return render(request, 'core/cliente/agendamento_delete.html', {'agendamento': agendamento})


# ========== PÁGINA PÚBLICA DE AGENDAMENTO ==========

def _horarios_disponiveis_publico(empresa, profissional, data_agendamento):
    horarios_cadastrados = HorarioAtendimento.objects.filter(
        empresa=empresa,
        profissional=profissional,
        dia_semana=data_agendamento.weekday(),
        ativo=True
    ).order_by('hora_inicio')

    horarios_ocupados = set(
        Agendamento.objects.filter(
            empresa=empresa,
            profissional=profissional,
            data=data_agendamento
        ).values_list('hora', flat=True)
    )

    horarios_disponiveis = []
    hoje = timezone.localdate()
    agora = timezone.localtime().time().replace(second=0, microsecond=0)
    for horario in horarios_cadastrados:
        inicio_dt = datetime.combine(data_agendamento, horario.hora_inicio)
        fim_dt = datetime.combine(data_agendamento, horario.hora_fim)
        passo = timedelta(minutes=horario.intervalo_minutos or 30)

        while inicio_dt < fim_dt:
            hora_slot = inicio_dt.time().replace(second=0, microsecond=0)
            if data_agendamento == hoje and hora_slot <= agora:
                inicio_dt += passo
                continue
            if hora_slot not in horarios_ocupados:
                horarios_disponiveis.append(hora_slot.strftime('%H:%M'))
            inicio_dt += passo

    # Remove duplicados e ordena por horário mais próximo
    unicos = list(dict.fromkeys(horarios_disponiveis))
    return sorted(unicos, key=lambda h: datetime.strptime(h, '%H:%M').time())

def agendamento_publico(request, empresa_slug=None):
    """Página pública para agendamento"""
    # Se não tem slug, lista empresas ou redireciona
    if not empresa_slug:
        empresas = Empresa.objects.filter(ativo=True, assinatura__ativa=True)
        return render(request, 'core/publico/escolher_empresa.html', {'empresas': empresas})
    
    empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
    
    # Verificar se tem assinatura e se está ativa
    if not hasattr(empresa, 'assinatura') or empresa.assinatura.esta_vencida():
        messages.error(request, 'Esta empresa não está disponível para agendamentos no momento.')
        return redirect('agendamento_publico')
    
    if request.method == 'POST':
        form = AgendamentoPublicoForm(empresa=empresa, data=request.POST)
        if form.is_valid():
            # Criar agendamento manualmente (AgendamentoPublicoForm é Form, não ModelForm)
            agendamento = Agendamento.objects.create(
                empresa=empresa,
                servico=form.cleaned_data['servico'],
                profissional=form.cleaned_data['profissional'],
                data=form.cleaned_data['data'],
                hora=form.cleaned_data['hora'],
                cliente_nome=form.cleaned_data['cliente_nome'],
                cliente_telefone=form.cleaned_data['cliente_telefone'],
                cliente_email=form.cleaned_data.get('cliente_email', ''),
                observacoes=form.cleaned_data.get('observacoes', ''),
                status='pendente'
            )
            
            # Enviar mensagem de confirmação
            WhatsAppService.enviar_confirmacao(agendamento)
            
            messages.success(request, 'Agendamento realizado com sucesso! Você receberá uma confirmação em breve.')
            request.session['ultimo_ag_publico_id'] = agendamento.pk
            return redirect('agendamento_publico_sucesso', empresa_slug=empresa_slug)
    else:
        form = AgendamentoPublicoForm(empresa=empresa)
    
    # Buscar dados para exibição
    servicos = Servico.objects.filter(empresa=empresa, ativo=True).order_by('nome')
    profissionais = Profissional.objects.filter(empresa=empresa, ativo=True).order_by('nome')
    horarios_atendimento = HorarioAtendimento.objects.filter(
        empresa=empresa,
        ativo=True,
        profissional__isnull=False
    ).select_related('profissional').order_by('profissional__nome', 'dia_semana', 'hora_inicio')
    
    return render(request, 'core/publico/agendamento.html', {
        'empresa': empresa,
        'form': form,
        'servicos': servicos,
        'profissionais': profissionais,
        'horarios_atendimento': horarios_atendimento,
    })


def api_dias_disponiveis(request, empresa_slug):
    """Retorna os dias da semana (0-6) que um barbeiro tem horário cadastrado."""
    empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
    profissional_id = request.GET.get('profissional')
    if not profissional_id:
        return JsonResponse({'dias': []})
    try:
        profissional = Profissional.objects.get(pk=profissional_id, empresa=empresa, ativo=True)
    except Profissional.DoesNotExist:
        return JsonResponse({'dias': []})
    dias_qs = HorarioAtendimento.objects.filter(
        empresa=empresa, profissional=profissional, ativo=True
    ).values_list('dia_semana', flat=True).distinct()
    # Garante inteiros 0–6 (Seg–Dom, igual a date.weekday() no Django)
    dias = sorted({int(d) for d in dias_qs})
    return JsonResponse({'dias': dias})


def api_horarios_publicos(request, empresa_slug):
    """Retorna horários disponíveis por barbeiro e data (JSON)."""
    empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)

    if not hasattr(empresa, 'assinatura') or empresa.assinatura.esta_vencida():
        return JsonResponse({'horarios': [], 'erro': 'Empresa indisponível no momento.'}, status=403)

    profissional_id = request.GET.get('profissional')
    data_str = request.GET.get('data')

    if not profissional_id or not data_str:
        return JsonResponse({'horarios': []})

    try:
        profissional = Profissional.objects.get(pk=profissional_id, empresa=empresa, ativo=True)
        data_agendamento = datetime.strptime(data_str, '%Y-%m-%d').date()
    except (Profissional.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'horarios': []})

    horarios = _horarios_disponiveis_publico(empresa, profissional, data_agendamento)
    return JsonResponse({'horarios': horarios})


def empresa_detalhes(request, empresa_slug):
    """Página de detalhes da empresa (pública)"""
    empresa = get_object_or_404(Empresa, slug=empresa_slug, ativo=True)
    
    # Verificar se tem assinatura e se está ativa
    if not hasattr(empresa, 'assinatura') or empresa.assinatura.esta_vencida():
        messages.error(request, 'Esta empresa não está disponível para agendamentos no momento.')
        return redirect('agendamento_publico')
    
    # Buscar dados para exibição
    servicos = Servico.objects.filter(empresa=empresa, ativo=True).order_by('nome')
    horarios_atendimento = HorarioAtendimento.objects.filter(
        empresa=empresa,
        ativo=True,
        profissional__isnull=False
    ).select_related('profissional').order_by('profissional__nome', 'dia_semana', 'hora_inicio')
    
    return render(request, 'core/publico/empresa_detalhes.html', {
        'empresa': empresa,
        'servicos': servicos,
        'horarios_atendimento': horarios_atendimento,
    })


def agendamento_publico_sucesso(request, empresa_slug):
    """Página de sucesso do agendamento público"""
    from urllib.parse import quote

    empresa = get_object_or_404(Empresa, slug=empresa_slug)

    agendamento = None
    aid = request.session.pop('ultimo_ag_publico_id', None)
    if aid is not None:
        try:
            agendamento = Agendamento.objects.select_related('servico', 'profissional').get(
                pk=int(aid), empresa=empresa
            )
        except (Agendamento.DoesNotExist, ValueError, TypeError):
            agendamento = None

    def _digitos_tel(val):
        if not val:
            return ''
        return ''.join(c for c in str(val) if c.isdigit())

    raw = (empresa.whatsapp_numero or empresa.telefone or '').strip()
    digitos = _digitos_tel(raw)
    if digitos.startswith('55'):
        wa_tel_barbearia = digitos
    elif digitos:
        wa_tel_barbearia = '55' + digitos.lstrip('0')
    else:
        wa_tel_barbearia = ''

    if agendamento and wa_tel_barbearia:
        msg = (
            f"Olá! Acabei de agendar pelo site ({empresa.nome}). "
            f"Lembrar do meu horário: {agendamento.data.strftime('%d/%m/%Y')} às {agendamento.hora.strftime('%H:%M')} "
            f"com {agendamento.profissional.nome} — {agendamento.servico.nome}. "
            f"Cliente: {agendamento.cliente_nome}."
        )
        wa_lembrar_url = f'https://wa.me/{wa_tel_barbearia}?text={quote(msg)}'
    elif wa_tel_barbearia:
        msg = f"Olá! Acabei de fazer um agendamento pelo site da {empresa.nome}. Pode confirmar?"
        wa_lembrar_url = f'https://wa.me/{wa_tel_barbearia}?text={quote(msg)}'
    else:
        wa_lembrar_url = ''

    suporte_url = 'https://wa.me/5531982435468?text=' + quote('Olá! Preciso de suporte com o Agenda PRO.')

    return render(request, 'core/publico/agendamento_sucesso.html', {
        'empresa': empresa,
        'agendamento': agendamento,
        'wa_lembrar_url': wa_lembrar_url,
        'suporte_url': suporte_url,
    })


# ========== API ALERTA DE AGENDAMENTOS (CLIENTE / BARBEARIA) ==========

@login_required
def api_agendamentos_alerta(request):
    """Conta pendentes e quantos agendamentos novos desde `since` (ISO)."""
    if not request.user.is_authenticated:
        return JsonResponse({'pendente_total': 0, 'novos': 0, 'server_time': timezone.now().isoformat()})

    if request.user.is_super_admin():
        return JsonResponse({'pendente_total': 0, 'novos': 0, 'server_time': timezone.now().isoformat()})

    try:
        empresa = request.user.empresa
    except (Empresa.DoesNotExist, AttributeError):
        return JsonResponse({'pendente_total': 0, 'novos': 0, 'server_time': timezone.now().isoformat()})

    pendente_total = Agendamento.objects.filter(empresa=empresa, status='pendente').count()

    novos = 0
    since = request.GET.get('since', '').strip()
    if since:
        from django.utils.dateparse import parse_datetime

        dt = parse_datetime(since.replace('Z', '+00:00'))
        if dt is not None:
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.get_current_timezone())
            novos = Agendamento.objects.filter(empresa=empresa, criado_em__gt=dt).count()

    return JsonResponse({
        'pendente_total': pendente_total,
        'novos': novos,
        'server_time': timezone.now().isoformat(),
    })


# ========== API PARA ANÚNCIOS ==========

def api_anuncios(request):
    """Anúncios do super admin: só para clientes com assinatura ativa."""
    if not request.user.is_authenticated:
        return JsonResponse({'anuncios': []})

    if request.user.tipo == 'super_admin':
        return JsonResponse({'anuncios': []})

    if not hasattr(request.user, 'empresa'):
        return JsonResponse({'anuncios': []})

    from .mensagens import empresa_tem_assinatura_ativa
    if not empresa_tem_assinatura_ativa(request.user.empresa):
        return JsonResponse({'anuncios': []})

    anuncios_ativos = Anuncio.objects.filter(ativo=True)
    anuncios_data = []

    for anuncio in anuncios_ativos:
        if anuncio.esta_ativo():
            anuncios_data.append({
                'id': anuncio.id,
                'titulo': anuncio.titulo,
                'mensagem': anuncio.mensagem,
                'tipo': anuncio.tipo,
            })

    return JsonResponse({'anuncios': anuncios_data})


@login_required
@empresa_required
def api_agendamento_detalhe(request, pk):
    """Detalhes do agendamento + mensagens prontas para WhatsApp (JSON)."""
    from .mensagens import formatar_mensagem_agendamento, url_whatsapp

    empresa = request.user.empresa
    agendamento = get_object_or_404(
        Agendamento.objects.select_related('servico', 'profissional'),
        pk=pk,
        empresa=empresa,
    )

    padrao_conf = (
        'Olá {cliente}! Seu agendamento na {empresa} foi confirmado para {data} às {hora} '
        'com {profissional} — serviço: {servico}. Até lá!'
    )
    padrao_lembrete = (
        'Olá {cliente}! Lembrete: você tem horário em {data} às {hora} com {profissional} '
        '({servico}) na {empresa}.'
    )
    padrao_pendente = (
        'Olá {cliente}! Recebemos seu pedido de agendamento para {data} às {hora} '
        'com {profissional} ({servico}) na {empresa}. Em breve confirmamos!'
    )

    msg_confirmacao = formatar_mensagem_agendamento(
        empresa.mensagem_confirmacao, agendamento, padrao_conf
    )
    msg_lembrete = formatar_mensagem_agendamento(
        empresa.mensagem_lembrete, agendamento, padrao_lembrete
    )
    msg_pendente = formatar_mensagem_agendamento('', agendamento, padrao_pendente)

    tel = agendamento.cliente_telefone or ''

    status_labels = {
        'pendente': 'Pendente',
        'confirmado': 'Confirmado',
        'cancelado': 'Cancelado',
        'concluido': 'Concluído',
    }

    return JsonResponse({
        'id': agendamento.pk,
        'cliente_nome': agendamento.cliente_nome,
        'cliente_telefone': tel,
        'cliente_email': agendamento.cliente_email or '',
        'servico': agendamento.servico.nome,
        'profissional': agendamento.profissional.nome,
        'data': agendamento.data.strftime('%d/%m/%Y'),
        'hora': agendamento.hora.strftime('%H:%M'),
        'status': agendamento.status,
        'status_label': status_labels.get(agendamento.status, agendamento.status),
        'observacoes': agendamento.observacoes or '',
        'edit_url': f'/agendamentos/{agendamento.pk}/editar/',
        'delete_url': f'/agendamentos/{agendamento.pk}/excluir/',
        'mensagens': {
            'confirmacao': msg_confirmacao,
            'lembrete': msg_lembrete,
            'pendente': msg_pendente,
        },
        'whatsapp': {
            'confirmacao': url_whatsapp(tel, msg_confirmacao),
            'lembrete': url_whatsapp(tel, msg_lembrete),
            'pendente': url_whatsapp(tel, msg_pendente),
        },
    })

