"""Тесты ПР10: менеджеры QuerySet, slug, GeneratedField, контекстный процессор, админка."""
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from applications.models import VolunteerApplication
from organizations.models import Organization

from .models import Event


class EventModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(name="Галерея", contact="mail@example.com")
        now = timezone.now()
        cls.future = Event.objects.create(title="Ночь в галерее", description="x", organization=cls.org,
                                          date=now + timedelta(days=2), location="Москва", volunteers_needed=2,
                                          status=Event.Status.PUBLISHED)
        cls.past = Event.objects.create(title="Прошлое", description="x", organization=cls.org,
                                        date=now - timedelta(days=2), location="Москва",
                                        status=Event.Status.PUBLISHED)
        cls.cancelled = Event.objects.create(title="Отменённое", description="x", organization=cls.org,
                                             date=now + timedelta(days=3), location="Москва",
                                             status=Event.Status.CANCELLED)

    def test_queryset_methods(self):
        self.assertQuerySetEqual(Event.objects.published().upcoming(), [self.future])
        self.assertNotIn(self.cancelled, Event.objects.active())
        self.assertIn(self.future, Event.objects.for_date(timezone.localdate(self.future.date)))

    def test_slug_is_latin_unique_and_used_in_url(self):
        self.assertEqual(self.future.slug, "noch-v-galeree")
        twin = Event.objects.create(title="Ночь в галерее", description="x", organization=self.org,
                                    date=timezone.now() + timedelta(days=5), location="Москва")
        self.assertEqual(twin.slug, "noch-v-galeree-2")
        self.assertEqual(self.future.get_absolute_url(), "/events/noch-v-galeree/")
        self.assertEqual(self.client.get(self.future.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(reverse("event_detail", args=["net-takogo"])).status_code, 404)

    def test_generated_field_is_recalculated_by_database(self):
        self.assertFalse(self.future.is_large)
        self.future.volunteers_needed = 15
        self.future.save()
        self.future.refresh_from_db()
        self.assertTrue(self.future.is_large)

    def test_free_slots_count_only_accepted_applications(self):
        for i, status in enumerate(["accepted", "rejected", "pending"]):
            user = User.objects.create_user(username=f"u{i}", password="StrongPass123!")
            VolunteerApplication.objects.create(user=user, event=self.future, applicant_name="x",
                                                contact="x@example.com", status=status)
        event = Event.objects.with_free_slots().get(pk=self.future.pk)
        self.assertEqual(event.accepted_count, 1)
        self.assertEqual(event.free_slots, 1)
        self.assertEqual(VolunteerApplication.objects.for_event(self.future).pending().count(), 1)

    def test_cancel_keeps_record(self):
        self.future.cancel()
        self.assertTrue(Event.objects.filter(pk=self.future.pk, status=Event.Status.CANCELLED).exists())

    def test_context_processor(self):
        response = self.client.get(reverse("event_list"))
        self.assertEqual(response.context["site_name"], "ArtVolunteers")
        self.assertEqual(response.context["upcoming_events_count"], 1)


class AdminTests(TestCase):
    def setUp(self):
        User.objects.create_superuser("admin", "admin@example.com", "AdminPass123!")
        self.client.login(username="admin", password="AdminPass123!")
        org = Organization.objects.create(name="Галерея", contact="mail@example.com")
        self.event = Event.objects.create(title="Выставка", description="x", organization=org,
                                          date=timezone.now() + timedelta(days=2), location="Москва",
                                          volunteers_needed=1, status=Event.Status.PUBLISHED)
        self.apps = []
        for i in range(2):
            user = User.objects.create_user(username=f"v{i}", password="StrongPass123!")
            self.apps.append(VolunteerApplication.objects.create(user=user, event=self.event, applicant_name=f"V{i}",
                                                                 contact="v@example.com"))

    def test_admin_pages_open(self):
        for url in ["/admin/", "/admin/events/event/", f"/admin/events/event/{self.event.pk}/change/",
                    "/admin/applications/volunteerapplication/", "/admin/auth/user/",
                    f"/admin/auth/user/{self.apps[0].user_id}/change/", "/admin/organizations/organization/",
                    "/admin/events/event/?q=выставка&status__exact=published"]:
            self.assertEqual(self.client.get(url).status_code, 200, url)

    def test_accept_action_respects_free_slots(self):
        self.client.post("/admin/applications/volunteerapplication/", {
            "action": "accept_applications", "_selected_action": [a.pk for a in self.apps], "index": 0,
        })
        self.assertEqual(VolunteerApplication.objects.accepted().count(), 1)
