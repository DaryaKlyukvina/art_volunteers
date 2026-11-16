from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class AccountTests(TestCase):
    def test_signup_creates_django_user_and_logs_them_in(self):
        response = self.client.post(reverse("signup"), {
            "username": "new_volunteer",
            "first_name": "Анна",
            "last_name": "Смирнова",
            "email": "anna@example.com",
            "password1": "S0mething-Strong-123",
            "password2": "S0mething-Strong-123",
        })
        self.assertRedirects(response, reverse("profile"))
        self.assertTrue(User.objects.filter(username="new_volunteer").exists())
        self.assertTrue(response.wsgi_request.user.is_authenticated)
