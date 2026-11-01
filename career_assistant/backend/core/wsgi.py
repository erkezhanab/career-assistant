"""
Точка входа WSGI — через неё веб-сервер запускает приложение.

WSGI (Web Server Gateway Interface) — стандарт связи между
веб-сервером (Gunicorn, uWSGI) и Python-приложением.

При разработке используется python manage.py runserver,
а на реальном сервере запускается именно этот файл.
"""

import os
from django.core.wsgi import get_wsgi_application

# Указываем Django, где искать настройки проекта.
# setdefault, а не прямое присваивание: если переменная уже задана
# в окружении сервера, её значение не будет перезаписано
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Объект, к которому обращается веб-сервер при каждом запросе
application = get_wsgi_application()
