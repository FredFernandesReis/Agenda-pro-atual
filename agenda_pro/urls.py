"""
URL configuration for agenda_pro project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # Produção (VPS): com DEBUG=False o static() acima não roda. Logos ficam em MEDIA_ROOT.
    # Ideal: Nginx servir /media/ (veja deploy/nginx-media.conf.example).
    # Fallback: Gunicorn entrega /media/ aqui (funciona se o proxy mandar /media/ para o Django).
    _media_prefix = settings.MEDIA_URL.strip('/')
    if _media_prefix:
        urlpatterns += [
            re_path(
                rf'^{_media_prefix}/(?P<path>.*)$',
                serve,
                {'document_root': settings.MEDIA_ROOT},
            ),
        ]


