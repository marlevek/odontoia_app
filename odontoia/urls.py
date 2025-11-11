from django.contrib import admin
from django.urls import path, include, reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views, logout



def admin_logout_redirect(request):
    """
    Encerra sessão do painel admin e redireciona
    para o login do OdontoIA (sem ir ao dashboard).
    """
    # 🔒 Encerra a sessão manualmente
    logout(request)

    # 💬 Mostra mensagem amigável
    messages.info(request, "Sessão do painel administrativo encerrada com sucesso.")

    # 🔁 Redireciona para o login do app
    return redirect("clinic:login")


urlpatterns = [
    path("admin/logout/", admin_logout_redirect, name="admin_logout_redirect"),  # ✅ intercepta logout
    path("admin/", admin.site.urls),
    path("", include("clinic.urls", namespace="clinic")),


    # Login e Logout
    path('login/', auth_views.LoginView.as_view(
        template_name='clinic/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)



