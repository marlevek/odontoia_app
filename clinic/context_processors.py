# clinic/context_processors.py
from .utils.subscription import verificar_assinatura

def trial_status(request):
    """
    Adiciona variáveis de status de assinatura/trial no contexto global.
    Evita erros em páginas públicas (login, registrar etc).
    """
    if not request.user.is_authenticated:
        # Retorna valores neutros para templates públicos
        return {
            "trial": None,
            "trial_alerta": None,
            "trial_dias": None,
            "trial_ativo": False,
        }

    ativo, dias = verificar_assinatura(request.user)
    alerta = None

    if ativo and dias <= 3:
        alerta = f"⚠️ Seu teste gratuito expira em {dias} dia(s)."
    elif not ativo:
        alerta = "🚫 Seu teste gratuito expirou. Faça uma assinatura para continuar."

    return {
        "trial": {
            "ativo": ativo,
            "dias_restantes": dias,
            "expirada": not ativo,
        },
        "trial_alerta": alerta,
        "trial_dias": dias,
        "trial_ativo": ativo,
    }
