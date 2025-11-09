import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'odontoia.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth.models import User

print("🚀 Iniciando migrações...")
call_command('migrate', interactive=False)

username = "admin"
email = "marcelo@odontoia.com.br"
password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "OdontoIA@2025")

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print("✅ Superusuário criado com sucesso!")
else:
    print("⚠️ Superusuário já existe.")

print("✅ Migrações concluídas com sucesso!")
