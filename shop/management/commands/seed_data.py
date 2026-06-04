import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from shop.models import (ProductType, Employee, Product, ProductTag,
                          Customer, Order, OrderItem, PickupPoint,
                          Article, CompanyInfo, GlossaryTerm, Review,
                          Vacancy, PromoCode)

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database — Вариант 24 Кондитерская'

    def handle(self, *args, **options):
        self.stdout.write('Seeding...')

        # Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin','admin@sweet.by','admin123',
                role='admin', first_name='Администратор', last_name='Системы',
                birth_date=date(1999,5,5))

        # 10 Employees
        emp_data = [
            ('ivanova_m','Мария','Иванова','+375 (29) 111-11-11','baker','1988-03-15'),
            ('petrov_s','Сергей','Петров','+375 (33) 222-22-22','manager','1990-07-22'),
            ('sidorova_t','Татьяна','Сидорова','+375 (44) 333-33-33','courier','1985-11-08'),
            ('kozlov_a','Алексей','Козлов','+375 (29) 444-44-44','baker','1992-04-12'),
            ('volkova_n','Наталья','Волкова','+375 (33) 555-55-55','cashier','1987-09-30'),
            ('morozov_d','Дмитрий','Морозов','+375 (44) 666-66-66','courier','1993-02-18'),
            ('novikova_e','Елена','Новикова','+375 (29) 777-77-77','baker','1991-06-25'),
            ('sokolov_v','Виктор','Соколов','+375 (33) 888-88-88','manager','1986-12-05'),
            ('popova_l','Людмила','Попова','+375 (44) 999-99-99','cashier','1994-08-14'),
            ('grishko_i','Игорь','Гришко','+375 (29) 123-45-67','admin','1989-01-20'),
        ]
        employees = []
        for uname,fn,ln,phone,pos,bd in emp_data:
            u,c = User.objects.get_or_create(username=uname, defaults=dict(
                first_name=fn, last_name=ln, email=f'{uname}@sweet.by',
                role='employee', phone=phone, birth_date=date.fromisoformat(bd),
            ))
            if c: u.set_password('emp123'); u.save()
            emp,_ = Employee.objects.get_or_create(user=u, defaults=dict(
                position=pos, hire_date=date(2019,1,15),
                salary=Decimal('1100.00'), bio=f'Специалист по кондитерскому делу.'
            ))
            employees.append(emp)

        # Client users
        clients_data = [
            ('client1','Анна','Козлова','anna@mail.by',date(1995,6,10)),
            ('client2','Иван','Смирнов','ivan@mail.by',date(1990,3,22)),
            ('client3','Ольга','Белова','olga@mail.by',date(1988,11,5)),
        ]
        client_users = []
        for uname,fn,ln,email,bd in clients_data:
            cu,c = User.objects.get_or_create(username=uname, defaults=dict(
                first_name=fn, last_name=ln, email=email,
                role='client', birth_date=bd))
            if c: cu.set_password('client123'); cu.save()
            client_users.append(cu)

        # Company
        CompanyInfo.objects.get_or_create(name='СладкийДом', defaults=dict(
            description='Авторская кондитерская ручной работы. Торты на заказ, пирожные, конфеты и другие сладости из натуральных ингредиентов.',
            founded_year=2015, address='г. Минск, ул. Кондитерская, 7',
            phone='+375 (17) 200-30-40', email='info@sladkiydom.by',
            inn='190345678', history='2015 — открытие\n2018 — расширение ассортимента\n2020 — онлайн-заказы\n2023 — 10 точек самовывоза',
        ))

        # ProductTypes (10)
        types_data = ['Торты','Пирожные','Конфеты','Печенье','Зефир','Пряники','Трюфели','Макаруны','Чизкейки','Рулеты']
        types = {}
        for t in types_data:
            obj,_ = ProductType.objects.get_or_create(name=t, defaults={'description':f'Вкусные {t.lower()} ручной работы'})
            types[t] = obj

        # Tags
        tag_names = ['без глютена','без сахара','веганское','ручная работа','хит','новинка','сезонное','на заказ']
        tags = [ProductTag.objects.get_or_create(name=t)[0] for t in tag_names]

        # Products (12+)
        products_data = [
            ('Наполеон классический','Торты','pcs',45.0,1200,'Слоёные коржи с нежным кремом из сгущёнки','Мука, масло, сгущёнка, сахар',True,True),
            ('Медовик','Торты','pcs',38.0,1100,'Медовые коржи со сметанным кремом','Мёд, мука, яйца, сметана',True,True),
            ('Красный бархат','Торты','pcs',55.0,1300,'Эффектный торт с крем-чизом','Мука, какао, краситель, крем-чиз',True,False),
            ('Эклеры шоколадные','Пирожные','pcs',4.5,350,'Классические эклеры с шоколадным кремом','Заварное тесто, шоколад, крем',True,True),
            ('Макаруны ассорти','Макаруны','box',18.0,380,'Набор 12 штук разных вкусов','Миндальная мука, сахар, краситель',True,False),
            ('Трюфели бельгийские','Трюфели','box',22.0,500,'Набор 8 шт из бельгийского шоколада','Шоколад, сливки, какао',True,True),
            ('Зефир ванильный','Зефир','kg',12.0,280,'Воздушный домашний зефир','Яблочное пюре, сахар, агар-агар',True,False),
            ('Имбирные пряники','Пряники','pcs',2.5,320,'Расписные имбирные пряники','Мука, имбирь, мёд, специи',True,False),
            ('Чизкейк Нью-Йорк','Чизкейки','pcs',42.0,1150,'Классический американский чизкейк','Крем-чиз, яйца, сахар, печенье',True,True),
            ('Шоколадное печенье','Печенье','kg',9.0,420,'Хрустящее печенье с кусочками шоколада','Мука, шоколад, масло, сахар',True,False),
            ('Конфеты Ассорти','Конфеты','box',15.0,450,'Набор шоколадных конфет 16 шт','Шоколад, орехи, сухофрукты',True,True),
            ('Бисквитный рулет','Рулеты','pcs',28.0,890,'Воздушный рулет с вишнёвой начинкой','Яйца, мука, сахар, вишня',True,False),
        ]
        products = []
        for name,ptype,unit,price,cal,desc,comp,avail,feat in products_data:
            p,created = Product.objects.get_or_create(name=name, defaults=dict(
                product_type=types[ptype], unit=unit, price=Decimal(str(price)),
                calories=cal, description=desc, composition=comp,
                is_available=avail, is_featured=feat, weight=random.randint(200,1500)
            ))
            products.append(p)

        # Customers (10)
        customers_data = [
            ('Козлова','Анна','Ивановна','+375 (29) 101-01-01','anna@mail.by','Минск'),
            ('Смирнов','Иван','Петрович','+375 (33) 202-02-02','ivan@mail.by','Минск'),
            ('Белова','Ольга','Николаевна','+375 (44) 303-03-03','olga@mail.by','Гродно'),
            ('Захаров','Михаил','Сергеевич','+375 (29) 404-04-04','misha@mail.by','Брест'),
            ('Лукашенко','Светлана','Андреевна','+375 (33) 505-05-05','sveta@mail.by','Минск'),
            ('Дорошенко','Виталий','Юрьевич','+375 (44) 606-06-06','vital@mail.by','Гомель'),
            ('Ковалёва','Юлия','Александровна','+375 (29) 707-07-07','julia@mail.by','Минск'),
            ('Бондарь','Николай','Васильевич','+375 (33) 808-08-08','nikol@mail.by','Витебск'),
            ('Мельник','Ирина','Дмитриевна','+375 (44) 909-09-09','irina@mail.by','Минск'),
            ('Шевченко','Андрей','Олегович','+375 (29) 010-10-10','andrey@mail.by','Могилёв'),
        ]
        customers = []
        for ln,fn,mn,phone,email,city in customers_data:
            c,_ = Customer.objects.get_or_create(phone=phone, defaults=dict(
                last_name=ln, first_name=fn, middle_name=mn,
                email=email, city=city, address=f'г. {city}, ул. Тестовая, 1'
            ))
            customers.append(c)

        # Link first 3 client users to first 3 customers
        for i, cu in enumerate(client_users):
            try:
                _ = cu.customer_profile
            except Exception:
                customers[i].user = cu
                customers[i].save()

        # PickupPoints
        pp_data = [
            ('Центр','г. Минск, пр. Независимости, 1','пн-пт 9-20, сб-вс 10-18','+375 (17) 200-30-40'),
            ('Запад','г. Минск, ул. Притыцкого, 62','пн-пт 10-20','+375 (17) 200-30-41'),
            ('Восток','г. Минск, пр. Партизанский, 78','пн-вс 9-21','+375 (17) 200-30-42'),
        ]
        for nm,addr,wh,ph in pp_data:
            PickupPoint.objects.get_or_create(name=nm, defaults=dict(
                address=addr, working_hours=wh, phone=ph, is_active=True))

        # Articles
        articles_data = [
            ('Новинка: Чизкейк Нью-Йорк', 'Наш новый чизкейк уже в продаже!',
             'Мы рады представить классический американский чизкейк, приготовленный по оригинальному рецепту...'),
            ('Весенняя коллекция пряников', 'Расписные пряники к весенним праздникам',
             'К весеннему сезону наши мастера подготовили особую коллекцию расписных пряников...'),
            ('Мастер-класс: торты на заказ', 'Приглашаем на мастер-класс',
             'Хотите научиться делать торты? Наши кондитеры проведут мастер-класс...'),
        ]
        for title,summary,content in articles_data:
            Article.objects.get_or_create(title=title, defaults=dict(
                summary=summary, content=content, is_published=True))

        # Glossary
        terms_data = [
            ('Ганаш','Смесь шоколада и сливок, используемая для покрытия тортов'),
            ('Темперирование','Процесс нагрева и охлаждения шоколада для придания блеска'),
            ('Бисквит','Воздушная основа для тортов из яиц, муки и сахара'),
            ('Крем-чиз','Мягкий сливочный сыр для начинок и покрытий'),
            ('Мастика','Пластичная масса для украшения тортов'),
        ]
        for term,defn in terms_data:
            GlossaryTerm.objects.get_or_create(term=term, defaults={'definition':defn})

        # Reviews (approved)
        reviews_data = [
            ('Марина К.', 5, 'Очень вкусные торты! Заказывала Медовик на день рождения — все гости были в восторге.', True),
            ('Дмитрий П.', 4, 'Хороший ассортимент, быстрая доставка. Рекомендую эклеры!', True),
            ('Светлана В.', 5, 'Лучшая кондитерская в городе! Зефир просто тает во рту.', True),
        ]
        for name,rating,text,approved in reviews_data:
            Review.objects.get_or_create(name=name, defaults=dict(
                rating=rating, text=text, is_approved=approved))

        # Vacancies
        vac_data = [
            ('Кондитер','Ищем опытного кондитера для создания тортов и пирожных',
             'Опыт работы от 2 лет, знание технологий выпечки', Decimal('1200'), Decimal('1800')),
            ('Курьер','Доставка заказов по Минску',
             'Наличие велосипеда или самоката', Decimal('800'), Decimal('1200')),
        ]
        for title,desc,req,sal_from,sal_to in vac_data:
            Vacancy.objects.get_or_create(title=title, defaults=dict(
                description=desc, requirements=req, salary_from=sal_from,
                salary_to=sal_to, is_active=True))

        # PromoCodes
        PromoCode.objects.get_or_create(code='SWEET10', defaults=dict(
            description='Скидка 10% на первый заказ',
            discount_percent=10.0,
            valid_from=date(2024,1,1), valid_to=date(2026,12,31), is_active=True))
        PromoCode.objects.get_or_create(code='CAKE15', defaults=dict(
            description='Скидка 15% на торты',
            discount_percent=15.0,
            valid_from=date(2024,1,1), valid_to=date(2026,12,31), is_active=True))

        # Orders
        statuses = ['new','processing','ready','delivering','delivered','cancelled']
        delivery_types = ['pickup','delivery']
        if Order.objects.count() < 10:
            for i in range(20):
                cust = customers[i % len(customers)]
                emp = employees[i % len(employees)]
                product = products[i % len(products)]
                status = statuses[i % len(statuses)]
                dtype = delivery_types[i % 2]
                daddr = f'г. Минск, ул. Тестовая, {i+1}' if dtype == 'delivery' else ''
                order = Order.objects.create(
                    customer=cust, employee=emp, status=status,
                    delivery_type=dtype, delivery_address=daddr,
                    delivery_cost=Decimal('5.00') if dtype == 'delivery' else Decimal('0'),
                    total_price=Decimal(str(round(product.price * (i % 3 + 1), 2))),
                    comment=f'Тестовый заказ #{i+1}',
                    delivery_date=date.today() + timedelta(days=i % 7 + 1),
                )
                OrderItem.objects.create(
                    order=order, product=product,
                    quantity=i % 3 + 1, price=product.price
                )

        self.stdout.write(self.style.SUCCESS('Done!'))
