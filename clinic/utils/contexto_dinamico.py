# clinic/utils/contexto_dinamico.py
from django.utils import timezone
from clinic.models import Paciente, Consulta
from django.db.models import Sum
from datetime import timedelta

def gerar_contexto_dinamico(user):
    """Coleta dados financeiros e operacionais da clínica do usuário."""
    hoje = timezone.now().date()
    inicio_mes = hoje.replace(day=1)

    total_pacientes = Paciente.objects.count()
    consultas_mes = Consulta.objects.filter(data__date__gte=inicio_mes)
    total_consultas = consultas_mes.count()
    faturamento_mes = consultas_mes.aggregate(Sum('valor_final'))['valor_final__sum'] or 0
    comissoes_mes = consultas_mes.aggregate(Sum('comissao_valor'))['comissao_valor__sum'] or 0
    faturamento_liquido = faturamento_mes - comissoes_mes

    return (
        f"Contexto atualizado do OdontoIA:\n"
        f"- Total de pacientes: {total_pacientes}\n"
        f"- Consultas neste mês: {total_consultas}\n"
        f"- Faturamento bruto: R${faturamento_mes:,.2f}\n"
        f"- Comissões: R${comissoes_mes:,.2f}\n"
        f"- Faturamento líquido: R${faturamento_liquido:,.2f}\n"
        f"(Data: {hoje.strftime('%d/%m/%Y')})"
    )
