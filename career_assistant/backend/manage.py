#!/usr/bin/env python
"""
Утилита командной строки Django — точка входа для всех команд проекта.

Через этот файл запускаются:
  python manage.py runserver        — запуск сервера разработки
  python manage.py migrate          — применение миграций к базе
  python manage.py makemigrations   — создание новых миграций
  python manage.py createsuperuser  — создание администратора
  python manage.py seed_demo_data   — заполнение базы тестовыми данными

Файл создаётся Django автоматически и обычно не изменяется.
"""

import os
import sys


def main():
    """Run administrative tasks."""
    # Указываем, где лежат настройки проекта.
    # Без этой строки Django не знает, какую базу и какие
    # приложения использовать
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Понятное сообщение вместо технической ошибки импорта:
        # чаще всего причина — не активировано виртуальное окружение
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    # sys.argv — аргументы командной строки: имя команды и её параметры
    execute_from_command_line(sys.argv)


# Блок выполняется только при прямом запуске файла
if __name__ == '__main__':
    main()
