"""
Конфигурация приложения testing.

Django создаёт такой файл для каждого приложения; здесь задаются
его имя и настройки по умолчанию.
"""

from django.apps import AppConfig


class TestingConfig(AppConfig):
    """Настройки приложения тестирования."""

    # Тип первичного ключа для моделей этого приложения.
    # BigAutoField вмещает больше записей, чем обычный AutoField
    default_auto_field = 'django.db.models.BigAutoField'

    # Имя приложения — должно совпадать с названием папки
    # и со строкой в INSTALLED_APPS
    name = 'testing'
