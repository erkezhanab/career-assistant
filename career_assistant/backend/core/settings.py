"""
Настройки Django-проекта Career Assistant.

Единый файл конфигурации: подключённые приложения, база данных,
способ аутентификации, права доступа к API, работа с файлами
и ключи внешних сервисов.

Секретные данные (пароли, ключи API) сюда не записываются —
они читаются из файла .env, который не попадает в репозиторий.
"""

import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# Читает файл .env и помещает его содержимое в переменные окружения,
# после чего их можно получить через os.getenv()
load_dotenv()

# Абсолютный путь к папке backend. Используется, чтобы строить пути
# к файлам независимо от того, откуда запущен проект
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ — им подписываются сессии и JWT-токены.
# В рабочей системе обязан браться из .env, значение по умолчанию только для разработки
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Режим отладки: показывает подробные страницы ошибок.
# На реальном сервере должен быть False — иначе видны внутренние данные проекта
DEBUG = True

# Адреса, с которых разрешено принимать запросы (защита от подмены Host-заголовка)
ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'backend']

INSTALLED_APPS = [
    # Встроенные приложения Django
    'django.contrib.admin',          # админ-панель
    'django.contrib.auth',           # система пользователей и прав
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party
    'rest_framework',                # построение REST API
    'rest_framework_simplejwt',      # JWT-токены для входа
    'corsheaders',                   # разрешение запросов с другого домена (React)
    'django_filters',                # фильтрация в списках API

    # Local apps — модули самого проекта, по одному на функцию
    'users',         # пользователи и аутентификация
    'resumes',       # резюме и их анализ
    'vacancies',     # поиск вакансий
    'interviews',    # пробные собеседования
    'applications',  # отклики и сопроводительные письма
    'testing',       # тестирование знаний и сертификаты
]

# Middleware — цепочка обработчиков, через которую проходит каждый запрос.
# Порядок важен: они выполняются сверху вниз
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # CORS обязан стоять как можно выше, до CommonMiddleware,
    # иначе браузер заблокирует запросы с React-приложения
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Файл с главными маршрутами проекта
ROOT_URLCONF = 'core.urls'

# Шаблоны HTML. В этом проекте почти не используются:
# интерфейс рисует React, Django отдаёт только JSON и админку
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'core.wsgi.application'

# Database
# PostgreSQL выбран вместо SQLite из-за поддержки JSONField
# и способности выдерживать одновременную работу многих пользователей.
# Данные для подключения читаются из .env
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'career_assistant'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', '1234'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

# JWT
# Настройки токенов аутентификации
SIMPLE_JWT = {
    # Короткий срок жизни access-токена: если его перехватят,
    # он быстро перестанет действовать
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    # Refresh-токен живёт дольше — по нему обновляют access без повторного входа
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    # При каждом обновлении выдаётся новый refresh-токен
    'ROTATE_REFRESH_TOKENS': True,
    # Старый refresh-токен сразу становится недействительным
    'BLACKLIST_AFTER_ROTATION': True,
}

# REST Framework
REST_FRAMEWORK = {
    # Пользователь определяется по JWT-токену в заголовке Authorization
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Правило по умолчанию: все эндпоинты требуют авторизации.
    # Исключения (регистрация, вход) помечаются AllowAny в самих views.
    # Такой подход безопаснее: забыть закрыть эндпоинт невозможно
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
}

# CORS
# Браузер по умолчанию запрещает запросы между разными портами.
# Здесь явно разрешаем обращения с React-приложения (порт 3000)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_CREDENTIALS = True

# Media files
# Файлы, загруженные пользователями (резюме, сертификаты)
MEDIA_URL = '/media/'                          # адрес для доступа из браузера
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')   # папка на диске

# Claude (Anthropic) API
# Основной ИИ-сервис. Если ключ не задан, ClaudeService
# переходит в демо-режим с заранее подготовленными ответами
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# HeadHunter API
# Адрес внешнего сервиса вакансий (используется в HeadHunterService)
HH_API_URL = 'https://api.hh.ru/vacancies'

# File upload settings
# Ограничения загрузки: защита от переполнения диска
# и от загрузки исполняемых файлов вместо резюме
MAX_UPLOAD_SIZE = 10485760  # 10MB
ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx']

# Требования к паролю при регистрации
AUTH_PASSWORD_VALIDATORS = [
    {
        # Минимальная длина пароля
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        # Запрещает пароли, состоящие только из цифр
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-ru'          # язык интерфейса админки и сообщений об ошибках
TIME_ZONE = 'Europe/Moscow'      # часовой пояс для дат
USE_I18N = True                  # поддержка перевода
USE_TZ = True                    # даты хранятся в UTC — корректно для разных поясов

STATIC_URL = 'static/'

# Тип первичного ключа по умолчанию: BigAutoField вмещает
# больше записей, чем обычный AutoField
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Главная настройка кастомного пользователя: говорит Django
# использовать нашу модель users.User (вход по email) вместо встроенной
AUTH_USER_MODEL = 'users.User'
