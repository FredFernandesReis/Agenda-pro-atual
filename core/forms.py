from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import User, Empresa, Assinatura, Servico, Profissional, HorarioAtendimento, Agendamento


class LoginForm(forms.Form):
    username = forms.CharField(
        label='Usuário',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite seu usuário'})
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Digite sua senha'})
    )


class EmpresaForm(forms.ModelForm):
    username = forms.CharField(
        label='Usuário',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    email = forms.EmailField(
        label='E-mail',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=False
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    class Meta:
        model = Empresa
        fields = ['nome', 'cnpj', 'telefone', 'email', 'endereco', 'whatsapp_numero', 
                  'mensagem_confirmacao', 'mensagem_lembrete']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cnpj': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'whatsapp_numero': forms.TextInput(attrs={'class': 'form-control'}),
            'mensagem_confirmacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'mensagem_lembrete': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Se está editando, torna username e email opcionais
            self.fields['username'].required = False
            self.fields['email'].required = False
        else:
            # Criação: usuário obrigatório; e-mail opcional (admin / fluxo interno)
            self.fields['username'].required = True
            self.fields['email'].required = False


class EmpresaPerfilForm(forms.ModelForm):
    """Form para o dono da barbearia editar seu próprio perfil."""
    class Meta:
        model = Empresa
        fields = ['nome', 'telefone', 'email', 'endereco', 'descricao',
                  'logo', 'whatsapp_numero',
                  'mensagem_confirmacao', 'mensagem_lembrete']
        widgets = {
            'nome':                forms.TextInput(attrs={'class': 'form-control'}),
            'telefone':            forms.TextInput(attrs={'class': 'form-control'}),
            'email':               forms.EmailInput(attrs={'class': 'form-control'}),
            'endereco':            forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'descricao':           forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                                         'placeholder': 'Ex: A melhor barbearia da região, especializada em cortes modernos...'}),
            'whatsapp_numero':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': '31999999999'}),
            'mensagem_confirmacao':forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'mensagem_lembrete':   forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'logo':                forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


class AssinaturaForm(forms.ModelForm):
    class Meta:
        model = Assinatura
        fields = ['ativa', 'data_vencimento']
        widgets = {
            'ativa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_vencimento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ['nome', 'preco', 'duracao', 'descricao', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Corte masculino, Barba, Combo…',
            }),
            'preco': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0,00',
            }),
            'duracao': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '5',
                'step': '5',
                'placeholder': '30',
            }),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Opcional — aparece na página pública',
            }),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nome'].help_text = 'Nome curto que o cliente entende na hora de agendar.'
        self.fields['preco'].help_text = 'Valor em reais (use ponto ou vírgula conforme o teclado).'
        self.fields['duracao'].help_text = 'Tempo médio em minutos (ex.: 30, 45).'


class ProfissionalForm(forms.ModelForm):
    class Meta:
        model = Profissional
        fields = ['nome', 'telefone', 'email', 'especialidades', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nome do barbeiro',
            }),
            'telefone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Opcional — WhatsApp',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Opcional',
            }),
            'especialidades': forms.CheckboxSelectMultiple(attrs={'class': 'esp-checkboxes'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nome'].help_text = 'Como o nome aparece para o cliente na página pública.'
        self.fields['especialidades'].help_text = (
            'Marque os serviços que este barbeiro faz. Se ainda não cadastrou serviços, faça isso antes.'
        )
        self.fields['especialidades'].required = False


class HorarioAtendimentoForm(forms.ModelForm):
    class Meta:
        model = HorarioAtendimento
        fields = ['profissional', 'dia_semana', 'hora_inicio', 'hora_fim', 'intervalo_minutos', 'ativo']
        widgets = {
            'profissional': forms.Select(attrs={'class': 'form-control'}),
            'dia_semana': forms.Select(attrs={'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'hora_fim': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'intervalo_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profissional'].required = False
        self.fields['profissional'].empty_label = 'Geral da empresa (todos os barbeiros)'

    def clean(self):
        cleaned_data = super().clean()
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fim = cleaned_data.get('hora_fim')

        if hora_inicio and hora_fim and hora_fim <= hora_inicio:
            self.add_error('hora_fim', 'A hora final deve ser maior que a hora inicial.')

        return cleaned_data


class HorarioBulkForm(forms.Form):
    """Um único envio: mesmo horário de início/fim em vários dias da semana para um barbeiro."""

    profissional = forms.ModelChoiceField(
        queryset=Profissional.objects.none(),
        label='Barbeiro',
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    dias_semana = forms.MultipleChoiceField(
        label='Dias da semana',
        choices=HorarioAtendimento.DIA_SEMANA_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'horario-bulk-dias'}),
    )
    hora_inicio = forms.TimeField(
        label='Abre às',
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
    )
    hora_fim = forms.TimeField(
        label='Fecha às',
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
    )
    intervalo_minutos = forms.IntegerField(
        label='Intervalo entre horários (minutos)',
        min_value=5,
        max_value=240,
        initial=30,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 240}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profissional'].help_text = (
            'O mesmo turno será aplicado em todos os dias marcados abaixo.'
        )
        self.fields['dias_semana'].help_text = (
            'Marque todos os dias em que este barbeiro atende neste horário (ex.: seg a sex).'
        )

    def clean(self):
        cleaned = super().clean()
        hi = cleaned.get('hora_inicio')
        hf = cleaned.get('hora_fim')
        if hi and hf and hf <= hi:
            self.add_error('hora_fim', 'O horário de fechamento deve ser depois da abertura.')
        dias = cleaned.get('dias_semana')
        if not dias:
            self.add_error('dias_semana', 'Marque pelo menos um dia da semana.')
        return cleaned


class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['servico', 'profissional', 'data', 'hora', 'cliente_nome', 
                  'cliente_telefone', 'cliente_email', 'observacoes', 'status']
        widgets = {
            'servico': forms.Select(attrs={'class': 'form-control'}),
            'profissional': forms.Select(attrs={'class': 'form-control'}),
            'data': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'cliente_nome': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente_telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'cliente_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        profissional = cleaned_data.get('profissional')
        data = cleaned_data.get('data')
        hora = cleaned_data.get('hora')

        if not profissional or not data or not hora:
            return cleaned_data

        empresa = profissional.empresa
        dia_semana = data.weekday()
        horarios_validos = HorarioAtendimento.objects.filter(
            empresa=empresa,
            dia_semana=dia_semana,
            ativo=True
        ).filter(
            Q(profissional=profissional) | Q(profissional__isnull=True)
        )

        hora_disponivel = any(
            horario.hora_inicio <= hora < horario.hora_fim
            for horario in horarios_validos
        )

        if not hora_disponivel:
            self.add_error(
                'hora',
                'Este horário não está disponível para o barbeiro selecionado.'
            )

        conflito = Agendamento.objects.filter(
            empresa=empresa,
            profissional=profissional,
            data=data,
            hora=hora
        ).exclude(pk=self.instance.pk).exists()

        if conflito:
            self.add_error('hora', 'Já existe um agendamento para esse barbeiro nesse horário.')

        return cleaned_data


class AgendamentoPublicoForm(forms.Form):
    # Campos hidden — preenchidos pelo JS da página pública
    servico = forms.ModelChoiceField(
        queryset=Servico.objects.none(),
        label='Serviço',
        widget=forms.HiddenInput()
    )
    profissional = forms.ModelChoiceField(
        queryset=Profissional.objects.none(),
        label='Profissional',
        widget=forms.HiddenInput()
    )
    data = forms.DateField(
        label='Data',
        widget=forms.HiddenInput()
    )
    hora = forms.CharField(
        label='Horário',
        widget=forms.HiddenInput()
    )
    cliente_nome = forms.CharField(
        label='Seu Nome',
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Digite seu nome completo'})
    )
    cliente_telefone = forms.CharField(
        label='Telefone',
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '(00) 00000-0000'})
    )
    cliente_email = forms.EmailField(
        label='E-mail',
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'seu@email.com'})
    )
    observacoes = forms.CharField(
        label='Observações',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Alguma observação adicional?'})
    )

    def __init__(self, empresa=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.empresa = empresa
        if empresa:
            self.fields['servico'].queryset = Servico.objects.filter(empresa=empresa, ativo=True)
            self.fields['profissional'].queryset = Profissional.objects.filter(empresa=empresa, ativo=True)

    def clean_hora(self):
        hora = self.cleaned_data.get('hora')
        if not hora:
            raise forms.ValidationError('Selecione um horário disponível.')
        try:
            return datetime.strptime(hora, '%H:%M').time()
        except ValueError as exc:
            raise forms.ValidationError('Horário inválido.') from exc

    def clean(self):
        cleaned_data = super().clean()
        profissional = cleaned_data.get('profissional')
        data = cleaned_data.get('data')
        hora = cleaned_data.get('hora')

        if not self.empresa or not profissional or not data or not hora:
            return cleaned_data

        if data < timezone.localdate():
            self.add_error('data', 'Não é permitido agendar em datas passadas.')
            return cleaned_data

        dia_semana = data.weekday()
        horarios_validos = HorarioAtendimento.objects.filter(
            empresa=self.empresa,
            dia_semana=dia_semana,
            ativo=True,
            profissional=profissional
        )

        hora_disponivel = any(
            horario.hora_inicio <= hora < horario.hora_fim
            for horario in horarios_validos
        )

        if not hora_disponivel:
            self.add_error(
                'hora',
                'Este horário não está disponível para o barbeiro selecionado.'
            )

        conflito = Agendamento.objects.filter(
            empresa=self.empresa,
            profissional=profissional,
            data=data,
            hora=hora
        ).exists()

        if conflito:
            self.add_error('hora', 'Esse horário já foi reservado. Escolha outro, por favor.')

        return cleaned_data

