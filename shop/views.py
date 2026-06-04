import io, base64, calendar as cal_module, logging, requests
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse

from .models import (Product, ProductType, Order, OrderItem, Customer,
                     Employee, Article, CompanyInfo, GlossaryTerm,
                     Review, Vacancy, PromoCode, PickupPoint)
from .forms import (ProductFilterForm, ProductForm, OrderForm, UserOrderForm,
                    CustomerForm, ReviewForm)

logger = logging.getLogger('shop')


def _is_staff_or_employee(user):
    return user.is_authenticated and (user.is_staff or user.role == 'employee')

def _is_admin(user):
    return user.is_authenticated and (user.is_staff or user.role == 'admin')


# ═══════════════════════════════ ОБЩИЕ СТРАНИЦЫ ═══════════════════════════

def home(request):
    latest_article = Article.objects.filter(is_published=True).first()
    featured = Product.objects.filter(is_available=True, is_featured=True)[:6]
    if not featured:
        featured = Product.objects.filter(is_available=True)[:6]
    stats = {
        'products': Product.objects.filter(is_available=True).count(),
        'orders': Order.objects.filter(status='delivered').count(),
        'customers': Customer.objects.count(),
        'types': ProductType.objects.count(),
    }

    exchange_data = {}
    try:
        r = requests.get('https://open.er-api.com/v6/latest/BYN', timeout=3)
        if r.status_code == 200:
            d = r.json()
            exchange_data = {
                'USD': round(1 / d['rates'].get('USD', 1), 4),
                'EUR': round(1 / d['rates'].get('EUR', 1), 4),
                'RUB': round(1 / d['rates'].get('RUB', 1), 4),
            }
    except Exception as e:
        logger.warning(f'Exchange API error: {e}')

    food_fact = ''
    try:
        r2 = requests.get('https://catfact.ninja/fact', timeout=3)
        if r2.status_code == 200:
            food_fact = r2.json().get('fact', '')
    except Exception as e:
        logger.warning(f'CatFact API error: {e}')

    return render(request, 'main/home.html', {
        'latest_article': latest_article,
        'featured': featured,
        'stats': stats,
        'exchange_data': exchange_data,
        'food_fact': food_fact,
        'now': timezone.now(),
    })


def about(request):
    company = CompanyInfo.objects.first()
    employees = Employee.objects.filter(is_active=True).select_related('user')
    return render(request, 'main/about.html', {'company': company, 'employees': employees})


def news_list(request):
    articles = Article.objects.filter(is_published=True)
    paginator = Paginator(articles, 6)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'main/news.html', {'page_obj': page})


def news_detail(request, pk):
    article = get_object_or_404(Article, pk=pk, is_published=True)
    return render(request, 'main/news_detail.html', {'article': article})


@login_required
def news_create(request):
    if not _is_staff_or_employee(request.user):
        messages.error(request, 'Нет доступа.')
        return redirect('shop:news')
    from .forms import ArticleForm
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES)
        if form.is_valid():
            article = form.save()
            messages.success(request, 'Новость добавлена!')
            return redirect('shop:news_detail', pk=article.pk)
    else:
        form = ArticleForm()
    return render(request, 'main/news_form.html', {'form': form, 'title': 'Добавить новость'})


@login_required
def news_update(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if not _is_staff_or_employee(request.user):
        messages.error(request, 'Нет доступа.')
        return redirect('shop:news_detail', pk=pk)
    from .forms import ArticleForm
    if request.method == 'POST':
        form = ArticleForm(request.POST, request.FILES, instance=article)
        if form.is_valid():
            form.save()
            messages.success(request, 'Новость обновлена!')
            return redirect('shop:news_detail', pk=pk)
    else:
        form = ArticleForm(instance=article)
    return render(request, 'main/news_form.html', {'form': form, 'title': 'Редактировать новость', 'article': article})


@login_required
def news_delete(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if not _is_admin(request.user):
        messages.error(request, 'Нет доступа.')
        return redirect('shop:news_detail', pk=pk)
    if request.method == 'POST':
        article.delete()
        messages.success(request, 'Новость удалена.')
        return redirect('shop:news')
    return render(request, 'main/news_confirm_delete.html', {'article': article})


def glossary(request):
    terms = GlossaryTerm.objects.all()
    return render(request, 'main/glossary.html', {'terms': terms})


def contacts(request):
    company = CompanyInfo.objects.first()
    employees = Employee.objects.filter(is_active=True).select_related('user')
    weather = {}
    try:
        r = requests.get('https://wttr.in/Minsk?format=j1', timeout=3)
        if r.status_code == 200:
            d = r.json()
            weather = {
                'temp': d['current_condition'][0].get('temp_C', '?'),
                'desc': d['current_condition'][0].get('weatherDesc', [{}])[0].get('value', ''),
            }
    except Exception as e:
        logger.warning(f'Weather API error: {e}')
    pickup_points = PickupPoint.objects.filter(is_active=True)
    return render(request, 'main/contacts.html', {
        'company': company, 'employees': employees,
        'weather': weather, 'pickup_points': pickup_points,
    })


def privacy(request):
    return render(request, 'main/privacy.html')


def vacancies(request):
    return render(request, 'main/vacancies.html',
                  {'vacancies': Vacancy.objects.filter(is_active=True)})


# ═══════════════════════════════ ОТЗЫВЫ (CRUD для зарег. пользователя) ═══

def reviews(request):
    """
    Незарегистрированный: только читает одобренные отзывы.
    Зарегистрированный (любой): может оставлять отзывы без модерации,
    редактировать/удалять свои отзывы.
    Сотрудник/Админ: видит все отзывы и может управлять любыми.
    """
    if _is_staff_or_employee(request.user):
        all_reviews = Review.objects.all()
    else:
        all_reviews = Review.objects.filter(is_approved=True)

    form = ReviewForm()
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.warning(request, 'Войдите чтобы оставить отзыв.')
            return redirect('users:login')
        form = ReviewForm(request.POST)
        if form.is_valid():
            rv = form.save(commit=False)
            rv.author = request.user
            if not rv.name:
                rv.name = request.user.get_full_name() or request.user.username
            rv.is_approved = True  # без модерации
            rv.save()
            messages.success(request, 'Отзыв опубликован!')
            return redirect('shop:reviews')
    return render(request, 'main/reviews.html', {'reviews': all_reviews, 'form': form})


@login_required
def review_update(request, pk):
    review = get_object_or_404(Review, pk=pk)
    # Только автор или персонал/админ
    if review.author != request.user and not _is_staff_or_employee(request.user):
        messages.error(request, 'Нет доступа.')
        return redirect('shop:reviews')
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Отзыв обновлён!')
            return redirect('shop:reviews')
    else:
        form = ReviewForm(instance=review)
    return render(request, 'main/review_form.html', {'form': form, 'review': review})


@login_required
def review_delete(request, pk):
    review = get_object_or_404(Review, pk=pk)
    if review.author != request.user and not _is_staff_or_employee(request.user):
        messages.error(request, 'Нет доступа.')
        return redirect('shop:reviews')
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Отзыв удалён.')
        return redirect('shop:reviews')
    return render(request, 'main/review_confirm_delete.html', {'review': review})


def promo_codes(request):
    today = timezone.now().date()
    return render(request, 'main/promos.html', {
        'active_promos': PromoCode.objects.filter(is_active=True),
        'archive_promos': PromoCode.objects.filter(is_active=False),
        'today': today,
    })


def pickup_points(request):
    points = PickupPoint.objects.filter(is_active=True)
    return render(request, 'main/pickup_points.html', {'points': points})


# ═══════════════════════════════ ТОВАРЫ (CRUD) ═══════════════════════════

def product_list(request):
    qs = Product.objects.select_related('product_type')
    if not _is_staff_or_employee(request.user):
        qs = qs.filter(is_available=True)
    form = ProductFilterForm(request.GET)
    if form.is_valid():
        s = form.cleaned_data
        if s.get('search'):
            qs = qs.filter(Q(name__icontains=s['search']) |
                           Q(description__icontains=s['search']))
        if s.get('product_type'):
            qs = qs.filter(product_type_id=s['product_type'])
        if s.get('price_min') is not None:
            qs = qs.filter(price__gte=s['price_min'])
        if s.get('price_max') is not None:
            qs = qs.filter(price__lte=s['price_max'])
        if s.get('is_available'):
            qs = qs.filter(is_available=True)
        sort = s.get('sort')
        if sort:
            qs = qs.order_by(sort)
    paginator = Paginator(qs, 9)
    page = paginator.get_page(request.GET.get('page'))
    types = ProductType.objects.all()
    logger.info(f'Product list: {qs.count()} results')
    return render(request, 'shop/product_list.html',
                  {'page_obj': page, 'form': form, 'types': types})


def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.views_count += 1
    product.save(update_fields=['views_count'])
    similar = Product.objects.filter(
        product_type=product.product_type, is_available=True
    ).exclude(pk=pk)[:4]
    return render(request, 'shop/product_detail.html',
                  {'product': product, 'similar': similar})


@login_required
def product_create(request):
    if not _is_staff_or_employee(request.user):
        messages.error(request, 'Нет доступа. Только сотрудники могут добавлять товары.')
        return redirect('shop:product_list')
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            logger.info(f'Product #{product.pk} created by {request.user}')
            messages.success(request, 'Изделие добавлено!')
            return redirect('shop:product_detail', pk=product.pk)
    else:
        form = ProductForm()
    return render(request, 'shop/product_form.html',
                  {'form': form, 'title': 'Добавить изделие'})


@login_required
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if not _is_staff_or_employee(request.user):
        messages.error(request, 'Нет доступа.')
        return redirect('shop:product_detail', pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Изделие обновлено!')
            return redirect('shop:product_detail', pk=pk)
    else:
        form = ProductForm(instance=product)
    return render(request, 'shop/product_form.html',
                  {'form': form, 'title': 'Редактировать изделие', 'product': product})


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if not _is_admin(request.user):
        messages.error(request, 'Нет доступа. Только администратор может удалять товары.')
        return redirect('shop:product_detail', pk=pk)
    if request.method == 'POST':
        logger.warning(f'Product #{pk} deleted by {request.user}')
        product.delete()
        messages.success(request, 'Изделие удалено.')
        return redirect('shop:product_list')
    return render(request, 'shop/product_confirm_delete.html', {'product': product})


# ═══════════════════════════════ ЗАКАЗЫ (CRUD) ═══════════════════════════
# Незарегистрированный: нет доступа.
# Клиент: создаёт/просматривает/редактирует/отменяет СВОИ заказы.
# Сотрудник: видит все незавершённые заказы, редактирует статус/заказ.
# Админ: полный CRUD.

@login_required
def order_list(request):
    if _is_admin(request.user):
        qs = Order.objects.all().select_related('customer', 'employee')
    elif request.user.role == 'employee':
        # Сотрудник видит все незавершённые заказы
        qs = Order.objects.exclude(
            status__in=['delivered', 'cancelled']
        ).select_related('customer', 'employee')
    elif request.user.is_authenticated and request.user.role == 'client':
        try:
            cust = request.user.customer_profile
            qs = Order.objects.filter(customer=cust)
        except Exception:
            qs = Order.objects.none()
    else:
        qs = Order.objects.none()

    search = request.GET.get('search', '')
    if search:
        qs = qs.filter(Q(customer__last_name__icontains=search) |
                       Q(customer__first_name__icontains=search))
    sort = request.GET.get('sort', '-order_date')
    qs = qs.order_by(sort)

    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'shop/order_list.html',
                  {'page_obj': page, 'search': search})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    # Check access
    if not _is_staff_or_employee(request.user):
        try:
            cust = request.user.customer_profile
            if order.customer != cust:
                messages.error(request, 'Нет доступа.')
                return redirect('shop:order_list')
        except Exception:
            messages.error(request, 'Нет доступа.')
            return redirect('shop:order_list')
    return render(request, 'shop/order_detail.html', {'order': order})


@login_required
def order_create(request):
    """
    Сотрудник/Админ: полная форма заказа.
    Клиент: упрощённая форма (выбор товаров + адрес).
    """
    if not request.user.is_authenticated:
        return redirect('users:login')

    if _is_staff_or_employee(request.user):
        # Full form for staff
        if request.method == 'POST':
            form = OrderForm(request.POST)
            if form.is_valid():
                order = form.save()
                logger.info(f'Order #{order.pk} created by {request.user}')
                messages.success(request, f'Заказ #{order.pk} создан!')
                return redirect('shop:order_detail', pk=order.pk)
        else:
            form = OrderForm()
        return render(request, 'shop/order_form.html',
                      {'form': form, 'title': 'Новый заказ'})
    elif request.user.role == 'client':
        # Simplified form for client
        try:
            customer = request.user.customer_profile
        except Exception:
            messages.error(request, 'Сначала заполните профиль клиента.')
            return redirect('users:profile')

        products = Product.objects.filter(is_available=True)
        if request.method == 'POST':
            form = UserOrderForm(request.POST)
            if form.is_valid():
                product_id = form.cleaned_data['product']
                quantity = form.cleaned_data['quantity']
                delivery_type = form.cleaned_data['delivery_type']
                delivery_address = form.cleaned_data.get('delivery_address', '')
                comment = form.cleaned_data.get('comment', '')

                product = get_object_or_404(Product, pk=product_id, is_available=True)
                total = product.price * quantity
                if delivery_type == 'delivery':
                    total += Decimal('5.00')

                order = Order.objects.create(
                    customer=customer,
                    status='new',
                    delivery_type=delivery_type,
                    delivery_address=delivery_address,
                    delivery_cost=Decimal('5.00') if delivery_type == 'delivery' else Decimal('0'),
                    total_price=total,
                    comment=comment,
                )
                OrderItem.objects.create(order=order, product=product,
                                         quantity=quantity, price=product.price)
                messages.success(request, f'Заказ #{order.pk} оформлен!')
                return redirect('shop:order_detail', pk=order.pk)
        else:
            form = UserOrderForm()
        return render(request, 'shop/order_user_form.html',
                      {'form': form, 'title': 'Оформить заказ', 'products': products})
    else:
        messages.error(request, 'Нет доступа.')
        return redirect('shop:product_list')


@login_required
def order_update(request, pk):
    order = get_object_or_404(Order, pk=pk)

    if _is_admin(request.user):
        # Admin: full edit
        if request.method == 'POST':
            form = OrderForm(request.POST, instance=order)
            if form.is_valid():
                form.save()
                messages.success(request, 'Заказ обновлён!')
                return redirect('shop:order_detail', pk=pk)
        else:
            form = OrderForm(instance=order)
        return render(request, 'shop/order_form.html',
                      {'form': form, 'title': f'Редактировать заказ #{pk}', 'order': order})

    elif request.user.role == 'employee':
        # Employee: can edit order (including status)
        if request.method == 'POST':
            form = OrderForm(request.POST, instance=order)
            if form.is_valid():
                form.save()
                messages.success(request, 'Заказ обновлён!')
                return redirect('shop:order_detail', pk=pk)
        else:
            form = OrderForm(instance=order)
        return render(request, 'shop/order_form.html',
                      {'form': form, 'title': f'Редактировать заказ #{pk}', 'order': order})

    elif request.user.role == 'client':
        # Client: can only edit own orders that are still 'new'
        try:
            cust = request.user.customer_profile
        except Exception:
            messages.error(request, 'Нет доступа.')
            return redirect('shop:order_list')
        if order.customer != cust:
            messages.error(request, 'Нет доступа.')
            return redirect('shop:order_list')
        if order.status not in ('new',):
            messages.warning(request, 'Заказ уже обрабатывается и не может быть изменён.')
            return redirect('shop:order_detail', pk=pk)
        # Client can only change address/comment/delivery type, not status
        if request.method == 'POST':
            form = UserOrderForm(request.POST)
            if form.is_valid():
                order.delivery_type = form.cleaned_data['delivery_type']
                order.delivery_address = form.cleaned_data.get('delivery_address', '')
                order.comment = form.cleaned_data.get('comment', '')
                order.save()
                messages.success(request, 'Заказ обновлён!')
                return redirect('shop:order_detail', pk=pk)
        else:
            form = UserOrderForm(initial={
                'delivery_type': order.delivery_type,
                'delivery_address': order.delivery_address,
                'comment': order.comment,
            })
        return render(request, 'shop/order_client_edit.html',
                      {'form': form, 'order': order})
    else:
        messages.error(request, 'Нет доступа.')
        return redirect('shop:order_list')


@login_required
def order_cancel(request, pk):
    """Client can cancel their own new order."""
    order = get_object_or_404(Order, pk=pk)
    try:
        cust = request.user.customer_profile
    except Exception:
        messages.error(request, 'Нет доступа.')
        return redirect('shop:order_list')
    if order.customer != cust:
        messages.error(request, 'Нет доступа.')
        return redirect('shop:order_list')
    if order.status == 'new':
        order.status = 'cancelled'
        order.save()
        messages.success(request, 'Заказ отменён.')
    else:
        messages.warning(request, 'Нельзя отменить заказ на этом этапе.')
    return redirect('shop:order_list')


@login_required
def order_delete(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if not _is_staff_or_employee(request.user):
        messages.error(request, 'Нет доступа. Только сотрудник или администратор может удалять заказы.')
        return redirect('shop:order_list')
    if request.method == 'POST':
        order.delete()
        messages.success(request, 'Заказ удалён.')
        return redirect('shop:order_list')
    return render(request, 'shop/order_confirm_delete.html', {'order': order})


# ═══════════════════════════════ КЛИЕНТЫ (CRUD) ══════════════════════════

@login_required
def customer_list(request):
    if not _is_staff_or_employee(request.user):
        messages.error(request, 'Нет доступа.')
        return redirect('shop:product_list')
    search = request.GET.get('search', '')
    sort = request.GET.get('sort', 'last_name')
    qs = Customer.objects.all()
    if search:
        qs = qs.filter(Q(last_name__icontains=search) |
                       Q(first_name__icontains=search) |
                       Q(phone__icontains=search))
    qs = qs.order_by(sort)
    paginator = Paginator(qs, 10)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'shop/customer_list.html',
                  {'page_obj': page, 'search': search, 'sort': sort})


@login_required
def customer_create(request):
    if not _is_staff_or_employee(request.user):
        messages.error(request, 'Нет доступа.')
        return redirect('shop:product_list')
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Клиент добавлен!')
            return redirect('shop:customer_list')
    else:
        form = CustomerForm()
    return render(request, 'shop/customer_form.html',
                  {'form': form, 'title': 'Добавить клиента'})


@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if not _is_staff_or_employee(request.user):
        messages.error(request, 'Нет доступа.')
        return redirect('shop:customer_list')
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Клиент обновлён!')
            return redirect('shop:customer_list')
    else:
        form = CustomerForm(instance=customer)
    return render(request, 'shop/customer_form.html',
                  {'form': form, 'title': 'Редактировать клиента', 'customer': customer})


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if not _is_admin(request.user):
        messages.error(request, 'Нет доступа. Только администратор может удалять клиентов.')
        return redirect('shop:customer_list')
    if request.method == 'POST':
        customer.delete()
        messages.success(request, 'Клиент удалён.')
        return redirect('shop:customer_list')
    return render(request, 'shop/customer_confirm_delete.html', {'customer': customer})


# ═══════════════════════════════ СТАТИСТИКА ══════════════════════════════

@login_required
def statistics(request):
    if not _is_staff_or_employee(request.user):
        messages.error(request, 'Нет доступа.')
        return redirect('shop:product_list')

    from django.db.models.functions import TruncMonth

    delivered = Order.objects.filter(status='delivered')
    total_revenue = delivered.aggregate(s=Sum('total_price'))['s'] or 0
    avg_order = delivered.aggregate(a=Avg('total_price'))['a'] or 0
    total_delivery = delivered.aggregate(s=Sum('delivery_cost'))['s'] or 0

    by_type = Product.objects.values('product_type__name').annotate(
        cnt=Count('id')).order_by('-cnt')
    top_products = OrderItem.objects.values('product__name').annotate(
        sold=Sum('quantity'), revenue=Sum('price')).order_by('-sold')[:10]
    monthly = delivered.annotate(month=TruncMonth('order_date')).values('month').annotate(
        cnt=Count('id'), total=Sum('total_price')).order_by('month')
    customers_by_city = Customer.objects.values('city').annotate(
        cnt=Count('id')).order_by('-cnt')
    by_delivery = Order.objects.values('delivery_type').annotate(cnt=Count('id'))
    by_status = Order.objects.values('status').annotate(cnt=Count('id'))

    customers_stats = Customer.objects.annotate(
        orders_cnt=Count('orders'),
        total=Sum('orders__total_price')
    ).order_by('last_name')

    utc_now = timezone.now()
    local_now = timezone.localtime(utc_now)
    text_calendar = cal_module.month(local_now.year, local_now.month)

    import json as _json

    def to_json(qs):
        result = []
        for item in qs:
            row = {}
            for k, v in item.items():
                if hasattr(v, 'strftime'):
                    row[k] = v.strftime('%m/%Y')
                else:
                    row[k] = float(v) if hasattr(v, '__float__') else v
            result.append(row)
        return _json.dumps(result)

    import statistics as _stats
    amounts = list(delivered.values_list('total_price', flat=True))
    amounts_float = [float(a) for a in amounts]
    median_order = round(_stats.median(amounts_float), 2) if amounts_float else 0
    try:
        mode_order = round(_stats.mode(amounts_float), 2) if amounts_float else 0
    except Exception:
        mode_order = max(set(amounts_float), key=amounts_float.count) if amounts_float else 0

    from users.models import CustomUser
    today = timezone.now().date()
    users_bd = CustomUser.objects.filter(birth_date__isnull=False)
    ages = [(today - u.birth_date).days // 365 for u in users_bd]
    avg_age = round(_stats.mean(ages), 1) if ages else 0
    median_age = round(_stats.median(ages), 1) if ages else 0

    context = {
        'total_revenue': total_revenue,
        'avg_order': avg_order,
        'total_delivery': total_delivery,
        'delivered_count': delivered.count(),
        'median_order': median_order,
        'mode_order': mode_order,
        'avg_age': avg_age,
        'median_age': median_age,
        'ages_count': len(ages),
        'by_type': to_json(by_type),
        'top_products': list(top_products),
        'monthly': to_json(monthly),
        'customers_by_city': to_json(customers_by_city),
        'by_delivery': to_json(by_delivery),
        'by_status': to_json(by_status),
        'customers_stats': customers_stats,
        'utc_now': utc_now,
        'local_now': local_now,
        'text_calendar': text_calendar,
    }
    return render(request, 'shop/statistics.html', context)


# ═══════════════════════════════ ГРАФИК MATPLOTLIB ═══════════════════════

@login_required
def chart_python(request):
    if not _is_staff_or_employee(request.user):
        messages.error(request, 'Нет доступа.')
        return redirect('shop:product_list')

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    from django.db.models.functions import TruncMonth

    monthly = Order.objects.filter(status='delivered').annotate(
        month=TruncMonth('order_date')
    ).values('month').annotate(
        cnt=Count('id'), total=Sum('total_price')
    ).order_by('month')

    if monthly:
        months = [d['month'].strftime('%m/%Y') for d in monthly]
        totals = [float(d['total'] or 0) for d in monthly]
        counts = [d['cnt'] for d in monthly]
    else:
        months = ['01/2024','02/2024','03/2024','04/2024','05/2024','06/2024']
        totals = [1200, 1800, 1500, 2200, 1900, 2500]
        counts = [8, 12, 10, 15, 13, 17]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle('Статистика кондитерской «СладкийДом» (Python/matplotlib)',
                 fontsize=13, fontweight='bold')

    axes[0].bar(months, totals, color='#d63384', alpha=0.8)
    axes[0].set_title('Выручка по месяцам (руб.)')
    axes[0].set_ylabel('Выручка (руб.)')
    axes[0].tick_params(axis='x', rotation=45)
    axes[0].yaxis.set_major_formatter(
        ticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    for i, v in enumerate(totals):
        axes[0].text(i, v + 10, f'{v:.0f}', ha='center', fontsize=8)

    axes[1].plot(months, counts, marker='o', color='#f06eaa',
                 linewidth=2, markersize=7)
    axes[1].fill_between(range(len(months)), counts, alpha=0.2, color='#f06eaa')
    axes[1].set_title('Количество доставленных заказов')
    axes[1].set_ylabel('Кол-во заказов')
    axes[1].tick_params(axis='x', rotation=45)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    chart1_b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)

    by_type = Product.objects.values('product_type__name').annotate(
        cnt=Count('id')).order_by('cnt')
    if by_type:
        type_names = [d['product_type__name'] for d in by_type]
        type_counts = [d['cnt'] for d in by_type]
    else:
        type_names = ['Торты', 'Пирожные', 'Конфеты', 'Печенье', 'Зефир']
        type_counts = [15, 12, 20, 8, 6]

    colors = ['#d63384','#f06eaa','#b02870','#e85a9b','#f491c0',
              '#fac4dd','#fddbeb','#fce4f3']

    fig2, ax = plt.subplots(figsize=(8, 5))
    bars = ax.barh(type_names, type_counts,
                   color=colors[:len(type_names)], alpha=0.85)
    ax.set_title('Количество изделий по видам', fontsize=13)
    ax.set_xlabel('Количество позиций')
    for bar, val in zip(bars, type_counts):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height()/2,
                str(val), va='center', fontweight='bold')
    plt.tight_layout()
    buf2 = io.BytesIO()
    plt.savefig(buf2, format='png', dpi=100, bbox_inches='tight')
    buf2.seek(0)
    chart2_b64 = base64.b64encode(buf2.read()).decode()
    plt.close(fig2)

    top = OrderItem.objects.values('product__name').annotate(
        sold=Sum('quantity')).order_by('-sold')[:5]
    if top:
        top_names = [d['product__name'] for d in top]
        top_vals = [d['sold'] for d in top]
    else:
        top_names = ['Наполеон', 'Медовик', 'Эклеры', 'Трюфели', 'Безе']
        top_vals = [45, 38, 30, 25, 18]

    fig3, ax3 = plt.subplots(figsize=(7, 5))
    ax3.pie(top_vals, labels=top_names, autopct='%1.1f%%',
            colors=colors[:len(top_names)], startangle=90)
    ax3.set_title('Топ-5 изделий по количеству продаж', fontsize=12)
    plt.tight_layout()
    buf3 = io.BytesIO()
    plt.savefig(buf3, format='png', dpi=100, bbox_inches='tight')
    buf3.seek(0)
    chart3_b64 = base64.b64encode(buf3.read()).decode()
    plt.close(fig3)

    utc_now = timezone.now()
    local_now = timezone.localtime(utc_now)
    text_calendar = cal_module.month(local_now.year, local_now.month)

    return render(request, 'shop/chart_python.html', {
        'chart1_b64': chart1_b64,
        'chart2_b64': chart2_b64,
        'chart3_b64': chart3_b64,
        'utc_now': utc_now,
        'local_now': local_now,
        'text_calendar': text_calendar,
        'timezone': 'Europe/Minsk',
    })
