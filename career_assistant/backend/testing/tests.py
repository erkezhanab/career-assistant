"""
Автоматические тесты приложения testing.

Файл создан Django автоматически и пока не заполнен — написание
автотестов указано в плане развития проекта (README, раздел Roadmap).

Что имеет смысл покрыть тестами в первую очередь:
  - TestSession.calculate_score()  — подсчёт баллов для всех трёх
    типов вопросов (одиночный, множественный выбор, открытый)
  - TestSession.can_start_test()   — запрет пересдачи раньше срока
  - StartTestView                  — запрет двух активных тестов сразу

Запуск тестов: python manage.py test
"""

from django.test import TestCase

# Create your tests here.
