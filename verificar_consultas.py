import os, django
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "odontoia.settings")
django.setup()

from clinic.models import Consulta

print("\n📋 Consultas registradas:\n")

hoje = timezone.now().date()
passadas, futuras, ultimos_30 = 0, 0, 0

for c in Consulta.objects.select_related("paciente", "dentista"):
    data = c.data.date()
    situacao = "🕒"
    if data < hoje:
        situacao = "⏳ Passada"
        passadas += 1
    elif data > hoje:
        situacao = "📅 Futura"
        futuras += 1
    else:
        situacao = "📍 Hoje"

    if data >= hoje - timedelta(days=30):
        ultimos_30 += 1

    print(f"{c.paciente.nome:20} | {c.dentista.nome if c.dentista else '-':25} | {data} | valor_final={c.valor_final} | comissao={c.comissao_valor} | {situacao}")

print("\nResumo:")
print(f"🔹 Consultas passadas: {passadas}")
print(f"🔹 Consultas futuras: {futuras}")
print(f"🔹 Consultas nos últimos 30 dias: {ultimos_30}")
