from django.shortcuts import redirect
from django.conf import settings
from .utils.subscription import verificar_assinatura

def require_active_subscription(view_func):
    def wrapper(request, *args, **kwargs):
        # 🚀 Em modo DEBUG, ignora verificação
        if getattr(settings, "DEBUG", False):
            return view_func(request, *args, **kwargs)

        # 🔒 Em produção, verifica assinatura normalmente
        ativo, _ = verificar_assinatura(request.user)
        if not ativo:
            return redirect('clinic:assinatura_expirada')

        return view_func(request, *args, **kwargs)
    return wrapper

   