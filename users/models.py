import re, logging
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

logger = logging.getLogger('users')

def validate_phone(value):
    if not re.match(r'^\+375 \((29|33|44|25)\) \d{3}-\d{2}-\d{2}$', value):
        raise ValidationError('Формат: +375 (29) XXX-XX-XX')

def validate_age_18(value):
    today = timezone.now().date()
    if (today - value).days // 365 < 18:
        raise ValidationError('Возраст должен быть не менее 18 лет.')

class CustomUser(AbstractUser):
    ROLE_ADMIN = 'admin'; ROLE_EMPLOYEE = 'employee'; ROLE_CLIENT = 'client'
    ROLE_CHOICES = [('admin','Администратор'),('employee','Сотрудник'),('client','Покупатель')]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client', verbose_name='Роль')
    phone = models.CharField(max_length=20, blank=True, null=True, validators=[validate_phone], verbose_name='Телефон')
    birth_date = models.DateField(blank=True, null=True, validators=[validate_age_18], verbose_name='Дата рождения')
    address = models.CharField(max_length=255, blank=True, verbose_name='Адрес')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='Фото')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.get_full_name() or self.username} ({self.get_role_display()})'

    def is_employee(self): return self.role == 'employee'
    def is_client(self): return self.role == 'client'
