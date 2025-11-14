# clinic/context_processors.py
from .utils.subscription import verificar_assinatura
from .models import Assinatura
from django.utils import timezone


def trial_status(request):
    """
    Adiciona a assinatura/trial no contexto global:
    - trial.ativo
    - trial.dias_restantes
    - trial.expirada
    - trial.tipo  (trial / basico / profissional / premium)
    """
    if not request.user.is_authenticated:
        return {
            "trial": None,
            "trial_alerta": None,
            "trial_dias": None,
            "trial_ativo": False,
        }

    assinatura = Assinatura.objects.filter(user=request.user).first()

    if not assinatura:
        return {
            "trial": None,
            "trial_alerta": "Nenhuma assinatura encontrada.",
            "trial_dias": None,
            "trial_ativo": False,
        }

    # Ativo = flag ativa + não expirou pela data
    agora = timezone.now()
    ativo = assinatura.ativa and (not assinatura.fim_teste or assinatura.fim_teste >= agora)
    dias = assinatura.dias_restantes() if hasattr(assinatura, "dias_restantes") else 0

    alerta = None
    if assinatura.tipo == "trial":
        if ativo and dias <= 3:
            alerta = f"⚠️ Seu teste gratuito expira em {dias} dia(s)."
        elif not ativo:
            alerta = "🚫 Seu teste gratuito expirou. Faça uma assinatura para continuar."

    return {
        "trial": {
            "ativo": ativo,
            "dias_restantes": dias,
            "expirada": not ativo,
            "tipo": assinatura.tipo,   # 👈 AGORA TEM TIPO
        },
        "trial_alerta": alerta,
        "trial_dias": dias,
        "trial_ativo": ativo,
    }
