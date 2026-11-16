from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from events.models import Event
from events.views import parse_date
from organizations.models import OrganizationMember

from .forms import VolunteerApplicationForm
from .models import VolunteerApplication
from .services import set_application_status

# Допустимые варианты сортировки списка заявок организации
APPLICATION_SORT_OPTIONS = {
    "-created": ("Сначала новые", ("-created_at",)),
    "created": ("Сначала старые", ("created_at",)),
    "event": ("По мероприятию", ("event_title", "-created_at")),
    "event_date": ("По дате мероприятия", ("event_date", "applicant_name")),
    "name": ("По имени волонтёра", ("applicant_name",)),
}
DEFAULT_APPLICATION_SORT = "-created"
APPLICATIONS_PER_PAGE = 10


@login_required
def apply_to_event(request, event_id):
    event = get_object_or_404(Event.objects.published().upcoming(), pk=event_id)
    if VolunteerApplication.objects.filter(user=request.user, event=event).exists():
        messages.info(request, "Вы уже отправляли заявку на это мероприятие.")
        return redirect(event)
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
        form = VolunteerApplicationForm(initial={
            "applicant_name": request.user.get_full_name() or request.user.username,
            "contact": request.user.email,
        })
    return render(request, "applications/apply.html", {"form": form, "event": event})


@login_required
def my_applications(request):
    applications = VolunteerApplication.objects.filter(user=request.user).with_related()
    return render(request, "applications/mine.html", {"applications": applications})


@login_required
def organization_applications(request):
    memberships = OrganizationMember.objects.filter(user=request.user).select_related("organization")
    organization_ids = memberships.values_list("organization_id", flat=True)
    if request.user.is_superuser:
        applications = VolunteerApplication.objects.all()
        events = Event.objects.all()
    else:
        # Фильтрация по полю связанной модели: организация мероприятия
        applications = VolunteerApplication.objects.for_organizations(organization_ids)
        events = Event.objects.filter(organization_id__in=organization_ids)
    errors = []

    # Несколько условий фильтрации из request.GET с проверкой значений
    event_id = request.GET.get("event", "")
    if event_id.isdigit():
        applications = applications.filter(event_id=int(event_id))
    status = request.GET.get("status", "")
    if status in VolunteerApplication.Status.values:
        applications = applications.filter(status=status)
    elif status:
        errors.append("Неизвестный статус — фильтр по статусу не применён.")
        status = ""
    if request.GET.get("hide_rejected") == "1":
        applications = applications.exclude(status=VolunteerApplication.Status.REJECTED)
    query = request.GET.get("q", "").strip()
    if query:
        applications = applications.filter(
            Q(applicant_name__icontains=query) | Q(user__username__icontains=query) | Q(contact__icontains=query)
        )
    date_from = parse_date(request.GET.get("date_from"), errors, "Подана с")
    date_to = parse_date(request.GET.get("date_to"), errors, "Подана по")
    if date_from:
        applications = applications.filter(created_at__date__gte=date_from)
    if date_to:
        applications = applications.filter(created_at__date__lte=date_to)

    # Только нужные поля: values() + вычисляемые поля из связанных таблиц через annotate(F())
    rows = applications.annotate(
        event_title=F("event__title"),
        event_date=F("event__date"),
        username=F("user__username"),
        user_email=F("user__email"),
    ).values(
        "id", "applicant_name", "contact", "experience", "status", "created_at",
        "event_title", "event_date", "username", "user_email",
    )

    sort = request.GET.get("sort", DEFAULT_APPLICATION_SORT)
    if sort not in APPLICATION_SORT_OPTIONS:
        sort = DEFAULT_APPLICATION_SORT
    rows = rows.order_by(*APPLICATION_SORT_OPTIONS[sort][1])

    page_obj = Paginator(rows, APPLICATIONS_PER_PAGE).get_page(request.GET.get("page"))
    status_labels = dict(VolunteerApplication.Status.choices)
    for row in page_obj:
        row["status_label"] = status_labels.get(row["status"], row["status"])

    context = {
        "page_obj": page_obj,
        "memberships": memberships,
        "events": events.order_by("date"),
        "statuses": VolunteerApplication.Status.choices,
        "sort_options": [(key, label) for key, (label, _f) in APPLICATION_SORT_OPTIONS.items()],
        "selected_event": event_id,
        "selected_status": status,
        "hide_rejected": request.GET.get("hide_rejected") == "1",
        "query": query,
        "date_from": request.GET.get("date_from", ""),
        "date_to": request.GET.get("date_to", ""),
        "sort": sort,
        "errors": errors,
    }
    return render(request, "applications/organization_list.html", context)


@login_required
@require_POST
def change_application_status(request, application_id):
    application = get_object_or_404(
        VolunteerApplication.objects.select_related("event__organization"), pk=application_id,
    )
    is_member = OrganizationMember.objects.filter(
        user=request.user, organization=application.event.organization,
    ).exists()
    if not is_member and not request.user.is_superuser:
        raise PermissionDenied("У вас нет доступа к заявкам этой организации.")
    try:
        set_application_status(application, request.POST.get("status", ""))
        messages.success(request, "Статус заявки обновлён.")
    except ValidationError as error:
        messages.error(request, error.messages[0])
    next_url = request.POST.get("next", "")
    if next_url.startswith("/applications/organization/"):
        return redirect(next_url)
    return redirect("organization_applications")
