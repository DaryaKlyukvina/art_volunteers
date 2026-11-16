from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from events.models import Event

from .models import Organization


def organization_detail(request, pk):
    organization = get_object_or_404(Organization, pk=pk)
    # Обратная связь Organization -> Event через related_name="events"
    events = organization.events.filter(status=Event.Status.PUBLISHED, date__gte=timezone.now()).order_by("date")
    return render(request, "organizations/detail.html", {"organization": organization, "events": events})
