"""
Представления (views) приложения users — регистрация, вход и профиль.

Отвечает за аутентификацию по JWT-токенам:
  - RegisterView       — регистрация нового пользователя
  - LoginView          — вход по email и паролю
  - UserProfileView    — настройки уведомлений
  - ChangePasswordView — смена пароля
  - UserInfoView       — данные текущего пользователя для интерфейса

Как работает JWT: сервер не хранит сессии. При входе выдаются два токена —
access (короткоживущий, прикладывается к каждому запросу) и refresh
(долгоживущий, нужен для получения нового access без повторного входа).
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer
)
from .models import UserProfile


class RegisterView(generics.CreateAPIView):
    """
    Регистрация нового пользователя.  POST /api/auth/register/

    После успешного создания аккаунта сразу выдаёт токены,
    чтобы пользователю не нужно было отдельно входить в систему.
    """

    serializer_class = UserRegistrationSerializer
    # AllowAny — регистрация должна быть доступна без авторизации
    # (по умолчанию в settings.py стоит IsAuthenticated, поэтому разрешаем явно)
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        """Проверяет данные, создаёт пользователя и возвращает токены."""
        serializer = self.get_serializer(data=request.data)
        # raise_exception=True — при некорректных данных DRF сам вернёт
        # ответ 400 со списком ошибок по каждому полю
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Генерируем пару токенов для нового пользователя
        refresh = RefreshToken.for_user(user)

        return Response({
            'user': {
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            },
            'refresh': str(refresh),
            # access_token создаётся на основе refresh-токена
            'access': str(refresh.access_token)
        }, status=status.HTTP_201_CREATED)  # 201 = ресурс создан


class LoginView(APIView):
    """Вход в систему.  POST /api/auth/login/"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        # authenticate() сам сверяет пароль с хешем из базы.
        # Проверять пароль вручную нельзя — в БД он хранится только в виде хеша
        user = authenticate(email=email, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            })

        # Намеренно общий текст ошибки: не сообщаем, что именно неверно —
        # email или пароль, чтобы нельзя было подобрать существующие адреса
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED  # 401 = не авторизован
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Просмотр и изменение настроек уведомлений.
    GET/PUT/PATCH /api/auth/profile/
    """

    serializer_class = UserProfileSerializer
    # Только для авторизованных: чужой профиль открыть нельзя,
    # так как объект берётся из токена текущего пользователя
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Получаем или создаем профиль, если его нет
        user = self.request.user
        # get_or_create защищает от ошибки 404 у пользователей,
        # зарегистрированных до появления модели UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)
        return profile


class ChangePasswordView(generics.UpdateAPIView):
    """Смена пароля.  PUT /api/auth/change-password/"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        # Обязательная проверка старого пароля: иначе при краже токена
        # злоумышленник сменил бы пароль и забрал аккаунт себе
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'old_password': ['Wrong password.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        # set_password хеширует новый пароль перед сохранением
        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({'message': 'Password updated successfully'})


class UserInfoView(APIView):
    """
    Полная информация о текущем пользователе.  GET /api/auth/user-info/

    Используется фронтендом после входа: по полям is_staff/is_superuser
    интерфейс решает, показывать ли раздел администратора.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # request.user подставляется автоматически из JWT-токена в заголовке
        user = request.user

        # Получаем профиль, если он существует
        try:
            profile = user.profile
            profile_data = {
                'notifications_enabled': profile.notifications_enabled,
                'search_frequency': profile.search_frequency,
                'email_notifications': profile.email_notifications,
            }
        except UserProfile.DoesNotExist:
            # Профиля нет — отдаём пустой словарь вместо ошибки,
            # чтобы страница профиля всё равно открылась
            profile_data = {}

        return Response({
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'specialization': user.specialization,
            # Флаги прав: по ним фронтенд скрывает/показывает админ-панель
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff,
            'is_active': user.is_active,
            'date_joined': user.date_joined,
            'last_login': user.last_login,
            'profile': profile_data
        })
