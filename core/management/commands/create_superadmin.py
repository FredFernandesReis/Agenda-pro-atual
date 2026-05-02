from django.core.management.base import BaseCommand
from core.models import User


class Command(BaseCommand):
    help = 'Cria um usuário super admin'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Nome de usuário')
        parser.add_argument('--email', type=str, help='E-mail')
        parser.add_argument('--password', type=str, help='Senha')

    def handle(self, *args, **options):
        username = options.get('username') or input('Username: ')
        email = options.get('email') or input('Email: ')
        password = options.get('password') or input('Password: ')
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f'Usuário {username} já existe!'))
            return
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            tipo='super_admin'
        )
        
        self.stdout.write(self.style.SUCCESS(f'Super admin {username} criado com sucesso!'))


