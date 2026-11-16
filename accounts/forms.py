from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Электронная почта")
    first_name = forms.CharField(max_length=150, label="Имя")
    last_name = forms.CharField(max_length=150, required=False, label="Фамилия")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")
