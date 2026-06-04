from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils import timezone
from .models import CustomUser


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True, label='Имя')
    last_name = forms.CharField(max_length=100, required=True, label='Фамилия')
    phone = forms.CharField(max_length=20, required=False, label='Телефон',
                            help_text='+375 (29) XXX-XX-XX')
    birth_date = forms.DateField(required=False, label='Дата рождения',
                                 widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = CustomUser
        fields = ['username','first_name','last_name','email','phone','birth_date','password1','password2']

    def clean_birth_date(self):
        bd = self.cleaned_data.get('birth_date')
        if bd:
            if (timezone.now().date() - bd).days // 365 < 18:
                raise forms.ValidationError('Возраст должен быть не менее 18 лет.')
        return bd


class LoginForm(AuthenticationForm):
    pass


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name','last_name','email','phone','birth_date','address','avatar']
        widgets = {'birth_date': forms.DateInput(attrs={'type': 'date'})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If birth_date is already set, lock it (read-only) and make it not required
        instance = kwargs.get('instance')
        if instance and instance.birth_date:
            self.fields['birth_date'].widget.attrs['readonly'] = True
            self.fields['birth_date'].widget.attrs['disabled'] = True
            self.fields['birth_date'].required = False

    def clean_birth_date(self):
        # If field was disabled (already set), return existing value
        instance = self.instance
        if instance and instance.birth_date:
            return instance.birth_date
        return self.cleaned_data.get('birth_date')
