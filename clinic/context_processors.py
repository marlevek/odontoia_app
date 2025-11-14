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
            "assinatura": None,
            "trial_alerta": None,
            "trial_dias": None,
            "trial_ativo": False,
        }

    ativo, dias = verificar_assinatura(request.user)
    
    assinatura = Assinatura.objects.filter(user=request.user).first()

    alerta = None
    if ativo and dias <= 3:
        alerta = f"⚠️ Seu plano expira em {dias} dia(s)."
    elif not ativo:
        alerta = "🚫 Sua assinatura expirou. Renove para continuar."
    
    

    return {
        "assinatura": assinatura,
        "trial_alerta": alerta,
        "trial_dias": dias,
        "trial_ativo": ativo,
      
    }
