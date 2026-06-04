import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, ProfileForm
from shop.models import Order

logger = logging.getLogger('users')


def register(request):
    if request.user.is_authenticated:
        return redirect('shop:home')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = 'client'
            user.save()
            # Auto-create Customer profile from registration data
            from shop.models import Customer
            Customer.objects.get_or_create(
                user=user,
                defaults={
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'middle_name': '',
                    'phone': user.phone or '',
                    'email': user.email,
                    'address': user.address or '',
                }
            )
            login(request, user)
            logger.info(f'New user: {user.username}')
            messages.success(request, f'Добро пожаловать, {user.first_name}!')
            return redirect('shop:home')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('shop:home')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Вы вошли как {user.username}.')
            return redirect(request.GET.get('next', 'shop:home'))
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('shop:home')


@login_required
def profile(request):
    user = request.user
    form = ProfileForm(request.POST or None, request.FILES or None, instance=user)
    orders = Order.objects.none()
    try:
        if user.is_client():
            orders = Order.objects.filter(
                customer=user.customer_profile).order_by('-order_date')[:5]
        elif user.is_employee():
            orders = Order.objects.filter(
                employee=user.employee_profile).order_by('-order_date')[:5]
    except Exception:
        pass
    if request.method == 'POST' and form.is_valid():
        form.save()
        # Sync Customer record if exists
        try:
            cust = user.customer_profile
            cust.first_name = user.first_name
            cust.last_name = user.last_name
            cust.phone = user.phone or ''
            cust.email = user.email
            cust.address = user.address or ''
            cust.save()
        except Exception:
            pass
        messages.success(request, 'Профиль обновлён!')
        return redirect('users:profile')
    return render(request, 'users/profile.html', {'form': form, 'orders': orders})
