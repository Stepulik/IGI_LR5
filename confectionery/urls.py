from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


from shop.multitasking_views import multitasking
from django.urls import path as _path
urlpatterns = [
    _path('multitasking/', multitasking, name='multitasking'),
    path('admin/', admin.site.urls),
    path('', include('shop.urls', namespace='shop')),
    path('users/', include('users.urls', namespace='users')),
    path('api/', include('api.urls', namespace='api')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
