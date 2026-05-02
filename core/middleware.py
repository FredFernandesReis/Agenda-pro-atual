from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import logout
from .models import Empresa


class AssinaturaMiddleware:
    """Middleware para verificar se a assinatura está ativa"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # URLs que não precisam verificar assinatura (incluindo admin)
        public_urls = [
            '/login/',
            '/logout/',
            '/agendamento-publico/',
            '/admin/',
            '/static/',
            '/media/',
        ]
        
        # Se não está autenticado ou é URL pública, continua
        if not request.user.is_authenticated or any(request.path.startswith(url) for url in public_urls):
            response = self.get_response(request)
            return response
        
        # Super Admin não precisa verificar assinatura
        if request.user.is_super_admin():
            response = self.get_response(request)
            return response
        
        # Verifica se o usuário tem empresa e assinatura
        try:
            empresa = request.user.empresa
            assinatura = empresa.assinatura
            
            # Se a assinatura está vencida, redireciona para tela de aviso
            if assinatura.esta_vencida():
                # Permite acesso apenas à página de assinatura vencida
                if request.path != '/assinatura-vencida/':
                    return redirect('assinatura_vencida')
        except (Empresa.DoesNotExist, AttributeError):
            # Se não tem empresa, permite acesso (pode ser super admin sem empresa)
            pass
        
        response = self.get_response(request)
        return response

