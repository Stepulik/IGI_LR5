from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username','email','first_name','last_name','role','phone','is_staff']
    list_filter = ['role','is_staff','is_active']
    search_fields = ['username','email','first_name','last_name']
    list_editable = ['role']
    fieldsets = UserAdmin.fieldsets + (
        ('Доп. информация', {'fields': ('role','phone','birth_date','address','avatar')}),
    )
