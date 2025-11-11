# clinic/utils/subscription.py
from django.utils import timezone
from datetime import timedelta
from ..models import Assinatura

def get_trial_info(user):
    """
    Retorna informações sobre o teste (trial) do usuário.
    """
    try:
        assinatura = Assinatura.objects.get(user=user)
    except Assinatura.DoesNotExist:
        return {
            "existe": False,
            "ativa": False,
            "expirada": True,
            "dias_restantes": 0,
            "fim_teste": None,
        }

    hoje = timezone.now().date()
    fim_teste = assinatura.fim_teste.date() if assinatura.fim_teste else None

    if fim_teste and hoje > fim_teste:
        expirada = True
        dias_restantes = 0
    else:
        expirada = False
        dias_restantes = (fim_teste - hoje).days if fim_teste else 0

    return {
        "existe": True,
        "ativa": not expirada,
        "expirada": expirada,
        "dias_restantes": dias_restantes,
        "fim_teste": assinatura.fim_teste,
    }


def verificar_assinatura(user):
    """
    Retorna (ativa: bool, dias_restantes: int)
    Compatível com o que o middleware/decorators usam.
    """
    info = get_trial_info(user)
    if not info:
        return (False, 0)
    return (info["ativa"], info["dias_restantes"])
