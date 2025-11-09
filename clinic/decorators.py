from django.shortcuts import redirect
from django.contrib import messages
from .utils.subscription import get_trial_info

def require_active_subscription(view_func):
    """
    Bloqueia acesso de usuários cujo período de teste expirou
    """
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        info = get_trial_info(request.user)
        if info["status"] == "expired":
            messages.error(request, "Seu período de teste expirou. Ative sua assinatura para continuar.")
            return redirect("assinatura_expirada")
        return view_func(request, *args, **kwargs)
    return _wrapped
