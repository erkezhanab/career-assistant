from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/resumes/', include('resumes.urls')),
    path('api/vacancies/', include('vacancies.urls')),
    path('api/applications/', include('applications.urls')),
    path('api/interviews/', include('interviews.urls')),
    path('api/testing/', include('testing.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)