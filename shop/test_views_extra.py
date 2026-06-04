"""Дополнительные интеграционные тесты для повышения покрытия (>=80%)."""
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client as TC
from django.urls import reverse
from django.contrib.auth import get_user_model

from shop.models import (ProductType, Product, ProductTag, Customer, Order,
                         OrderItem, Employee, Article, GlossaryTerm, Review,
                         Vacancy, PromoCode, PickupPoint, CompanyInfo)

User = get_user_model()


def admin_user():
    u = User.objects.create_user('xadmin', password='pass', role='admin',
                                 first_name='Админ', last_name='Главный',
                                 birth_date=date(1980, 1, 1),
                                 is_staff=True, is_superuser=True)
    return u


def employee_user():
    u = User.objects.create_user('xemp', password='pass', role='employee',
                                 first_name='Мария', last_name='Иванова',
                                 birth_date=date(1992, 6, 15),
                                 phone='+375 (29) 111-22-33')
    Employee.objects.create(user=u, position='manager',
                            hire_date=date(2021, 1, 1), salary=Decimal('1500'))
    return u


def client_user():
    u = User.objects.create_user('xclient', password='pass', role='client',
                                 first_name='Пётр', last_name='Петров',
                                 birth_date=date(1996, 4, 4))
    return u


def seed_min():
    t = ProductType.objects.create(name='Торты')
    p1 = Product.objects.create(name='Наполеон', product_type=t,
                                price=Decimal('30'), unit='pcs', is_featured=True)
    p2 = Product.objects.create(name='Медовик', product_type=t,
                                price=Decimal('25'), unit='pcs')
    c = Customer.objects.create(last_name='Сидоров', first_name='Иван',
                                phone='+375 (29) 200-00-00', city='Минск')
    return t, p1, p2, c


class StatisticsViewTest(TestCase):
    def setUp(self):
        self.tc = TC()
        self.admin = admin_user()
        self.t, self.p1, self.p2, self.c = seed_min()
        emp_u = employee_user()
        self.emp = emp_u.employee_profile
        o = Order.objects.create(customer=self.c, employee=self.emp,
                                 status='delivered', delivery_type='delivery',
                                 delivery_cost=Decimal('5'),
                                 total_price=Decimal('60'),
                                 delivery_date=date.today())
        OrderItem.objects.create(order=o, product=self.p1, quantity=2, price=self.p1.price)
        o2 = Order.objects.create(customer=self.c, status='delivered',
                                  delivery_type='pickup', total_price=Decimal('25'))
        OrderItem.objects.create(order=o2, product=self.p2, quantity=1, price=self.p2.price)

    def test_statistics_denied_for_client(self):
        client_user()
        self.tc.login(username='xclient', password='pass')
        r = self.tc.get(reverse('shop:statistics'))
        self.assertEqual(r.status_code, 302)

    def test_statistics_full_render(self):
        self.tc.login(username='xadmin', password='pass')
        r = self.tc.get(reverse('shop:statistics'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('text_calendar', r.context)
        self.assertIn('median_order', r.context)
        self.assertIn('customers_stats', r.context)

    def test_chart_python_render(self):
        self.tc.login(username='xadmin', password='pass')
        r = self.tc.get(reverse('shop:chart_python'))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.context['chart1_b64'])
        self.assertTrue(r.context['chart2_b64'])
        self.assertTrue(r.context['chart3_b64'])

    def test_chart_denied_for_anonymous(self):
        r = self.tc.get(reverse('shop:chart_python'))
        self.assertEqual(r.status_code, 302)

    def test_chart_denied_for_client(self):
        client_user()
        self.tc.login(username='xclient', password='pass')
        r = self.tc.get(reverse('shop:chart_python'))
        self.assertEqual(r.status_code, 302)


class ProductCrudFlowTest(TestCase):
    def setUp(self):
        self.tc = TC()
        self.admin = admin_user()
        self.t, self.p1, self.p2, self.c = seed_min()

    def test_create_product_post(self):
        self.tc.login(username='xadmin', password='pass')
        r = self.tc.post(reverse('shop:product_create'), {
            'name': 'Эклер', 'product_type': self.t.pk, 'price': '12.50',
            'unit': 'pcs', 'description': 'Вкусно', 'composition': '',
            'is_available': 'on'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Product.objects.filter(name='Эклер').exists())

    def test_update_product_get_and_post(self):
        self.tc.login(username='xadmin', password='pass')
        url = reverse('shop:product_update', args=[self.p1.pk])
        self.assertEqual(self.tc.get(url).status_code, 200)
        self.tc.post(url, {'name': 'Наполеон+', 'product_type': self.t.pk,
                           'price': '40', 'unit': 'pcs', 'description': 'x',
                           'composition': '', 'is_available': 'on'})
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.name, 'Наполеон+')

    def test_update_denied_for_client(self):
        client_user()
        self.tc.login(username='xclient', password='pass')
        r = self.tc.get(reverse('shop:product_update', args=[self.p1.pk]))
        self.assertEqual(r.status_code, 302)

    def test_delete_get_confirm(self):
        self.tc.login(username='xadmin', password='pass')
        r = self.tc.get(reverse('shop:product_delete', args=[self.p1.pk]))
        self.assertEqual(r.status_code, 200)

    def test_delete_denied_for_employee(self):
        employee_user()
        self.tc.login(username='xemp', password='pass')
        r = self.tc.post(reverse('shop:product_delete', args=[self.p1.pk]))
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Product.objects.filter(pk=self.p1.pk).exists())


class OrderCrudFlowTest(TestCase):
    def setUp(self):
        self.tc = TC()
        self.admin = admin_user()
        self.t, self.p1, self.p2, self.c = seed_min()
        self.emp = employee_user().employee_profile

    def test_order_list_admin(self):
        self.tc.login(username='xadmin', password='pass')
        self.assertEqual(self.tc.get(reverse('shop:order_list')).status_code, 200)

    def test_order_list_employee(self):
        self.tc.login(username='xemp', password='pass')
        self.assertEqual(self.tc.get(reverse('shop:order_list')).status_code, 200)

    def test_order_list_client(self):
        u = client_user()
        self.c.user = u
        self.c.save()
        self.tc.login(username='xclient', password='pass')
        self.assertEqual(self.tc.get(reverse('shop:order_list')).status_code, 200)

    def test_order_create_and_detail(self):
        self.tc.login(username='xadmin', password='pass')
        self.assertEqual(self.tc.get(reverse('shop:order_create')).status_code, 200)
        r = self.tc.post(reverse('shop:order_create'), {
            'customer': self.c.pk, 'status': 'new', 'delivery_type': 'pickup',
            'delivery_cost': '0', 'discount_amount': '0', 'total_price': '30',
            'delivery_address': '', 'comment': ''})
        self.assertEqual(r.status_code, 302)
        order = Order.objects.latest('pk')
        self.assertEqual(self.tc.get(reverse('shop:order_detail', args=[order.pk])).status_code, 200)

    def test_order_update(self):
        o = Order.objects.create(customer=self.c, status='new',
                                 delivery_type='pickup', total_price=Decimal('30'))
        self.tc.login(username='xadmin', password='pass')
        url = reverse('shop:order_update', args=[o.pk])
        self.assertEqual(self.tc.get(url).status_code, 200)
        self.tc.post(url, {'customer': self.c.pk, 'status': 'ready',
                           'delivery_type': 'pickup', 'delivery_cost': '0',
                           'discount_amount': '0', 'total_price': '30',
                           'delivery_address': '', 'comment': ''})
        o.refresh_from_db()
        self.assertEqual(o.status, 'ready')

    def test_order_delete(self):
        o = Order.objects.create(customer=self.c, status='new',
                                 delivery_type='pickup', total_price=Decimal('30'))
        self.tc.login(username='xadmin', password='pass')
        self.assertEqual(self.tc.get(reverse('shop:order_delete', args=[o.pk])).status_code, 200)
        self.tc.post(reverse('shop:order_delete', args=[o.pk]))
        self.assertFalse(Order.objects.filter(pk=o.pk).exists())

    def test_order_create_denied_client(self):
        client_user()
        self.tc.login(username='xclient', password='pass')
        self.assertEqual(self.tc.get(reverse('shop:order_create')).status_code, 302)

    def test_order_calculate_total(self):
        o = Order.objects.create(customer=self.c, status='new',
                                 delivery_type='delivery',
                                 delivery_cost=Decimal('5'),
                                 discount_amount=Decimal('2'),
                                 total_price=Decimal('0'))
        OrderItem.objects.create(order=o, product=self.p1, quantity=2, price=Decimal('30'))
        self.assertEqual(o.calculate_total(), Decimal('63'))


class CustomerCrudFlowTest(TestCase):
    def setUp(self):
        self.tc = TC()
        self.admin = admin_user()
        self.t, self.p1, self.p2, self.c = seed_min()

    def test_customer_list_search_sort(self):
        self.tc.login(username='xadmin', password='pass')
        r = self.tc.get(reverse('shop:customer_list') + '?search=Сидоров&sort=last_name')
        self.assertEqual(r.status_code, 200)

    def test_customer_list_denied_client(self):
        client_user()
        self.tc.login(username='xclient', password='pass')
        self.assertEqual(self.tc.get(reverse('shop:customer_list')).status_code, 302)

    def test_customer_create(self):
        self.tc.login(username='xadmin', password='pass')
        self.assertEqual(self.tc.get(reverse('shop:customer_create')).status_code, 200)
        r = self.tc.post(reverse('shop:customer_create'), {
            'first_name': 'Анна', 'last_name': 'Кот', 'middle_name': '',
            'phone': '+375 (29) 333-44-55', 'email': 'a@a.by',
            'address': '', 'city': 'Минск', 'comment': ''})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Customer.objects.filter(last_name='Кот').exists())

    def test_customer_create_bad_phone(self):
        self.tc.login(username='xadmin', password='pass')
        r = self.tc.post(reverse('shop:customer_create'), {
            'first_name': 'Плохой', 'last_name': 'Телефон', 'middle_name': '',
            'phone': '1234', 'email': '', 'address': '', 'city': 'Минск', 'comment': ''})
        self.assertEqual(r.status_code, 200)  # форма невалидна, остаёмся
        self.assertFalse(Customer.objects.filter(last_name='Телефон').exists())

    def test_customer_update(self):
        self.tc.login(username='xadmin', password='pass')
        url = reverse('shop:customer_update', args=[self.c.pk])
        self.assertEqual(self.tc.get(url).status_code, 200)
        self.tc.post(url, {'first_name': 'Иван', 'last_name': 'Сидоров-Новый',
                           'middle_name': '', 'phone': '+375 (29) 200-00-00',
                           'email': '', 'address': '', 'city': 'Минск', 'comment': ''})
        self.c.refresh_from_db()
        self.assertEqual(self.c.last_name, 'Сидоров-Новый')

    def test_customer_delete(self):
        self.tc.login(username='xadmin', password='pass')
        self.assertEqual(self.tc.get(reverse('shop:customer_delete', args=[self.c.pk])).status_code, 200)
        self.tc.post(reverse('shop:customer_delete', args=[self.c.pk]))
        self.assertFalse(Customer.objects.filter(pk=self.c.pk).exists())

    def test_customer_total_spent(self):
        Order.objects.create(customer=self.c, status='delivered',
                             delivery_type='pickup', total_price=Decimal('100'))
        self.assertEqual(self.c.total_spent, Decimal('100'))


class ReviewFlowTest(TestCase):
    def setUp(self):
        self.tc = TC()

    def test_review_post_requires_login(self):
        r = self.tc.post(reverse('shop:reviews'), {'name': 'X', 'rating': 5, 'text': 'a' * 20})
        self.assertEqual(r.status_code, 302)

    def test_review_post_authenticated(self):
        client_user()
        self.tc.login(username='xclient', password='pass')
        r = self.tc.post(reverse('shop:reviews'),
                         {'name': 'Пётр', 'rating': 5, 'text': 'Замечательный торт!'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(Review.objects.exists())


class NewsAndPagesTest(TestCase):
    def setUp(self):
        self.tc = TC()
        self.a = Article.objects.create(title='Новость', summary='Кратко',
                                        content='Полный текст', is_published=True)

    def test_news_detail(self):
        self.assertEqual(self.tc.get(reverse('shop:news_detail', args=[self.a.pk])).status_code, 200)

    def test_news_detail_404_unpublished(self):
        a2 = Article.objects.create(title='Скрыто', summary='x', content='y', is_published=False)
        self.assertEqual(self.tc.get(reverse('shop:news_detail', args=[a2.pk])).status_code, 404)

    def test_promos_archive(self):
        PromoCode.objects.create(code='OLD', discount_percent=10,
                                 valid_from=date(2020, 1, 1), valid_to=date(2020, 12, 31),
                                 is_active=False)
        PromoCode.objects.create(code='NEW', discount_percent=15,
                                 valid_from=date.today(),
                                 valid_to=date.today() + timedelta(days=30), is_active=True)
        r = self.tc.get(reverse('shop:promos'))
        self.assertEqual(r.status_code, 200)

    def test_promo_is_current(self):
        p = PromoCode.objects.create(code='C', discount_percent=5,
                                     valid_from=date.today() - timedelta(days=1),
                                     valid_to=date.today() + timedelta(days=1), is_active=True)
        self.assertTrue(p.is_current)


class MultitaskingViewTest(TestCase):
    def setUp(self):
        self.tc = TC()

    def test_page_no_run(self):
        self.assertEqual(self.tc.get('/multitasking/').status_code, 200)

    def test_threading_demo(self):
        r = self.tc.get('/multitasking/?run=a')
        self.assertEqual(r.status_code, 200)
        self.assertIn('threading_result', r.context)
        res = r.context['threading_result']
        self.assertLessEqual(res['sold'], res['total'])

    def test_asyncio_demo(self):
        r = self.tc.get('/multitasking/?run=c')
        self.assertEqual(r.status_code, 200)
        res = r.context['asyncio_result']
        self.assertEqual(res['valid'] + res['invalid'], res['total'])
