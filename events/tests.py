from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from organizations.models import Organization
from .models import Event, Category

class EventPagesTests(TestCase):
    def setUp(self):
        org = Organization.objects.create(name="Организация", contact="mail@example.com")
        Event.objects.create(title="Опубликованное", description="Описание", organization=org,
            date=timezone.now()+timedelta(days=3), location="Москва", status=Event.Status.PUBLISHED)
        Event.objects.create(title="Черновик", description="Не показывать", organization=org,
            date=timezone.now()+timedelta(days=4), location="Москва", status=Event.Status.DRAFT)

    def test_public_list_shows_only_published_events(self):
        response = Client().get(reverse("event_list"))
        self.assertContains(response, "Опубликованное")
        self.assertNotContains(response, "Черновик")
