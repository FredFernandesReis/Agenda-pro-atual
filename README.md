# Agenda PRO - Sistema de Agendamento Online

Sistema completo para gerenciamento de agendamentos para pequenos negócios.

## 🚀 Início Rápido

### 1. Instalar e Configurar

```bash
# Instalar dependências
pip install -r requirements.txt

# Criar banco de dados
python manage.py migrate

# Criar Super Admin
python manage.py create_superadmin

# Iniciar servidor
python manage.py runserver
```

Acesse: `http://localhost:8000`

### 2. Criar Primeira Empresa

1. Login como Super Admin
2. Vá em **"Empresas"** → **"Nova Empresa"**
3. Preencha os dados e salve
4. Clique no ícone de **cartão** para ativar a assinatura

### 3. Configurar Empresa

1. Faça logout e login como cliente
2. Cadastre **Serviços**
3. Cadastre **Profissionais**
4. Configure **Horários** de atendimento

### 4. Compartilhar Link

No dashboard do cliente, copie o **link público** e compartilhe com seus clientes!

## 📋 Funcionalidades

- ✅ Gerenciamento de empresas e assinaturas
- ✅ Cadastro de serviços e profissionais
- ✅ Configuração de horários
- ✅ Agendamentos online (página pública)
- ✅ Dashboard com estatísticas
- ✅ Controle completo de agendamentos

## 🔐 Tipos de Usuário

- **Super Admin**: Gerencia empresas e assinaturas
- **Cliente**: Gerencia serviços, profissionais e agendamentos

## 📱 Página Pública

Cada empresa tem sua própria página de agendamento:
- `/agendamento-publico/<slug-da-empresa>/`

Compartilhe o link com seus clientes para agendamentos online!

## ⚙️ Requisitos

- Python 3.8+
- Django 4.2+

## 📝 Notas

- Assinaturas são ativadas manualmente pelo Super Admin
- Cada empresa tem dados totalmente isolados
- Sistema pronto para uso comercial
