from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError


class CustomUserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter Password'}),
        label='Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        label='Confirm Password'
    )

    class Meta:
        model = User
        fields = ['first_name', 'username', 'email', 'password']
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'Enter Full Name'}),
            'username': forms.TextInput(attrs={'placeholder': 'Enter Username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Enter Email'}),
        }
        labels = {
            'first_name': 'Full Name',
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Passwords do not match.")
        return cleaned_data



from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-control'})
    )


from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'description', 'category', 'price', 'quantity', 'size', 'image']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class CustomUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'email', 'is_active', 'is_superuser', 'is_staff', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()
        return user

class CustomUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'email']
