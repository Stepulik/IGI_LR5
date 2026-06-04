import logging
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from users.models import CustomUser

logger = logging.getLogger('shop')


class ProductType(models.Model):
    """Вид изделия (торты, пирожные, конфеты и т.д.)"""
    name = models.CharField(max_length=100, verbose_name='Вид изделия')
    description = models.TextField(blank=True, verbose_name='Описание')
    image = models.ImageField(upload_to='types/', blank=True, null=True, verbose_name='Фото')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Вид изделия'
        verbose_name_plural = 'Виды изделий'
        ordering = ['name']

    def __str__(self):
        return self.name


class Employee(models.Model):
    """Сотрудник кондитерской"""
    POSITION_CHOICES = [
        ('baker', 'Кондитер'),
        ('manager', 'Менеджер'),
        ('courier', 'Курьер'),
        ('admin', 'Администратор'),
        ('cashier', 'Кассир'),
    ]
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE,
                                related_name='employee_profile', verbose_name='Пользователь')
    position = models.CharField(max_length=50, choices=POSITION_CHOICES, verbose_name='Должность')
    hire_date = models.DateField(verbose_name='Дата найма')
    salary = models.DecimalField(max_digits=10, decimal_places=2,
                                 validators=[MinValueValidator(0)], verbose_name='Зарплата (руб.)')
    photo = models.ImageField(upload_to='employees/', blank=True, null=True, verbose_name='Фото')
    bio = models.TextField(blank=True, verbose_name='О себе')
    is_active = models.BooleanField(default=True, verbose_name='Работает')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'

    def __str__(self):
        return f'{self.full_name} — {self.get_position_display()}'

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def phone(self):
        return self.user.phone

    @property
    def email(self):
        return self.user.email


class Product(models.Model):
    """Изделие (сладость)"""
    UNIT_CHOICES = [
        ('pcs', 'штук'),
        ('kg', 'кг'),
        ('g', 'г'),
        ('l', 'л'),
        ('box', 'коробка'),
    ]
    name = models.CharField(max_length=200, verbose_name='Название')
    product_type = models.ForeignKey(ProductType, on_delete=models.PROTECT,
                                     related_name='products', verbose_name='Вид изделия')
    description = models.TextField(blank=True, verbose_name='Описание')
    composition = models.TextField(blank=True, verbose_name='Состав')
    price = models.DecimalField(max_digits=10, decimal_places=2,
                                validators=[MinValueValidator(0)], verbose_name='Цена (руб.)')
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='pcs', verbose_name='Ед. изм.')
    weight = models.FloatField(blank=True, null=True, verbose_name='Вес (г)')
    calories = models.PositiveIntegerField(blank=True, null=True, verbose_name='Калорийность (ккал/100г)')
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Фото')
    is_available = models.BooleanField(default=True, verbose_name='В наличии')
    is_featured = models.BooleanField(default=False, verbose_name='Хит продаж')
    tags = models.ManyToManyField('ProductTag', blank=True,
                                   related_name='products', verbose_name='Теги')
    views_count = models.PositiveIntegerField(default=0, verbose_name='Просмотры')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Изделие'
        verbose_name_plural = 'Изделия'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.price} руб./{self.get_unit_display()})'


class ProductTag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='Тег')

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Customer(models.Model):
    """Клиент / Заказчик"""
    user = models.OneToOneField(CustomUser, on_delete=models.SET_NULL,
                                null=True, blank=True,
                                related_name='customer_profile', verbose_name='Аккаунт')
    first_name = models.CharField(max_length=100, verbose_name='Имя')
    last_name = models.CharField(max_length=100, verbose_name='Фамилия')
    middle_name = models.CharField(max_length=100, blank=True, verbose_name='Отчество')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(blank=True, verbose_name='Email')
    address = models.CharField(max_length=255, blank=True, verbose_name='Адрес доставки')
    city = models.CharField(max_length=100, default='Минск', verbose_name='Город')
    comment = models.TextField(blank=True, verbose_name='Примечание')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name} {self.middle_name}'.strip()

    @property
    def orders_count(self):
        return self.orders.count()

    @property
    def total_spent(self):
        from django.db.models import Sum
        result = self.orders.filter(status='delivered').aggregate(s=Sum('total_price'))
        return result['s'] or 0


class Order(models.Model):
    """Заказ"""
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('processing', 'В обработке'),
        ('ready', 'Готов'),
        ('delivering', 'Доставляется'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменён'),
    ]
    DELIVERY_CHOICES = [
        ('pickup', 'Самовывоз'),
        ('delivery', 'Доставка'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT,
                                  related_name='orders', verbose_name='Клиент')
    employee = models.ForeignKey(Employee, on_delete=models.SET_NULL,
                                  null=True, blank=True,
                                  related_name='orders', verbose_name='Менеджер')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                               default='new', verbose_name='Статус')
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES,
                                      default='pickup', verbose_name='Тип доставки')
    delivery_address = models.CharField(max_length=255, blank=True, verbose_name='Адрес доставки')
    delivery_cost = models.DecimalField(max_digits=8, decimal_places=2,
                                         default=0, verbose_name='Стоимость доставки (руб.)')
    promo_code = models.ForeignKey('PromoCode', on_delete=models.SET_NULL,
                                    null=True, blank=True, verbose_name='Промокод')
    discount_amount = models.DecimalField(max_digits=8, decimal_places=2,
                                           default=0, verbose_name='Скидка (руб.)')
    total_price = models.DecimalField(max_digits=12, decimal_places=2,
                                       default=0, verbose_name='Итого (руб.)')
    comment = models.TextField(blank=True, verbose_name='Комментарий')
    order_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата заказа')
    delivery_date = models.DateField(blank=True, null=True, verbose_name='Дата доставки')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-order_date']

    def __str__(self):
        return f'Заказ #{self.pk} — {self.customer} — {self.get_status_display()}'

    def calculate_total(self):
        items_sum = sum(item.subtotal for item in self.items.all())
        discount = self.discount_amount or 0
        delivery = self.delivery_cost or 0
        return items_sum - discount + delivery


class OrderItem(models.Model):
    """Позиция заказа"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE,
                               related_name='items', verbose_name='Заказ')
    product = models.ForeignKey(Product, on_delete=models.PROTECT,
                                 related_name='order_items', verbose_name='Изделие')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена на момент заказа')

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f'{self.product.name} x{self.quantity}'

    @property
    def subtotal(self):
        return self.price * self.quantity


class PickupPoint(models.Model):
    """Точка самовывоза"""
    name = models.CharField(max_length=200, verbose_name='Название')
    address = models.CharField(max_length=255, verbose_name='Адрес')
    city = models.CharField(max_length=100, default='Минск', verbose_name='Город')
    phone = models.CharField(max_length=20, blank=True, verbose_name='Телефон')
    working_hours = models.CharField(max_length=100, blank=True, verbose_name='Режим работы')
    is_active = models.BooleanField(default=True, verbose_name='Работает')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Точка самовывоза'
        verbose_name_plural = 'Точки самовывоза'

    def __str__(self):
        return f'{self.name} — {self.address}'


# ===== ОБЩИЕ СТРАНИЦЫ =====

class Article(models.Model):
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    summary = models.CharField(max_length=500, verbose_name='Краткое содержание')
    content = models.TextField(verbose_name='Полный текст')
    image = models.ImageField(upload_to='articles/', blank=True, null=True, verbose_name='Фото')
    is_published = models.BooleanField(default=True, verbose_name='Опубликовано')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CompanyInfo(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    founded_year = models.PositiveIntegerField(verbose_name='Год основания')
    address = models.CharField(max_length=255, verbose_name='Адрес')
    phone = models.CharField(max_length=20, verbose_name='Телефон')
    email = models.EmailField(verbose_name='Email')
    logo = models.ImageField(upload_to='company/', blank=True, null=True, verbose_name='Логотип')
    inn = models.CharField(max_length=20, blank=True, verbose_name='УНП')
    history = models.TextField(blank=True, verbose_name='История')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'О компании'
        verbose_name_plural = 'О компании'

    def __str__(self):
        return self.name


class GlossaryTerm(models.Model):
    term = models.CharField(max_length=200, verbose_name='Термин')
    definition = models.TextField(verbose_name='Определение')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Термин'
        verbose_name_plural = 'Словарь терминов'
        ordering = ['term']

    def __str__(self):
        return self.term


class Review(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    author = models.ForeignKey(CustomUser, on_delete=models.SET_NULL,
                                null=True, blank=True, verbose_name='Автор')
    name = models.CharField(max_length=100, verbose_name='Имя')
    rating = models.PositiveIntegerField(choices=RATING_CHOICES,
                                          validators=[MinValueValidator(1), MaxValueValidator(5)],
                                          verbose_name='Оценка')
    text = models.TextField(verbose_name='Текст отзыва')
    is_approved = models.BooleanField(default=False, verbose_name='Одобрен')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} — {self.rating}★'


class Vacancy(models.Model):
    title = models.CharField(max_length=200, verbose_name='Должность')
    description = models.TextField(verbose_name='Описание')
    requirements = models.TextField(blank=True, verbose_name='Требования')
    salary_from = models.DecimalField(max_digits=10, decimal_places=2,
                                       null=True, blank=True, verbose_name='Зарплата от')
    salary_to = models.DecimalField(max_digits=10, decimal_places=2,
                                     null=True, blank=True, verbose_name='Зарплата до')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Вакансия'
        verbose_name_plural = 'Вакансии'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True, verbose_name='Код')
    description = models.TextField(blank=True, verbose_name='Описание')
    discount_percent = models.FloatField(validators=[MinValueValidator(0), MaxValueValidator(100)],
                                          verbose_name='Скидка %')
    valid_from = models.DateField(verbose_name='Действует с')
    valid_to = models.DateField(verbose_name='Действует до')
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'
        ordering = ['-valid_to']

    def __str__(self):
        return f'{self.code} ({self.discount_percent}%)'

    @property
    def is_current(self):
        today = timezone.now().date()
        return self.valid_from <= today <= self.valid_to and self.is_active
