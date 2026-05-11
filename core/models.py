from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.text import slugify
from datetime import timedelta


class User(AbstractUser):
    """Modelo de usuário customizado"""
    TIPO_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('cliente', 'Cliente'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='cliente')
    telefone = models.CharField(max_length=20, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.username
    
    def is_super_admin(self):
        return self.tipo == 'super_admin'


class Empresa(models.Model):
    """Modelo de empresa/cliente"""
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='empresa')
    nome = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True, null=True)
    cnpj = models.CharField(max_length=18, blank=True, null=True)
    telefone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True, help_text="Opcional")
    endereco = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    # Configurações WhatsApp
    # Identidade visual
    logo = models.ImageField(upload_to='logos/', blank=True, null=True, help_text="Logo da barbearia (será exibida na página pública)")
    foto_capa = models.ImageField(
        upload_to='capas/', blank=True, null=True,
        help_text="Legado: não é mais usado na página pública (apenas logo)."
    )
    descricao = models.TextField(blank=True, null=True, help_text="Descrição curta da barbearia para exibir na página pública")

    # Configurações WhatsApp
    whatsapp_numero = models.CharField(max_length=20, blank=True, null=True, help_text="Número para envio de mensagens WhatsApp")
    mensagem_confirmacao = models.TextField(
        blank=True,
        default="Olá! Seu agendamento foi confirmado para {data} às {hora} com {profissional}. Obrigado!",
        help_text="Use {data}, {hora}, {profissional}, {servico} como variáveis"
    )
    mensagem_lembrete = models.TextField(
        blank=True,
        default="Lembrete: Você tem um agendamento hoje às {hora} com {profissional}. Até breve!",
        help_text="Use {data}, {hora}, {profissional}, {servico} como variáveis"
    )
    
    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
            # Garante que o slug seja único
            original_slug = self.slug
            counter = 1
            while Empresa.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"


class Assinatura(models.Model):
    """Modelo de assinatura da empresa"""
    empresa = models.OneToOneField(Empresa, on_delete=models.CASCADE, related_name='assinatura')
    ativa = models.BooleanField(default=False)
    data_vencimento = models.DateField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        status = "Ativa" if self.ativa else "Inativa"
        return f"{self.empresa.nome} - {status}"
    
    def esta_vencida(self):
        """Verifica se a assinatura está vencida"""
        if not self.ativa:
            return True
        if self.data_vencimento and self.data_vencimento < timezone.now().date():
            return True
        return False
    
    class Meta:
        verbose_name = "Assinatura"
        verbose_name_plural = "Assinaturas"


class Servico(models.Model):
    """Modelo de serviços oferecidos pela empresa"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='servicos')
    nome = models.CharField(max_length=200)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    duracao = models.IntegerField(help_text="Duração em minutos")
    descricao = models.TextField(blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nome} - {self.empresa.nome}"
    
    class Meta:
        verbose_name = "Serviço"
        verbose_name_plural = "Serviços"
        ordering = ['nome']


class Profissional(models.Model):
    """Modelo de profissionais da empresa"""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='profissionais')
    nome = models.CharField(max_length=200)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    especialidades = models.ManyToManyField(Servico, blank=True, related_name='profissionais_especialistas')
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nome} - {self.empresa.nome}"
    
    class Meta:
        verbose_name = "Profissional"
        verbose_name_plural = "Profissionais"
        ordering = ['nome']


class HorarioAtendimento(models.Model):
    """Modelo de horários de atendimento da empresa"""
    DIA_SEMANA_CHOICES = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='horarios_atendimento')
    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.CASCADE,
        related_name='horarios_atendimento',
        null=True,
        blank=True,
        help_text="Deixe em branco para um horário geral da empresa"
    )
    dia_semana = models.IntegerField(choices=DIA_SEMANA_CHOICES)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()
    intervalo_minutos = models.IntegerField(default=30, help_text="Intervalo entre agendamentos em minutos")
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        dias = dict(self.DIA_SEMANA_CHOICES)
        profissional = self.profissional.nome if self.profissional else "Geral da empresa"
        return f"{profissional} - {dias[self.dia_semana]} - {self.hora_inicio} às {self.hora_fim}"
    
    class Meta:
        verbose_name = "Horário de Atendimento"
        verbose_name_plural = "Horários de Atendimento"
        ordering = ['dia_semana', 'hora_inicio']


class Agendamento(models.Model):
    """Modelo de agendamentos"""
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado'),
        ('concluido', 'Concluído'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE, related_name='agendamentos')
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE, related_name='agendamentos')
    data = models.DateField()
    hora = models.TimeField()
    cliente_nome = models.CharField(max_length=200)
    cliente_telefone = models.CharField(max_length=20)
    cliente_email = models.EmailField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    lembrete_enviado = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.cliente_nome} - {self.data} {self.hora}"
    
    class Meta:
        verbose_name = "Agendamento"
        verbose_name_plural = "Agendamentos"
        ordering = ['-data', '-hora']


class Anuncio(models.Model):
    """Modelo de anúncios do sistema"""
    TIPO_CHOICES = [
        ('info', 'Informação'),
        ('success', 'Sucesso'),
        ('warning', 'Aviso'),
        ('danger', 'Importante'),
    ]
    
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='info')
    ativo = models.BooleanField(default=True)
    data_inicio = models.DateTimeField(auto_now_add=True)
    data_fim = models.DateTimeField(null=True, blank=True, help_text="Deixe em branco para não expirar")
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.titulo
    
    def esta_ativo(self):
        """Verifica se o anúncio está ativo"""
        if not self.ativo:
            return False
        if self.data_fim and timezone.now() > self.data_fim:
            return False
        return True
    
    class Meta:
        verbose_name = "Anúncio"
        verbose_name_plural = "Anúncios"
        ordering = ['-criado_em']

