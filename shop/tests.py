from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client as TC
from django.urls import reverse
from django.contrib.auth import get_user_model
from shop.models import (ProductType, Product, Customer, Order, OrderItem,
                          Review, PromoCode)
from shop.forms import ReviewForm, CustomerForm, ProductFilterForm

User = get_user_model()


def make_admin():
    u,c = User.objects.get_or_create(username='ta', defaults=dict(
        first_name='A', last_name='B', role='admin',
        birth_date=date(1985,1,1), is_staff=True, is_superuser=True))
    if c: u.set_password('pass'); u.save()
    return u

def make_emp_user():
    u,c = User.objects.get_or_create(username='te', defaults=dict(
        first_name='E', last_name='F', role='employee',
        birth_date=date(1990,5,10), phone='+375 (29) 111-11-11'))
    if c: u.set_password('pass'); u.save()
    return u

def make_client_user():
    u,c = User.objects.get_or_create(username='tc', defaults=dict(
        first_name='C', last_name='D', role='client', birth_date=date(1995,3,20)))
    if c: u.set_password('pass'); u.save()
    return u

def make_ptype(name='Торты'):
    return ProductType.objects.get_or_create(name=name)[0]

def make_product(ptype=None, price=20, available=True):
    return Product.objects.create(
        name=f'Изделие #{Product.objects.count()+1}',
        product_type=ptype or make_ptype(),
        price=Decimal(str(price)), unit='pcs',
        description='Тестовое описание.', is_available=available)

def make_customer():
    return Customer.objects.get_or_create(last_name='Тест', first_name='Клиент', defaults=dict(
        phone='+375 (29) 200-00-01', email='t@t.by'))[0]


# ─── Модели ──────────────────────────────────────

class ProductTypeTest(TestCase):
    def test_str(self):
        self.assertEqual(str(ProductType(name='Торты')), 'Торты')

class ProductModelTest(TestCase):
    def setUp(self): self.p = make_product(price=45)
    def test_str_has_price(self): self.assertIn('45', str(self.p))
    def test_default_available(self): self.assertTrue(self.p.is_available)
    def test_views_default(self): self.assertEqual(self.p.views_count, 0)

class CustomerModelTest(TestCase):
    def test_full_name(self):
        c = Customer(last_name='Иванов', first_name='Иван', middle_name='Иванович')
        self.assertEqual(c.full_name, 'Иванов Иван Иванович')
    def test_str(self):
        c = Customer(last_name='Тест', first_name='Тест')
        self.assertIn('Тест', str(c))

class OrderModelTest(TestCase):
    def test_str_has_pk(self):
        p = make_product()
        c = make_customer()
        o = Order.objects.create(customer=c, status='new',
            delivery_type='pickup', total_price=Decimal('50'))
        self.assertIn(str(o.pk), str(o))

class PromoCodeModelTest(TestCase):
    def test_is_current_active(self):
        from django.utils import timezone
        today = timezone.now().date()
        p = PromoCode(code='T', discount_percent=10,
                      valid_from=today, valid_to=today+timedelta(days=10), is_active=True)
        self.assertTrue(p.is_current)

    def test_is_current_expired(self):
        p = PromoCode(code='T2', discount_percent=10,
                      valid_from=date(2020,1,1), valid_to=date(2020,12,31), is_active=True)
        self.assertFalse(p.is_current)

    def test_inactive(self):
        today = date.today()
        p = PromoCode(code='T3', discount_percent=10,
                      valid_from=today, valid_to=today+timedelta(days=10), is_active=False)
        self.assertFalse(p.is_current)

class UserModelTest(TestCase):
    def test_is_employee(self): self.assertTrue(User(username='e',role='employee').is_employee())
    def test_is_client(self): self.assertTrue(User(username='c',role='client').is_client())
    def test_str_has_role(self):
        u = User(username='x', first_name='А', last_name='Б', role='client')
        self.assertIn('Покупатель', str(u))


# ─── Формы ───────────────────────────────────────

class ReviewFormTest(TestCase):
    def test_valid(self):
        f = ReviewForm({'name':'Тест','rating':5,'text':'Очень вкусные торты, буду заказывать снова!'})
        self.assertTrue(f.is_valid())
    def test_short_text(self):
        f = ReviewForm({'name':'Тест','rating':4,'text':'Норм'})
        self.assertFalse(f.is_valid())
    def test_no_rating(self):
        f = ReviewForm({'name':'Тест','text':'Длинный текст отзыва о кондитерской.'})
        self.assertFalse(f.is_valid())

class CustomerFormTest(TestCase):
    VALID = {'first_name':'Иван','last_name':'Тест',
             'phone':'+375 (29) 123-45-67','email':'i@t.by','city':'Минск'}
    def test_valid(self): self.assertTrue(CustomerForm(self.VALID).is_valid())
    def test_bad_phone(self):
        f = CustomerForm({**self.VALID,'phone':'80291234567'})
        self.assertFalse(f.is_valid())
    def test_no_last_name(self):
        d = {**self.VALID}; del d['last_name']
        self.assertFalse(CustomerForm(d).is_valid())

class FilterFormTest(TestCase):
    def test_empty_valid(self): self.assertTrue(ProductFilterForm({}).is_valid())
    def test_with_params(self):
        f = ProductFilterForm({'search':'торт','price_min':'10','price_max':'100'})
        self.assertTrue(f.is_valid())


# ─── Публичные страницы ──────────────────────────

class PublicViewsTest(TestCase):
    def setUp(self):
        self.tc = TC()
        self.p = make_product()

    def _200(self, url): self.assertEqual(self.tc.get(url).status_code, 200)

    def test_home(self):      self._200(reverse('shop:home'))
    def test_catalog(self):   self._200(reverse('shop:product_list'))
    def test_detail(self):    self._200(reverse('shop:product_detail', args=[self.p.pk]))
    def test_about(self):     self._200(reverse('shop:about'))
    def test_news(self):      self._200(reverse('shop:news'))
    def test_glossary(self):  self._200(reverse('shop:glossary'))
    def test_contacts(self):  self._200(reverse('shop:contacts'))
    def test_privacy(self):   self._200(reverse('shop:privacy'))
    def test_vacancies(self): self._200(reverse('shop:vacancies'))
    def test_reviews(self):   self._200(reverse('shop:reviews'))
    def test_promos(self):    self._200(reverse('shop:promos'))
    def test_pickup(self):    self._200(reverse('shop:pickup_points'))

    def test_detail_increments_views(self):
        before = self.p.views_count
        self.tc.get(reverse('shop:product_detail', args=[self.p.pk]))
        self.p.refresh_from_db()
        self.assertEqual(self.p.views_count, before + 1)

    def test_list_search(self):
        self._200(reverse('shop:product_list') + '?search=торт')

    def test_list_price_filter(self):
        self._200(reverse('shop:product_list') + '?price_min=10&price_max=100')

    def test_list_sort(self):
        self._200(reverse('shop:product_list') + '?sort=price')


# ─── Авторизованные страницы ─────────────────────

class AuthViewsTest(TestCase):
    def setUp(self):
        self.tc = TC()
        self.admin = make_admin()
        self.emp_u = make_emp_user()
        from shop.models import Employee
        self.emp,_ = Employee.objects.get_or_create(user=self.emp_u, defaults=dict(
            position='baker', hire_date=date(2020,1,1), salary=Decimal('1000')))
        self.p = make_product()

    def test_create_requires_login(self):
        self.assertEqual(self.tc.get(reverse('shop:product_create')).status_code, 302)

    def test_create_as_employee(self):
        self.tc.login(username='te', password='pass')
        self.assertEqual(self.tc.get(reverse('shop:product_create')).status_code, 200)

    def test_create_as_client_redirects(self):
        make_client_user()
        self.tc.login(username='tc', password='pass')
        r = self.tc.get(reverse('shop:product_create'))
        self.assertEqual(r.status_code, 302)

    def test_statistics_requires_login(self):
        self.assertEqual(self.tc.get(reverse('shop:statistics')).status_code, 302)

    def test_statistics_as_admin(self):
        self.tc.login(username='ta', password='pass')
        self.assertEqual(self.tc.get(reverse('shop:statistics')).status_code, 200)

    def test_delete_as_admin(self):
        self.tc.login(username='ta', password='pass')
        p2 = make_product()
        self.tc.post(reverse('shop:product_delete', args=[p2.pk]))
        self.assertFalse(Product.objects.filter(pk=p2.pk).exists())

    def test_customer_list_as_employee(self):
        self.tc.login(username='te', password='pass')
        self.assertEqual(self.tc.get(reverse('shop:customer_list')).status_code, 200)


# ─── Auth регистрация/вход ───────────────────────

class UserAuthTest(TestCase):
    def setUp(self): self.tc = TC()

    def test_register_200(self):
        self.assertEqual(self.tc.get(reverse('users:register')).status_code, 200)

    def test_login_200(self):
        self.assertEqual(self.tc.get(reverse('users:login')).status_code, 200)

    def test_register_creates_user(self):
        self.tc.post(reverse('users:register'), {
            'username':'newu99','first_name':'Новый','last_name':'Юзер',
            'email':'n@t.by','password1':'SecurePass123!','password2':'SecurePass123!'})
        self.assertTrue(User.objects.filter(username='newu99').exists())

    def test_login_redirects(self):
        User.objects.create_user('lg1', password='TestPass999!',
                                 birth_date=date(1990,1,1), role='client')
        r = self.tc.post(reverse('users:login'), {'username':'lg1','password':'TestPass999!'})
        self.assertRedirects(r, reverse('shop:home'), fetch_redirect_response=False)

    def test_profile_requires_login(self):
        self.assertEqual(self.tc.get(reverse('users:profile')).status_code, 302)


# ─── Валидация ───────────────────────────────────

class ValidationTest(TestCase):
    def test_phone_valid(self):
        from users.models import validate_phone
        for p in ['+375 (29) 123-45-67','+375 (33) 987-65-43','+375 (44) 000-00-00']:
            validate_phone(p)

    def test_phone_invalid(self):
        from users.models import validate_phone
        from django.core.exceptions import ValidationError
        for p in ['80291234567','+375291234567','+375 (28) 123-45-67']:
            with self.assertRaises(ValidationError): validate_phone(p)

    def test_age_under_18(self):
        from users.models import validate_age_18
        from django.core.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            validate_age_18(date.today()-timedelta(days=365*16))

    def test_age_over_18(self):
        from users.models import validate_age_18
        validate_age_18(date.today()-timedelta(days=365*20))


# ─── CRUD ORM ────────────────────────────────────

class ProductCRUDTest(TestCase):
    def test_create(self): self.assertIsNotNone(make_product().pk)
    def test_read(self):
        p = make_product()
        self.assertEqual(Product.objects.get(pk=p.pk).name, p.name)
    def test_update(self):
        p = make_product()
        p.price = Decimal('99')
        p.save(); p.refresh_from_db()
        self.assertEqual(p.price, Decimal('99'))
    def test_delete(self):
        p = make_product(); pk = p.pk; p.delete()
        self.assertFalse(Product.objects.filter(pk=pk).exists())
    def test_filter(self):
        make_product(available=True)
        self.assertGreater(Product.objects.filter(is_available=True).count(), 0)
    def test_order_by_price(self):
        make_product(price=10); make_product(price=100)
        ps = list(Product.objects.order_by('price'))
        self.assertLessEqual(ps[0].price, ps[-1].price)


# ─── Связи ───────────────────────────────────────

class RelationsTest(TestCase):
    def test_product_fk_type(self):
        t = make_ptype('Торты')
        p = make_product(ptype=t)
        self.assertIn(p, t.products.all())

    def test_product_m2m_tags(self):
        from shop.models import ProductTag
        p = make_product()
        t1 = ProductTag.objects.create(name='тег1')
        t2 = ProductTag.objects.create(name='тег2')
        p.tags.set([t1,t2])
        self.assertEqual(p.tags.count(), 2)

    def test_order_fk_customer(self):
        c = make_customer()
        o = Order.objects.create(customer=c, status='new',
            delivery_type='pickup', total_price=Decimal('50'))
        self.assertEqual(o.customer, c)
        self.assertIn(o, c.orders.all())

    def test_orderitem_fk(self):
        p = make_product()
        c = make_customer()
        o = Order.objects.create(customer=c, status='new',
            delivery_type='pickup', total_price=Decimal('40'))
        item = OrderItem.objects.create(order=o, product=p, quantity=2, price=p.price)
        self.assertEqual(item.subtotal, p.price * 2)
