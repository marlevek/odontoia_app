# clinic/context_processors.py
from .utils.subscription import verificar_assinatura
from .models import Assinatura

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

    # ✅ Já calcula se está ativo e quantos dias faltam
    ativo, dias = verificar_assinatura(request.user)

    # ✅ Descobre a assinatura do usuário (para pegar o tipo/plano)
    assinatura = Assinatura.objects.filter(user=request.user).first()
    tipo = assinatura.tipo if assinatura else "trial"  # fallback seguro

    alerta = None
    if ativo and dias <= 3:
        alerta = f"⚠️ Seu teste gratuito expira em {dias} dia(s)."
    elif not ativo:
        alerta = "🚫 Seu teste gratuito expirou. Faça uma assinatura para continuar."

    # 🔥 Agora trial tem também "tipo"
    return {
        "trial": {
            "ativo": ativo,
            "dias_restantes": dias,
            "expirada": not ativo,
            "tipo": tipo,          # 👈 AQUI que o menu vai usar
        },
        "trial_alerta": alerta,
        "trial_dias": dias,
        "trial_ativo": ativo,
    }