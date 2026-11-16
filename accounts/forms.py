from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from events.forms import BootstrapFormMixin


class SignUpForm(BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(required=True, label="Электронная почта")
    first_name = forms.CharField(max_length=150, label="Имя")
    last_name = forms.CharField(max_length=150, required=False, label="Фамилия")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()
