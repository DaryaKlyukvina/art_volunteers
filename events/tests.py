from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from applications.models import VolunteerApplication
from organizations.models import Organization, OrganizationMember

from .models import Category, Event


class EventCatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(name="Галерея", contact="mail@example.com")
        cls.other_org = Organization.objects.create(name="Театр", contact="theatre@example.com")
        cls.festivals = Category.objects.create(name="Фестивали", slug="festivali")
        cls.empty_category = Category.objects.create(name="Лекции", slug="lekcii")
        now = timezone.now()
        cls.published = Event.objects.create(
            title="Опубликованное", description="Описание", organization=cls.org, category=cls.festivals,
            date=now + timedelta(days=3), location="Москва", volunteers_needed=1, status=Event.Status.PUBLISHED)
        cls.second = Event.objects.create(
            title="Мастер-класс", description="Керамика", organization=cls.other_org,
            date=now + timedelta(days=10), location="Казань", volunteers_needed=5, status=Event.Status.PUBLISHED)
        Event.objects.create(
            title="Черновик", description="Не показывать", organization=cls.org,
            date=now + timedelta(days=4), location="Москва", status=Event.Status.DRAFT)
        Event.objects.create(
            title="Прошедшее", description="Уже было", organization=cls.org,
            date=now - timedelta(days=4), location="Москва", status=Event.Status.PUBLISHED)
        cls.user = User.objects.create_user(username="vol", password="StrongPass123!")
        VolunteerApplication.objects.create(user=cls.user, event=cls.published, applicant_name="Вол",
                                            contact="vol@example.com", status=VolunteerApplication.Status.ACCEPTED)

    def titles(self, params=None):
        response = self.client.get(reverse("event_list"), params or {})
        self.assertEqual(response.status_code, 200)
        return [event.title for event in response.context["page_obj"]]

    def test_public_list_shows_only_published_future_events(self):
        self.assertEqual(self.titles(), ["Опубликованное", "Мастер-класс"])

    def test_search_is_case_insensitive_for_cyrillic(self):
        self.assertEqual(self.titles({"q": "МАСТЕР"}), ["Мастер-класс"])
        self.assertEqual(self.titles({"q": "казань"}), ["Мастер-класс"])

    def test_filter_by_related_category_slug(self):
        self.assertEqual(self.titles({"category": "festivali"}), ["Опубликованное"])

    def test_exclude_events_without_free_slots(self):
        # На «Опубликованное» нужен 1 волонтёр и 1 уже принят — мест нет
        self.assertEqual(self.titles({"only_free": "1"}), ["Мастер-класс"])

    def test_sort_whitelist_and_unknown_value(self):
        self.assertEqual(self.titles({"sort": "-date"}), ["Мастер-класс", "Опубликованное"])
        self.assertEqual(self.titles({"sort": "id; DROP TABLE"}), ["Опубликованное", "Мастер-класс"])

    def test_invalid_date_shows_message(self):
        response = self.client.get(reverse("event_list"), {"date_from": "2026-13-45"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["errors"])

    def test_detail_and_404(self):
        self.assertEqual(self.client.get(self.published.get_absolute_url()).status_code, 200)
        self.assertEqual(self.client.get(reverse("event_detail", args=["net-takogo"])).status_code, 404)

    def test_statistics_counts_statuses_and_empty_categories(self):
        response = self.client.get(reverse("statistics"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["application_stats"]["accepted"], 1)
        self.assertEqual(response.context["application_stats"]["pending"], 0)
        categories = {c.name: c.events_count for c in response.context["categories"]}
        self.assertEqual(categories["Лекции"], 0)

    def test_pagination_keeps_filters(self):
        for i in range(8):
            Event.objects.create(title=f"Событие {i}", description="x", organization=self.org,
                                 date=timezone.now() + timedelta(days=20 + i), location="Москва",
                                 status=Event.Status.PUBLISHED)
        response = self.client.get(reverse("event_list"), {"q": "Событие", "sort": "-date"})
        self.assertContains(response, "?q=%D0%A1%D0%BE%D0%B1%D1%8B%D1%82%D0%B8%D0%B5&amp;sort=-date&amp;page=2")


class OrganizationApplicationsListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.org = Organization.objects.create(name="Галерея", contact="mail@example.com")
        cls.organizer = User.objects.create_user(username="org", password="StrongPass123!")
        OrganizationMember.objects.create(organization=cls.org, user=cls.organizer)
        event = Event.objects.create(title="Выставка", description="x", organization=cls.org,
                                     date=timezone.now() + timedelta(days=5), location="Москва",
                                     volunteers_needed=3, status=Event.Status.PUBLISHED)
        for i, status in enumerate(["pending", "accepted", "rejected"]):
            user = User.objects.create_user(username=f"u{i}", password="StrongPass123!")
            VolunteerApplication.objects.create(user=user, event=event, applicant_name=f"Волонтёр {i}",
                                                contact="v@example.com", status=status)

    def test_filters_and_exclude(self):
        self.client.login(username="org", password="StrongPass123!")
        url = reverse("organization_applications")
        self.assertEqual(self.client.get(url).context["page_obj"].paginator.count, 3)
        self.assertEqual(self.client.get(url, {"status": "accepted"}).context["page_obj"].paginator.count, 1)
        self.assertEqual(self.client.get(url, {"hide_rejected": "1"}).context["page_obj"].paginator.count, 2)
        row = self.client.get(url).context["page_obj"][0]
        self.assertEqual(row["event_title"], "Выставка")  # значение из связанной таблицы через F()
