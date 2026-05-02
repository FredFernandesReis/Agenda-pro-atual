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
            # Se está criando, username e email são obrigatórios
            self.fields['username'].required = True
            self.fields['email'].required = True


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
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duracao': forms.NumberInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProfissionalForm(forms.ModelForm):
    class Meta:
        model = Profissional
        fields = ['nome', 'telefone', 'email', 'especialidades', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'especialidades': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


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
    servico = forms.ModelChoiceField(
        queryset=Servico.objects.none(),
        label='Serviço',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    profissional = forms.ModelChoiceField(
        queryset=Profissional.objects.none(),
        label='Profissional',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    data = forms.DateField(
        label='Data',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    hora = forms.ChoiceField(
        label='Horário',
        choices=[],
        widget=forms.Select(attrs={'class': 'form-control'})
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
        self.fields['hora'].choices = [('', 'Selecione o barbeiro e a data')]
        self.fields['data'].widget.attrs['min'] = timezone.localdate().isoformat()
        if empresa:
            self.fields['servico'].queryset = Servico.objects.filter(empresa=empresa, ativo=True)
            self.fields['profissional'].queryset = Profissional.objects.filter(empresa=empresa, ativo=True)
            self._preencher_horarios_disponiveis()

    def _preencher_horarios_disponiveis(self):
        profissional_id = self.data.get('profissional') if self.is_bound else None
        data_str = self.data.get('data') if self.is_bound else None

        if not profissional_id or not data_str:
            return

        try:
            profissional = Profissional.objects.get(pk=profissional_id, empresa=self.empresa, ativo=True)
            data_agendamento = datetime.strptime(data_str, '%Y-%m-%d').date()
        except (Profissional.DoesNotExist, ValueError, TypeError):
            return

        horarios = HorarioAtendimento.objects.filter(
            empresa=self.empresa,
            profissional=profissional,
            dia_semana=data_agendamento.weekday(),
            ativo=True
        ).order_by('hora_inicio')

        ocupados = set(
            Agendamento.objects.filter(
                empresa=self.empresa,
                profissional=profissional,
                data=data_agendamento
            ).values_list('hora', flat=True)
        )

        opcoes = []
        hoje = timezone.localdate()
        agora = timezone.localtime().time().replace(second=0, microsecond=0)
        for horario in horarios:
            inicio_dt = datetime.combine(data_agendamento, horario.hora_inicio)
            fim_dt = datetime.combine(data_agendamento, horario.hora_fim)
            passo = timedelta(minutes=horario.intervalo_minutos or 30)

            while inicio_dt < fim_dt:
                hora_slot = inicio_dt.time().replace(second=0, microsecond=0)
                if data_agendamento == hoje and hora_slot <= agora:
                    inicio_dt += passo
                    continue

                if hora_slot not in ocupados:
                    valor = hora_slot.strftime('%H:%M')
                    opcoes.append((valor, valor))
                inicio_dt += passo

        unicas = list(dict.fromkeys(opcoes))
        self.fields['hora'].choices = unicas or [('', 'Sem horários disponíveis para este barbeiro nesta data')]

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

