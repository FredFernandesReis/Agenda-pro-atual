"""
Serviço para integração com WhatsApp
Estrutura preparada para integração futura com WhatsApp API
"""

from datetime import datetime, timedelta
from django.utils import timezone
from .models import Agendamento


class WhatsAppService:
    """Classe para gerenciar envio de mensagens WhatsApp"""
    
    @staticmethod
    def enviar_confirmacao(agendamento):
        """
        Envia mensagem de confirmação de agendamento
        TODO: Implementar integração real com WhatsApp API
        """
        empresa = agendamento.empresa
        
        # Verifica se tem número WhatsApp configurado
        if not empresa.whatsapp_numero:
            return False
        
        # Formata mensagem
        mensagem = empresa.mensagem_confirmacao or "Olá! Seu agendamento foi confirmado para {data} às {hora} com {profissional}. Obrigado!"
        
        # Substitui variáveis
        mensagem = mensagem.format(
            data=agendamento.data.strftime('%d/%m/%Y'),
            hora=agendamento.hora.strftime('%H:%M'),
            profissional=agendamento.profissional.nome,
            servico=agendamento.servico.nome
        )
        
        # TODO: Implementar envio real via API
        # Exemplo: enviar_via_api(empresa.whatsapp_numero, agendamento.cliente_telefone, mensagem)
        
        print(f"[WHATSAPP] Enviando para {agendamento.cliente_telefone}: {mensagem}")
        return True
    
    @staticmethod
    def enviar_lembrete(agendamento):
        """
        Envia lembrete 1 hora antes do agendamento
        TODO: Implementar integração real com WhatsApp API
        """
        empresa = agendamento.empresa
        
        # Verifica se tem número WhatsApp configurado
        if not empresa.whatsapp_numero:
            return False
        
        # Formata mensagem
        mensagem = empresa.mensagem_lembrete or "Lembrete: Você tem um agendamento hoje às {hora} com {profissional}. Até breve!"
        
        # Substitui variáveis
        mensagem = mensagem.format(
            data=agendamento.data.strftime('%d/%m/%Y'),
            hora=agendamento.hora.strftime('%H:%M'),
            profissional=agendamento.profissional.nome,
            servico=agendamento.servico.nome
        )
        
        # TODO: Implementar envio real via API
        # Exemplo: enviar_via_api(empresa.whatsapp_numero, agendamento.cliente_telefone, mensagem)
        
        print(f"[WHATSAPP] Enviando lembrete para {agendamento.cliente_telefone}: {mensagem}")
        return True
    
    @staticmethod
    def processar_lembretes():
        """
        Processa e envia lembretes para agendamentos que estão 1 hora antes
        Deve ser executado periodicamente (ex: via Celery ou cron)
        """
        agora = timezone.now()
        uma_hora_depois = agora + timedelta(hours=1)
        
        # Busca agendamentos confirmados que estão entre agora e 1 hora depois
        agendamentos = Agendamento.objects.filter(
            status='confirmado',
            data=agora.date(),
            hora__gte=agora.time(),
            hora__lte=uma_hora_depois.time(),
            lembrete_enviado=False
        )
        
        for agendamento in agendamentos:
            if WhatsAppService.enviar_lembrete(agendamento):
                agendamento.lembrete_enviado = True
                agendamento.save()
        
        return agendamentos.count()


