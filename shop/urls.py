from django.urls import re_path
from . import views

app_name = 'shop'

urlpatterns = [
    # Общие страницы
    re_path(r'^$', views.home, name='home'),
    re_path(r'^about/$', views.about, name='about'),
    re_path(r'^news/$', views.news_list, name='news'),
    re_path(r'^news/(?P<pk>\d+)/$', views.news_detail, name='news_detail'),
    re_path(r'^news/create/$', views.news_create, name='news_create'),
    re_path(r'^news/(?P<pk>\d+)/edit/$', views.news_update, name='news_update'),
    re_path(r'^news/(?P<pk>\d+)/delete/$', views.news_delete, name='news_delete'),
    re_path(r'^glossary/$', views.glossary, name='glossary'),
    re_path(r'^contacts/$', views.contacts, name='contacts'),
    re_path(r'^privacy/$', views.privacy, name='privacy'),
    re_path(r'^vacancies/$', views.vacancies, name='vacancies'),
    re_path(r'^reviews/$', views.reviews, name='reviews'),
    re_path(r'^reviews/(?P<pk>\d+)/edit/$', views.review_update, name='review_update'),
    re_path(r'^reviews/(?P<pk>\d+)/delete/$', views.review_delete, name='review_delete'),
    re_path(r'^promos/$', views.promo_codes, name='promos'),
    re_path(r'^pickup-points/$', views.pickup_points, name='pickup_points'),

    # Товары CRUD
    re_path(r'^products/$', views.product_list, name='product_list'),
    re_path(r'^products/(?P<pk>\d+)/$', views.product_detail, name='product_detail'),
    re_path(r'^products/create/$', views.product_create, name='product_create'),
    re_path(r'^products/(?P<pk>\d+)/edit/$', views.product_update, name='product_update'),
    re_path(r'^products/(?P<pk>\d+)/delete/$', views.product_delete, name='product_delete'),

    # Заказы CRUD
    re_path(r'^orders/$', views.order_list, name='order_list'),
    re_path(r'^orders/(?P<pk>\d+)/$', views.order_detail, name='order_detail'),
    re_path(r'^orders/create/$', views.order_create, name='order_create'),
    re_path(r'^orders/(?P<pk>\d+)/edit/$', views.order_update, name='order_update'),
    re_path(r'^orders/(?P<pk>\d+)/cancel/$', views.order_cancel, name='order_cancel'),
    re_path(r'^orders/(?P<pk>\d+)/delete/$', views.order_delete, name='order_delete'),

    # Клиенты CRUD
    re_path(r'^customers/$', views.customer_list, name='customer_list'),
    re_path(r'^customers/create/$', views.customer_create, name='customer_create'),
    re_path(r'^customers/(?P<pk>\d+)/edit/$', views.customer_update, name='customer_update'),
    re_path(r'^customers/(?P<pk>\d+)/delete/$', views.customer_delete, name='customer_delete'),

    # Статистика и графики
    re_path(r'^statistics/$', views.statistics, name='statistics'),
    re_path(r'^statistics/chart/$', views.chart_python, name='chart_python'),
]
