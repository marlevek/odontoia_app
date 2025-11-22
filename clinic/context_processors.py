# clinic/context_processors.py
from .utils.subscription import verificar_assinatura
from .models import Assinatura, ClinicaConfig
from django.utils import timezone



def trial_status(request):
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
        "assinatura": assinatura,   # 👈 ESSENCIAL
        "trial_alerta": alerta,
        "trial_dias": dias,
        "trial_ativo": ativo,
    }


def clinica_config(request):
    if not request.user.is_authenticated:
        return {}
    
    config = ClinicaConfig.objects.filter(owner=request.user).first()
    
    return {
        "clinica_config": config
    }