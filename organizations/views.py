from django.shortcuts import get_object_or_404, render

from .models import Organization


def organization_detail(request, pk):
    organization = get_object_or_404(Organization, pk=pk)
    # Обратная связь Organization -> Event через related_name="events"
    events = organization.events.published().upcoming().order_by("date")
    return render(request, "organizations/detail.html", {"organization": organization, "events": events})
