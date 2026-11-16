from datetime import timedelta
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from organizations.models import Organization, OrganizationMember
from events.models import Event
from .models import VolunteerApplication


class VolunteerApplicationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="volunteer", password="StrongPass123!")
        self.org_user = User.objects.create_user(username="organizer", password="StrongPass123!")
        self.org = Organization.objects.create(name="Тестовая организация", contact="test@example.com")
        OrganizationMember.objects.create(organization=self.org, user=self.org_user)
        self.event = Event.objects.create(
            title="Тестовое событие", description="Описание", organization=self.org,
            date=timezone.now() + timedelta(days=10), location="Москва", volunteers_needed=1,
            status=Event.Status.PUBLISHED,
        )
        self.client = Client()

    def test_guest_cannot_open_application_form(self):
        response = self.client.get(reverse("apply_to_event", args=[self.event.pk]))
        self.assertEqual(response.status_code, 302)

    def test_logged_in_user_can_submit_application(self):
        self.client.login(username="volunteer", password="StrongPass123!")
        response = self.client.post(reverse("apply_to_event", args=[self.event.pk]), {
            "applicant_name": "Анна", "contact": "anna@example.com", "experience": "Помогала на ярмарке"
        })
        self.assertRedirects(response, reverse("profile"))
        self.assertTrue(VolunteerApplication.objects.filter(user=self.user, event=self.event).exists())

    def test_duplicate_application_is_forbidden_by_database_constraint(self):
        VolunteerApplication.objects.create(
            user=self.user, event=self.event, applicant_name="Анна", contact="anna@example.com")
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError), transaction.atomic():
            VolunteerApplication.objects.create(
                user=self.user, event=self.event, applicant_name="Анна", contact="anna@example.com")

    def test_organizer_can_accept_application(self):
        application = VolunteerApplication.objects.create(
            user=self.user, event=self.event, applicant_name="Анна", contact="anna@example.com")
        self.client.login(username="organizer", password="StrongPass123!")
        response = self.client.post(
            reverse("change_application_status", args=[application.pk]), {"status": "accepted"})
        self.assertRedirects(response, reverse("organization_applications"))
        application.refresh_from_db()
        self.assertEqual(application.status, VolunteerApplication.Status.ACCEPTED)

    def test_unrelated_user_cannot_change_application_status(self):
        User.objects.create_user(username="outsider", password="StrongPass123!")
        application = VolunteerApplication.objects.create(
            user=self.user, event=self.event, applicant_name="Анна", contact="anna@example.com")
        self.client.login(username="outsider", password="StrongPass123!")
        response = self.client.post(
            reverse("change_application_status", args=[application.pk]), {"status": "accepted"})
        self.assertEqual(response.status_code, 403)

    def test_invalid_contact_does_not_create_application(self):
        self.client.login(username="volunteer", password="StrongPass123!")
        response = self.client.post(reverse("apply_to_event", args=[self.event.pk]), {
            "applicant_name": "Анна", "contact": "x", "experience": ""
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(VolunteerApplication.objects.filter(user=self.user, event=self.event).exists())

    def test_accepting_more_than_capacity_is_rejected(self):
        first = VolunteerApplication.objects.create(
            user=self.user, event=self.event, applicant_name="Анна", contact="anna@example.com")
        second_user = User.objects.create_user(username="volunteer2", password="StrongPass123!")
        second = VolunteerApplication.objects.create(
            user=second_user, event=self.event, applicant_name="Пётр", contact="petr@example.com")
        from applications.services import set_application_status
        from django.core.exceptions import ValidationError
        set_application_status(first, VolunteerApplication.Status.ACCEPTED)
        with self.assertRaises(ValidationError):
            set_application_status(second, VolunteerApplication.Status.ACCEPTED)
