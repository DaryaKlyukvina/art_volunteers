from django.shortcuts import get_object_or_404, render
from .models import Organization

def organization_detail(request, pk):
    organization = get_object_or_404(Organization, pk=pk)
    events = organization.events.filter(status="published").order_by("date")
    return render(request, "organizations/detail.html", {"organization": organization, "events": events})
