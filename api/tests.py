"""Тесты REST API — проверка ограничения для неавторизованных запросов."""
from datetime import date
from decimal import Decimal
from django.test import TestCase, Client as TC
from django.urls import reverse
from django.contrib.auth import get_user_model

from shop.models import ProductType, Product, Customer, Order, Employee

User = get_user_model()


class ApiTest(TestCase):
    def setUp(self):
        self.tc = TC()
        self.admin = User.objects.create_user('apiadmin', password='pass', role='admin',
                                               birth_date=date(1980, 1, 1),
                                               is_staff=True, is_superuser=True)
        self.client_u = User.objects.create_user('apiclient', password='pass', role='client',
                                                  birth_date=date(1995, 1, 1))
        self.t = ProductType.objects.create(name='Торты')
        self.p = Product.objects.create(name='Наполеон', product_type=self.t,
                                        price=Decimal('30'), unit='pcs')
        self.cust = Customer.objects.create(last_name='Иванов', first_name='И',
                                            phone='+375 (29) 200-00-00', user=self.client_u)
        Order.objects.create(customer=self.cust, status='new',
                             delivery_type='pickup', total_price=Decimal('30'))

    def test_products_requires_auth(self):
        self.assertEqual(self.tc.get(reverse('api:products')).status_code, 403)

    def test_products_authenticated(self):
        self.tc.login(username='apiclient', password='pass')
        r = self.tc.get(reverse('api:products'))
        self.assertEqual(r.status_code, 200)
        self.assertTrue(any(item['name'] == 'Наполеон' for item in r.json()))

    def test_product_detail(self):
        self.tc.login(username='apiclient', password='pass')
        r = self.tc.get(reverse('api:product_detail', args=[self.p.pk]))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['name'], 'Наполеон')

    def test_product_detail_404(self):
        self.tc.login(username='apiclient', password='pass')
        r = self.tc.get(reverse('api:product_detail', args=[99999]))
        self.assertEqual(r.status_code, 404)

    def test_statistics_admin_only(self):
        self.tc.login(username='apiclient', password='pass')
        self.assertEqual(self.tc.get(reverse('api:statistics')).status_code, 403)
        self.tc.login(username='apiadmin', password='pass')
        r = self.tc.get(reverse('api:statistics'))
        self.assertEqual(r.status_code, 200)
        self.assertIn('total_products', r.json())

    def test_my_orders_client(self):
        self.tc.login(username='apiclient', password='pass')
        r = self.tc.get(reverse('api:my_orders'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()), 1)

    def test_my_orders_employee(self):
        emp_u = User.objects.create_user('apiemp', password='pass', role='employee',
                                         birth_date=date(1990, 1, 1))
        emp = Employee.objects.create(user=emp_u, position='manager',
                                      hire_date=date(2021, 1, 1), salary=Decimal('1000'))
        Order.objects.create(customer=self.cust, employee=emp, status='new',
                             delivery_type='pickup', total_price=Decimal('40'))
        self.tc.login(username='apiemp', password='pass')
        r = self.tc.get(reverse('api:my_orders'))
        self.assertEqual(r.status_code, 200)
