"""
Модели приложения users — пользователи системы и их настройки.

Ответственность модуля:
  - User        — кастомная модель пользователя (вход по email вместо username)
  - UserManager — менеджер, который умеет создавать обычных пользователей и админов
  - UserProfile — дополнительные настройки уведомлений (связь 1:1 с User)
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """
    Менеджер создания пользователей.

    Нужен потому, что стандартный Django-менеджер требует username,
    а в нашей системе username удалён и логином служит email.
    """

    def create_user(self, email, password=None, **extra_fields):
        """Создаёт обычного пользователя. Email обязателен — это логин."""
        if not email:
            raise ValueError('Email is required')
        # normalize_email приводит домен к нижнему регистру (Mail.RU -> mail.ru),
        # чтобы один и тот же адрес нельзя было зарегистрировать дважды
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        # set_password хеширует пароль, в БД никогда не попадает открытый текст
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создаёт администратора (доступ в Django admin + админские API)."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Пользователь системы (соискатель или администратор).

    Наследуется от AbstractUser, чтобы переиспользовать готовую систему
    паролей и прав Django, но с заменой логина username -> email.
    Подключается в settings.py через AUTH_USER_MODEL = 'users.User'.
    """

    # username убран: вход в систему выполняется по email
    username = None

    # unique=True — на уровне БД гарантирует, что два аккаунта
    # с одинаковым email создать невозможно
    email = models.EmailField(_('email address'), unique=True)

    phone = models.CharField(max_length=20, blank=True, null=True)

    # Специализация ("Python Developer") — передаётся ИИ при анализе резюме,
    # чтобы оценка была под конкретную профессию
    specialization = models.CharField(max_length=255, blank=True, null=True)

    is_active = models.BooleanField(default=True)       # False = аккаунт заблокирован
    is_staff = models.BooleanField(default=False)       # доступ в /admin
    is_superuser = models.BooleanField(default=False)   # все права без ограничений

    # auto_now_add — дата проставляется автоматически при создании записи
    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)

    # Django использует эти два поля, чтобы понять, что логин — это email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # Подключаем свой менеджер (User.objects.create_user(...))
    objects = UserManager()

    def __str__(self):
        """Как объект отображается в админке и логах."""
        return self.email


class UserProfile(models.Model):
    """
    Настройки уведомлений пользователя.

    Вынесены в отдельную модель, а не в User, чтобы не раздувать
    основную таблицу аккаунтов настройками интерфейса.
    """

    # OneToOneField — у одного пользователя ровно один профиль.
    # on_delete=CASCADE — при удалении пользователя профиль удаляется автоматически.
    # related_name='profile' — обращение из кода: user.profile
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    notifications_enabled = models.BooleanField(default=True)

    # Как часто присылать подборку вакансий
    search_frequency = models.CharField(
        max_length=20,
        choices=[
            ('daily', 'Ежедневно'),
            ('weekly', 'Еженедельно'),
            ('monthly', 'Ежемесячно'),
        ],
        default='daily'
    )

    email_notifications = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)  # ставится один раз при создании
    updated_at = models.DateTimeField(auto_now=True)      # обновляется при каждом save()

    def __str__(self):
        return f"Profile of {self.user.email}"
