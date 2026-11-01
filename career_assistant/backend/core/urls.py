"""
Главный маршрутизатор проекта (точка входа всех HTTP-запросов).

Django по этому файлу определяет, какому приложению отдать запрос.
Каждое приложение имеет свой префикс и свой файл urls.py —
такое разделение позволяет развивать модули независимо друг от друга.

Указан в settings.py как ROOT_URLCONF = 'core.urls'.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Встроенная админ-панель Django: просмотр и правка всех таблиц БД
    path('admin/', admin.site.urls),

    # include() передаёт обработку дальше, в urls.py конкретного приложения.
    # Итоговый адрес = префикс здесь + путь внутри приложения,
    # например 'api/auth/' + 'login/' = /api/auth/login/
    path('api/auth/', include('users.urls')),                 # регистрация, вход, профиль
    path('api/resumes/', include('resumes.urls')),             # загрузка и анализ резюме
    path('api/vacancies/', include('vacancies.urls')),         # поиск вакансий
    path('api/applications/', include('applications.urls')),   # отклики и письма
    path('api/interviews/', include('interviews.urls')),       # пробные собеседования
    path('api/testing/', include('testing.urls')),             # тесты и сертификаты
]

# Раздача загруженных файлов (резюме, сертификатов) силами Django.
# Только при DEBUG=True: в реальной эксплуатации файлы должен отдавать
# веб-сервер (nginx), так как Django делает это медленно и небезопасно.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
