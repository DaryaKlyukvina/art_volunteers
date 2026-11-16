"""Тесты ПР11: формы фильтрации, создания, редактирования и отмены мероприятий, загрузка изображения."""
import shutil
import tempfile
from datetime import timedelta
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from organizations.models import Organization, OrganizationMember

from .forms import EventFilterForm, EventForm
from .models import Event

MEDIA_DIR = tempfile.mkdtemp()


def make_png():
    buffer = BytesIO()
    Image.new("RGB", (40, 30), "purple").save(buffer, "PNG")
    return SimpleUploadedFile("poster.png", buffer.getvalue(), content_type="image/png")


class EventFilterFormTests(TestCase):
    def test_valid_and_invalid_values(self):
        self.assertTrue(EventFilterForm({"q": "выставка", "sort": "free"}).is_valid())
        form = EventFilterForm({"q": "a", "date_from": "2026-13-01", "sort": "hack"})
        self.assertFalse(form.is_valid())
        self.assertEqual(set(form.errors), {"q", "date_from", "sort"})

    def test_date_range_is_non_field_error(self):
        form = EventFilterForm({"date_from": "2026-12-30", "date_to": "2026-12-01"})
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())
        self.assertNotIn("date_from", form.cleaned_data)

    def test_get_parameters_reach_form(self):
        response = self.client.get(reverse("event_list"), {"q": "x"})
        self.assertTrue(response.context["form"].is_bound)
        self.assertIn("q", response.context["form"].errors)


@override_settings(MEDIA_ROOT=MEDIA_DIR)
class EventManagementTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_DIR, ignore_errors=True)

    def setUp(self):
        self.org = Organization.objects.create(name="Галерея", contact="mail@example.com")
        self.other_org = Organization.objects.create(name="Театр", contact="t@example.com")
        self.organizer = User.objects.create_user(username="org", password="StrongPass123!")
        OrganizationMember.objects.create(organization=self.org, user=self.organizer)
        self.client.login(username="org", password="StrongPass123!")
        self.when = timezone.localtime(timezone.now() + timedelta(days=10)).replace(hour=19, minute=0, second=0,
                                                                                    microsecond=0)

    def data(self, **overrides):
        data = {
            "organization": self.org.pk, "title": "Вечер графики", "category": "",
            "date": self.when.strftime("%Y-%m-%dT%H:%M"), "location": "Москва, Флакон",
            "volunteers_needed": 3, "ticket_url": "", "status": "published", "description": "Описание",
        }
        data.update(overrides)
        return data

    def test_get_shows_empty_form(self):
        response = self.client.get(reverse("event_create"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_bound)
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertContains(response, 'enctype="multipart/form-data"')

    def test_create_with_image(self):
        response = self.client.post(reverse("event_create"), self.data(image=make_png()))
        self.assertRedirects(response, reverse("organizer_events"))
        event = Event.objects.get(title="Вечер графики")
        self.assertEqual(event.organization, self.org)
        self.assertTrue(event.image.name.startswith("events/poster"))
        self.assertContains(self.client.get(event.get_absolute_url()), event.image.url)

    def test_past_date_and_digits_title_are_rejected(self):
        response = self.client.post(reverse("event_create"), self.data(title="12345", date="2020-01-01T10:00"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("title", response.context["form"].errors)
        self.assertIn("date", response.context["form"].errors)
        self.assertFalse(Event.objects.exists())

    def test_busy_venue_and_cancelled_event_does_not_block(self):
        busy = Event.objects.create(title="Занято", description="x", organization=self.other_org, date=self.when,
                                    location="Москва, Флакон", status=Event.Status.PUBLISHED)
        response = self.client.post(reverse("event_create"), self.data(location="москва, флакон"))
        self.assertTrue(response.context["form"].non_field_errors())
        busy.cancel()
        response = self.client.post(reverse("event_create"), self.data())
        self.assertRedirects(response, reverse("organizer_events"))

    def test_edit_excludes_itself_but_detects_other_conflicts(self):
        self.client.post(reverse("event_create"), self.data())
        event = Event.objects.get(title="Вечер графики")
        url = reverse("event_update", args=[event.pk])
        response = self.client.post(url, self.data(volunteers_needed=5))
        self.assertRedirects(response, reverse("organizer_events"))
        event.refresh_from_db()
        self.assertEqual(event.volunteers_needed, 5)
        self.assertEqual(Event.objects.count(), 1)
        Event.objects.create(title="Другое", description="x", organization=self.other_org,
                             date=self.when + timedelta(days=1), location="Москва, Хлебозавод",
                             status=Event.Status.PUBLISHED)
        moved = self.when + timedelta(days=1)
        response = self.client.post(url, self.data(location="Москва, Хлебозавод",
                                                   date=moved.strftime("%Y-%m-%dT%H:%M")))
        self.assertTrue(response.context["form"].non_field_errors())

    def test_cancel_only_by_post_and_keeps_record(self):
        self.client.post(reverse("event_create"), self.data())
        event = Event.objects.get(title="Вечер графики")
        url = reverse("event_cancel", args=[event.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.PUBLISHED)
        self.client.post(url)
        event.refresh_from_db()
        self.assertEqual(event.status, Event.Status.CANCELLED)

    def test_missing_or_foreign_event_returns_404(self):
        foreign = Event.objects.create(title="Чужое", description="x", organization=self.other_org,
                                       date=self.when, location="Где-то", status=Event.Status.PUBLISHED)
        self.assertEqual(self.client.get(reverse("event_update", args=[foreign.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("event_update", args=[99999])).status_code, 404)

    def test_volunteer_without_organization_gets_403(self):
        User.objects.create_user(username="vol", password="StrongPass123!")
        self.client.login(username="vol", password="StrongPass123!")
        self.assertEqual(self.client.get(reverse("event_create")).status_code, 403)

    def test_form_limits_organizations(self):
        form = EventForm(organizations=Organization.objects.filter(pk=self.org.pk))
        self.assertEqual(list(form.fields["organization"].queryset), [self.org])
        self.assertNotIn("slug", form.fields)
