import os
from pathlib import Path
from dotenv import load_dotenv


# ⚙️ Carrega .env manualmente com caminho absoluto (garante que funcione)
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False").strip().lower() == "true"

ALLOWED_HOSTS = [
    'app.odontoia.codertec.com.br',
    'odontoia.codertec.com.br',
    '*.up.railway.app',
    'localhost',
    '127.0.0.1'
]

# Confiança no proxy (Railway) para HTTPS
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Redirecionar para HTTPS em produção
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() == "true"


# Aplicativos instalados
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Seus apps
    'clinic',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'clinic.middleware.TrialMiddleware',
]

# URLs
ROOT_URLCONF = 'odontoia.urls'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],  # se quiser usar templates globais
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "clinic.context_processors.trial_status",
                'clinic.context_processors.clinica_config', 
            ],
        },
    },
]

WSGI_APPLICATION = 'odontoia.wsgi.application'

# Banco de dados
if os.getenv("PGHOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("PGDATABASE", "railway"),
            "USER": os.getenv("PGUSER", "postgres"),
            "PASSWORD": os.getenv("PGPASSWORD", ""),
            "HOST": os.getenv("PGHOST", ""),
            "PORT": os.getenv("PGPORT", "5432"),
        }
    }
else:
    # fallback local (ex.: sqlite) – mantenha como estava
    DATABASES = {
        "default": {
            "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
            "NAME": os.getenv("DB_NAME", os.path.join(BASE_DIR, "db.sqlite3")),
            "USER": os.getenv("DB_USER", ""),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", ""),
            "PORT": os.getenv("DB_PORT", ""),
        }
    }

# Validações de senha
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Idioma e fuso horário
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Arquivos estáticos
STATIC_URL = '/static/'

STATICFILES_DIRS = [BASE_DIR / "static"]

STATIC_ROOT = BASE_DIR / "staticfiles"

# Uploads
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# Padrão do campo automático
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================
# ⚙️ CONFIGURAÇÕES DE SESSÃO
# ============================

# Expira a sessão ao fechar o navegador (evita logins persistentes em PCs públicos)
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Duração máxima da sessão (em segundos) – ex: 3 horas
SESSION_COOKIE_AGE = 10800  # 3 * 60 * 60

# Evita cookies acessíveis por JavaScript (protege contra XSS)
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True

# ============================
# 🔐 SEGURANÇA EM PRODUÇÃO
# ============================

# Define o domínio dos cookies (ajuste quando subir para servidor real)
# Exemplo: 'odontoia.com.br'  → REMOVA o '#' quando tiver domínio real
# SESSION_COOKIE_DOMAIN = "odontoia.com.br"
# CSRF_COOKIE_DOMAIN = "odontoia.com.br"

# Garante que cookies de sessão e CSRF só sejam enviados por HTTPS
# (em localhost, mantenha False até ativar HTTPS no servidor)
SESSION_COOKIE_SECURE = not DEBUG  
CSRF_COOKIE_SECURE = not DEBUG     


#CSRF p/ domínios
CSRF_TRUSTED_ORIGINS = [
    'https://app.odontoia.codertec.com.br',
    "https://odontoia.codertec.com.br",
    'https://*.up.railway.app',
]

# Previne carregamento de conteúdo inseguro em HTTPS
#SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False").lower() == "true"    # True em produção (redireciona http → https)
SECURE_HSTS_SECONDS = 31536000  # 1 ano (ativa HSTS)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Evita sequestro de clique (clickjacking)
X_FRAME_OPTIONS = 'DENY'

# ============================
# 🧠 AUTENTICAÇÃO
# ============================

# Redirecionamentos padrão do login/logout
LOGIN_URL = 'clinic:login'
LOGOUT_REDIRECT_URL = 'clinic:login'
LOGIN_REDIRECT_URL = 'clinic:dashboard'

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# ============================
# 📧 CONFIGURAÇÃO DE E-MAIL
# ============================

from django.core.exceptions import ImproperlyConfigured

def get_env_var(key, default=None, required=False):
    """Lê variáveis do .env de forma segura"""
    value = os.getenv(key, default)
    if required and not value:
        raise ImproperlyConfigured(f"A variável de ambiente {key} é obrigatória e não foi definida.")
    return value


# 🔐 Configurações principais email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = get_env_var("EMAIL_HOST", "mail.codertec.com.br")
EMAIL_PORT = int(get_env_var("EMAIL_PORT", "587"))
EMAIL_USE_TLS = get_env_var("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_USE_SSL = get_env_var("EMAIL_USE_SSL", "False").lower() == "true"
EMAIL_HOST_USER = get_env_var("EMAIL_HOST_USER", required=True)
EMAIL_HOST_PASSWORD = get_env_var("EMAIL_HOST_PASSWORD", required=True)
DEFAULT_FROM_EMAIL = get_env_var("DEFAULT_FROM_EMAIL", f"OdontoIA <{EMAIL_HOST_USER}>")


# 🧩 Fallback seguro (para desenvolvimento)
# Se DEBUG=True → imprime e-mails no console (não envia de verdade)
if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    print("⚙️ Modo DEBUG ativo → e-mails serão exibidos no console, não enviados.")
else:
    print(f"📨 E-mails reais ativados → usando {EMAIL_HOST}:{EMAIL_PORT}")


# ======= MERCADO PAGO / PAGAMENTOS =======
MERCADOPAGO_PUBLIC_KEY = os.getenv("MERCADOPAGO_PUBLIC_KEY")
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
CURRENCY_ID = os.getenv("CURRENCY_ID", "BRL")

# Em dev mostramos o e-mail no console (já está configurado no seu projeto)
# Em prod (Railway), basta definir EMAIL_* no .env que já funciona.

# Para montar URLs absolutas quando necessário (fallback)
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "").rstrip("/")
# Se vazio, nas views usaremos request.build_absolute_uri(), que é preferível.
