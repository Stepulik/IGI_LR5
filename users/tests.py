"""Тесты приложения users: регистрация, вход/выход, профиль, 18+."""
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client as TC
from django.urls import reverse
from django.contrib.auth import get_user_model

from shop.models import Customer, Order, Employee

User = get_user_model()


class RegisterTest(TestCase):
    def setUp(self):
        self.tc = TC()

    def test_register_under_18_rejected(self):
        young = (date.today() - timedelta(days=365 * 16)).isoformat()
        r = self.tc.post(reverse('users:register'), {
            'username': 'kid', 'first_name': 'Юный', 'last_name': 'Юзер',
            'email': 'k@k.by', 'birth_date': young,
            'password1': 'StrongPass123!', 'password2': 'StrongPass123!'})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(User.objects.filter(username='kid').exists())

    def test_register_over_18_ok(self):
        ok = (date.today() - timedelta(days=365 * 25)).isoformat()
        r = self.tc.post(reverse('users:register'), {
            'username': 'adultu', 'first_name': 'Взрослый', 'last_name': 'Юзер',
            'email': 'a@a.by', 'birth_date': ok,
            'password1': 'StrongPass123!', 'password2': 'StrongPass123!'})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(User.objects.filter(username='adultu').exists())

    def test_register_redirects_if_authenticated(self):
        User.objects.create_user('already', password='pass', role='client',
                                 birth_date=date(1990, 1, 1))
        self.tc.login(username='already', password='pass')
        self.assertEqual(self.tc.get(reverse('users:register')).status_code, 302)


class LoginLogoutTest(TestCase):
    def setUp(self):
        self.tc = TC()
        self.u = User.objects.create_user('loguser', password='LogPass123!',
                                          role='client', birth_date=date(1990, 1, 1))

    def test_login_get(self):
        self.assertEqual(self.tc.get(reverse('users:login')).status_code, 200)

    def test_login_authenticated_redirects(self):
        self.tc.login(username='loguser', password='LogPass123!')
        self.assertEqual(self.tc.get(reverse('users:login')).status_code, 302)

    def test_login_with_next(self):
        r = self.tc.post(reverse('users:login') + '?next=/products/',
                         {'username': 'loguser', 'password': 'LogPass123!'})
        self.assertEqual(r.status_code, 302)

    def test_logout(self):
        self.tc.login(username='loguser', password='LogPass123!')
        r = self.tc.get(reverse('users:logout'))
        self.assertEqual(r.status_code, 302)


class ProfileTest(TestCase):
    def setUp(self):
        self.tc = TC()

    def test_profile_requires_login(self):
        self.assertEqual(self.tc.get(reverse('users:profile')).status_code, 302)

    def test_profile_client_with_orders(self):
        u = User.objects.create_user('pclient', password='pass', role='client',
                                     birth_date=date(1990, 1, 1))
        c = Customer.objects.create(last_name='П', first_name='К',
                                    phone='+375 (29) 200-00-00', user=u)
        Order.objects.create(customer=c, status='new',
                             delivery_type='pickup', total_price=Decimal('30'))
        self.tc.login(username='pclient', password='pass')
        r = self.tc.get(reverse('users:profile'))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.context['orders']), 1)

    def test_profile_employee(self):
        u = User.objects.create_user('pemp', password='pass', role='employee',
                                     birth_date=date(1990, 1, 1))
        Employee.objects.create(user=u, position='manager',
                                hire_date=date(2021, 1, 1), salary=Decimal('1000'))
        self.tc.login(username='pemp', password='pass')
        self.assertEqual(self.tc.get(reverse('users:profile')).status_code, 200)

    def test_profile_update_post(self):
        User.objects.create_user('pupd', password='pass', role='client',
                                 birth_date=date(1990, 1, 1))
        self.tc.login(username='pupd', password='pass')
        r = self.tc.post(reverse('users:profile'), {
            'first_name': 'Новое', 'last_name': 'Имя', 'email': 'x@x.by',
            'phone': '+375 (29) 123-45-67', 'birth_date': '1990-01-01', 'address': 'Минск'})
        self.assertEqual(r.status_code, 302)
        self.assertEqual(User.objects.get(username='pupd').first_name, 'Новое')


class CustomUserModelTest(TestCase):
    def test_roles(self):
        emp = User.objects.create_user('roleemp', role='employee', birth_date=date(1990, 1, 1))
        cli = User.objects.create_user('rolecli', role='client', birth_date=date(1990, 1, 1))
        self.assertTrue(emp.is_employee())
        self.assertTrue(cli.is_client())
        self.assertFalse(emp.is_client())

    def test_str(self):
        u = User.objects.create_user('struser', first_name='Имя', last_name='Фам',
                                     role='client', birth_date=date(1990, 1, 1))
        self.assertIn('Имя', str(u))
