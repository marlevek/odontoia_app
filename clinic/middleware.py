# clinic/middleware.py
import os
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from .utils.subscription import verificar_assinatura


class TrialMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Middleware que bloqueia usuários com assinatura expirada.
        ✅ Mesmo em DEBUG=True, impede alterações (POST).
        """

        debug_env = os.getenv("DEBUG", "False").strip().lower() == "true"
        debug_setting = getattr(settings, "DEBUG", False)
        print(f"🧩 TrialMiddleware → DEBUG(env)={debug_env}, DEBUG(settings)={debug_setting}, path={request.path}")

        if request.user.is_authenticated:
            ativo, dias = verificar_assinatura(request.user)

            # Rotas sempre liberadas
            rotas_livres = [
                reverse("clinic:assinatura_expirada"),
                reverse("clinic:logout"),
                reverse("clinic:registrar_teste"),
                reverse("clinic:login"),
                "/api/chat/",
                "/api/chat/diag/",
                "/static/",
                "/media/",
            ]

            # ⚠️ Se a assinatura expirou:
            if not ativo:
                # Bloqueia qualquer tentativa de gravação (POST, PUT, DELETE)
                if request.method in ("POST", "PUT", "DELETE"):
                    print("🚫 Tentativa de modificação bloqueada: assinatura expirada")
                    return redirect("clinic:assinatura_expirada")

                # Bloqueia navegação em rotas críticas (cadastro, edição, etc.)
                rotas_restritas = [
                    "/novo", "/editar", "/excluir", "/create", "/update"
                ]
                if any(r in request.path for r in rotas_restritas):
                    print("🚫 Acesso restrito bloqueado (assinatura expirada)")
                    return redirect("clinic:assinatura_expirada")

                # Permite apenas visualização de listagens e páginas livres
                if not any(request.path.startswith(r) for r in rotas_livres):
                    print("⚠️ Redirecionando para aviso de assinatura expirada")
                    return redirect("clinic:assinatura_expirada")

        return self.get_response(request)
