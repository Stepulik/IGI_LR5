from django.urls import re_path
from . import views

app_name = 'api'

urlpatterns = [
    re_path(r'^products/$', views.api_products, name='products'),
    re_path(r'^products/(?P<pk>\d+)/$', views.api_product_detail, name='product_detail'),
    re_path(r'^statistics/$', views.api_statistics, name='statistics'),
    re_path(r'^my-orders/$', views.api_my_orders, name='my_orders'),
]
