import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Diretório base
BASE_DIR = Path(__file__).resolve().parent.parent

# Segurança
SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

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
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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
            ],
        },
    },
]

WSGI_APPLICATION = 'odontoia.wsgi.application'

# Banco de dados
DATABASES = {
    'default': {
        'ENGINE': os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        'NAME': os.getenv("DB_NAME", BASE_DIR / "db.sqlite3"),
        'USER': os.getenv("DB_USER", ""),
        'PASSWORD': os.getenv("DB_PASSWORD", ""),
        'HOST': os.getenv("DB_HOST", ""),
        'PORT': os.getenv("DB_PORT", ""),
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

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

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
SESSION_COOKIE_SECURE = False  # mude para True em produção (HTTPS)
CSRF_COOKIE_SECURE = False     # idem

# Previne carregamento de conteúdo inseguro em HTTPS
SECURE_SSL_REDIRECT = False    # True em produção (redireciona http → https)
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


