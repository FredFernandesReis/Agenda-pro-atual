"""Formatação de mensagens WhatsApp e URLs wa.me."""
from urllib.parse import quote


def formatar_mensagem_agendamento(template, agendamento, padrao=''):
    texto = (template or padrao or '').strip()
    if not texto:
        return ''
    return texto.format(
        data=agendamento.data.strftime('%d/%m/%Y'),
        hora=agendamento.hora.strftime('%H:%M'),
        profissional=agendamento.profissional.nome,
        servico=agendamento.servico.nome,
        cliente=agendamento.cliente_nome,
        empresa=agendamento.empresa.nome,
    )


def telefone_para_wa(numero):
    if not numero:
        return ''
    digitos = ''.join(c for c in str(numero) if c.isdigit())
    if not digitos:
        return ''
    if digitos.startswith('55'):
        return digitos
    return '55' + digitos.lstrip('0')


def url_whatsapp(telefone, mensagem):
    tel = telefone_para_wa(telefone)
    if not tel:
        return ''
    base = f'https://wa.me/{tel}'
    if mensagem:
        return f'{base}?text={quote(mensagem)}'
    return base


def empresa_tem_assinatura_ativa(empresa):
    if not empresa:
        return False
    from .models import Assinatura
    try:
        assinatura = empresa.assinatura
    except Assinatura.DoesNotExist:
        return False
    return assinatura.ativa and not assinatura.esta_vencida()
