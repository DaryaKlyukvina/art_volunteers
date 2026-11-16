from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from events.models import Event
from organizations.models import OrganizationMember
from .forms import VolunteerApplicationForm
from .models import VolunteerApplication
from .services import set_application_status


@login_required
def apply_to_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id, status=Event.Status.PUBLISHED, date__gte=timezone.now())
    if VolunteerApplication.objects.filter(user=request.user, event=event).exists():
        messages.info(request, "Вы уже отправляли заявку на это мероприятие.")
        return redirect("event_detail", pk=event.pk)
    if request.method == "POST":
        form = VolunteerApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.user = request.user
            application.event = event
            application.save()
            messages.success(request, "Заявка отправлена организатору.")
            return redirect("profile")
    else:
        form = VolunteerApplicationForm(
            initial={
                "applicant_name": request.user.get_full_name() or request.user.username,
                "contact": request.user.email})
    return render(request, "applications/apply.html", {"form": form, "event": event})


@login_required
def my_applications(request):
    applications = VolunteerApplication.objects.filter(user=request.user).select_related("event", "event__organization")
    return render(request, "applications/mine.html", {"applications": applications})


@login_required
def organization_applications(request):
    memberships = OrganizationMember.objects.filter(user=request.user).select_related("organization")
    organization_ids = memberships.values_list("organization_id", flat=True)
    if request.user.is_superuser:
        applications = VolunteerApplication.objects.all()
    else:
        applications = VolunteerApplication.objects.filter(event__organization_id__in=organization_ids)
    applications = applications.select_related("user", "event", "event__organization")
    return render(request, "applications/organization_list.html",
                  {"applications": applications, "memberships": memberships})


@login_required
@require_POST
def change_application_status(request, application_id):
    application = get_object_or_404(
        VolunteerApplication.objects.select_related("event__organization"),
        pk=application_id)
    if not OrganizationMember.objects.filter(
            user=request.user, organization=application.event.organization).exists() and not request.user.is_superuser:
        raise PermissionDenied("У вас нет доступа к заявкам этой организации.")
    try:
        set_application_status(application, request.POST.get("status", ""))
        messages.success(request, "Статус заявки обновлён.")
    except ValidationError as error:
        messages.error(request, error.messages[0])
    return redirect("organization_applications")
