"""
Сериализаторы приложения users.

Сериализатор — «переводчик» между JSON (который присылает React)
и объектами моделей Django. Он же проверяет корректность данных.

  - UserRegistrationSerializer  — регистрация с подтверждением пароля
  - UserProfileSerializer       — просмотр и правка профиля
  - UserProfileDetailSerializer — расширенные данные (для админки)
  - ChangePasswordSerializer    — смена пароля
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Проверка и создание нового пользователя."""

    # write_only=True — пароль принимается от клиента, но НИКОГДА
    # не возвращается в ответе (иначе он утёк бы в ответе сервера).
    # validate_password проверяет пароль по правилам из settings.py
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    # Второе поле для подтверждения: защита от опечатки при вводе
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        # Поля, которые пользователь может заполнить при регистрации.
        # Служебные (is_staff, is_superuser) отсутствуют намеренно —
        # иначе можно было бы зарегистрироваться администратором
        fields = ('email', 'password', 'password2', 'first_name', 'last_name', 'phone', 'specialization')

    def validate(self, attrs):
        """
        Проверка, затрагивающая несколько полей сразу.

        validate() для всей записи, validate_<поле>() — для одного поля.
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords don't match"})
        return attrs

    def create(self, validated_data):
        """Создаёт пользователя и его профиль настроек."""
        # Убираем подтверждение пароля: в модели User такого поля нет
        validated_data.pop('password2')
        # create_user (а не objects.create) — чтобы пароль был захеширован
        user = User.objects.create_user(**validated_data)
        # Профиль создаётся сразу, чтобы страница настроек
        # работала с первого входа
        UserProfile.objects.create(user=user)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Профиль пользователя: личные данные + настройки уведомлений.

    Данные лежат в двух таблицах (User и UserProfile), но для фронтенда
    они собираются в один плоский объект через параметр source.
    """

    # source='user.email' — значение берётся из связанной модели User.
    # Email только для чтения: он является логином и меняться не должен
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    phone = serializers.CharField(source='user.phone')
    specialization = serializers.CharField(source='user.specialization')

    class Meta:
        model = UserProfile
        fields = ('email', 'first_name', 'last_name', 'phone', 'specialization',
                  'notifications_enabled', 'search_frequency', 'email_notifications')

    def update(self, instance, validated_data):
        """
        Сохранение изменений в две таблицы.

        Метод написан вручную, так как по умолчанию DRF не умеет
        обновлять поля связанной модели (User) через вложенный source.
        """
        # Отделяем данные пользователя от данных профиля
        user_data = validated_data.pop('user', {})
        user = instance.user

        # setattr присваивает значение полю по его имени
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()

        # Остальные поля относятся к самому профилю
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance


class UserProfileDetailSerializer(serializers.ModelSerializer):
    """
    Расширенный профиль с данными аккаунта.

    Используется там, где нужны служебные поля (права, дата регистрации),
    например в административном разделе.
    """

    # SerializerMethodField — поле, значение которого вычисляется
    # методом get_<имя поля>
    user = serializers.SerializerMethodField()

    class Meta:
        model = UserProfile
        fields = '__all__'   # все поля модели

    def get_user(self, obj):
        """Собирает данные пользователя в отдельный вложенный объект."""
        return {
            'id': obj.user.id,
            'email': obj.user.email,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'is_superuser': obj.user.is_superuser,
            'is_active': obj.user.is_active,
            'date_joined': obj.user.date_joined,
            'last_login': obj.user.last_login
        }


class ChangePasswordSerializer(serializers.Serializer):
    """
    Смена пароля.

    Наследуется от Serializer (а не ModelSerializer), потому что
    эти поля не хранятся в базе — они нужны только для проверки запроса.
    """

    old_password = serializers.CharField(required=True)
    # Новый пароль проходит те же проверки надёжности, что и при регистрации
    new_password = serializers.CharField(required=True, validators=[validate_password])
