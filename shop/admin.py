from django.contrib import admin
from .models import (ProductType, Employee, Product, ProductTag, Customer,
                     Order, OrderItem, PickupPoint, Article, CompanyInfo,
                     GlossaryTerm, Review, Vacancy, PromoCode)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ['product', 'quantity', 'price']


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'position', 'salary', 'hire_date', 'is_active']
    list_filter = ['position', 'is_active']
    list_editable = ['is_active']
    search_fields = ['user__first_name', 'user__last_name']

    def full_name(self, obj): return obj.full_name
    full_name.short_description = 'ФИО'


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'product_type', 'price', 'unit', 'is_available', 'is_featured', 'views_count']
    list_filter = ['product_type', 'is_available', 'is_featured']
    list_editable = ['is_available', 'is_featured']
    search_fields = ['name', 'description']
    filter_horizontal = ['tags']
    readonly_fields = ['views_count', 'created_at', 'updated_at']


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'email', 'city', 'orders_count', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone', 'email']
    list_filter = ['city']

    def full_name(self, obj): return obj.full_name
    full_name.short_description = 'ФИО'

    def orders_count(self, obj): return obj.orders.count()
    orders_count.short_description = 'Заказов'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'status', 'delivery_type', 'total_price', 'order_date']
    list_filter = ['status', 'delivery_type']
    list_editable = ['status']
    search_fields = ['customer__last_name', 'customer__first_name']
    inlines = [OrderItemInline]
    readonly_fields = ['order_date', 'updated_at']
    date_hierarchy = 'order_date'


@admin.register(PickupPoint)
class PickupPointAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'city', 'phone', 'working_hours', 'is_active']
    list_editable = ['is_active']


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_published', 'created_at']
    list_editable = ['is_published']


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email']


@admin.register(GlossaryTerm)
class GlossaryTermAdmin(admin.ModelAdmin):
    list_display = ['term', 'created_at']
    search_fields = ['term']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['name', 'rating', 'is_approved', 'created_at']
    list_editable = ['is_approved']
    list_filter = ['rating', 'is_approved']


@admin.register(Vacancy)
class VacancyAdmin(admin.ModelAdmin):
    list_display = ['title', 'salary_from', 'salary_to', 'is_active']
    list_editable = ['is_active']


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_percent', 'valid_from', 'valid_to', 'is_active']
    list_editable = ['is_active']
