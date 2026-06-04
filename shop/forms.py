import re
from django import forms
from django.core.exceptions import ValidationError
from .models import Product, Order, OrderItem, Customer, Review, Article


class ProductFilterForm(forms.Form):
    search = forms.CharField(required=False, label='Поиск',
        widget=forms.TextInput(attrs={'placeholder': 'Название...', 'class': 'form-control'}))
    product_type = forms.IntegerField(required=False,
        widget=forms.Select(attrs={'class': 'form-select'}))
    price_min = forms.DecimalField(required=False, label='Цена от', min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', 'min': '0', 'step': '0.01'}))
    price_max = forms.DecimalField(required=False, label='Цена до', min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '999', 'min': '0', 'step': '0.01'}))
    is_available = forms.BooleanField(required=False, label='Только в наличии',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))
    sort = forms.ChoiceField(required=False, choices=[
        ('', 'По умолчанию'), ('name', 'По названию А-Я'),
        ('price', 'Цена ↑'), ('-price', 'Цена ↓'),
        ('-created_at', 'Сначала новые'), ('-views_count', 'Популярные'),
    ], widget=forms.Select(attrs={'class': 'form-select'}))


class ProductForm(forms.ModelForm):
    price = forms.DecimalField(
        min_value=0.01,
        max_digits=10,
        decimal_places=2,
        label='Цена (руб.)',
        widget=forms.NumberInput(attrs={
            'min': '0.01',
            'step': '0.01',
            'class': 'form-control',
            'placeholder': 'Например: 25.50'
        })
    )

    class Meta:
        model = Product
        exclude = ['views_count', 'created_at', 'updated_at']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'composition': forms.Textarea(attrs={'rows': 2}),
            'tags': forms.CheckboxSelectMultiple(),
        }

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price <= 0:
            raise ValidationError('Цена должна быть больше 0.')
        if price is not None and price > 99999:
            raise ValidationError('Цена не может превышать 99 999 руб.')
        return price


class OrderForm(forms.ModelForm):
    """Full form for staff/admin."""
    class Meta:
        model = Order
        fields = ['customer', 'employee', 'status', 'delivery_type',
                  'delivery_address', 'delivery_cost', 'promo_code',
                  'discount_amount', 'total_price', 'comment', 'delivery_date']
        widgets = {
            'delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'comment': forms.Textarea(attrs={'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        delivery_type = cleaned_data.get('delivery_type')
        delivery_address = cleaned_data.get('delivery_address')
        if delivery_type == 'delivery' and not delivery_address:
            raise ValidationError('При доставке укажите адрес.')
        return cleaned_data


class UserOrderForm(forms.Form):
    """Simplified order form for regular users."""
    from .models import Product as ProductModel
    product = forms.IntegerField(
        label='Изделие',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    quantity = forms.IntegerField(
        label='Количество',
        min_value=1,
        max_value=100,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1'})
    )
    delivery_type = forms.ChoiceField(
        label='Тип доставки',
        choices=[('pickup', 'Самовывоз'), ('delivery', 'Доставка (+5 руб.)')],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    delivery_address = forms.CharField(
        label='Адрес доставки',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'г. Минск, ул. ...'}),
    )
    comment = forms.CharField(
        label='Комментарий',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Product as Prod
        choices = [('', '— выберите —')] + [(p.pk, f'{p.name} — {p.price} руб./{p.get_unit_display()}')
                                              for p in Prod.objects.filter(is_available=True)]
        self.fields['product'].widget.choices = choices

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('delivery_type') == 'delivery' and not cleaned.get('delivery_address'):
            raise ValidationError('При доставке укажите адрес.')
        return cleaned


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        exclude = ['user', 'created_at', 'updated_at']
        widgets = {'comment': forms.Textarea(attrs={'rows': 2})}

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        if phone and not re.match(r'^\+375 \((29|33|44|25)\) \d{3}-\d{2}-\d{2}$', phone):
            raise ValidationError('Формат: +375 (29) XXX-XX-XX')
        return phone


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['name', 'rating', 'text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'rating': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_text(self):
        text = self.cleaned_data.get('text', '')
        if len(text) < 10:
            raise ValidationError('Отзыв должен содержать не менее 10 символов.')
        return text


class ArticleForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = ['title', 'summary', 'content', 'image', 'is_published']
        widgets = {
            'summary': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 8, 'class': 'form-control'}),
        }
