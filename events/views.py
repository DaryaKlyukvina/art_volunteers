from datetime import date

from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from applications.models import VolunteerApplication
from organizations.models import Organization

from .forms import EventFilterForm
from .models import Category, Event

# Допустимые варианты сортировки: значение поля sort формы -> поля order_by().
# Пользовательский ввод никогда не передаётся в order_by() напрямую.
EVENT_SORT_FIELDS = {
    "date": ("date",),
    "-date": ("-date",),
    "title": ("title", "date"),
    "free": ("-free_slots", "date"),
    "organization": ("organization__name", "date"),
}
DEFAULT_EVENT_SORT = "date"
EVENTS_PER_PAGE = 6


def parse_date(value, errors, label):
    """Преобразует строку ГГГГ-ММ-ДД в date; при ошибке добавляет сообщение."""
    value = (value or "").strip()
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        errors.append(f"«{value}» — некорректная дата в поле «{label}». Используйте формат ГГГГ-ММ-ДД.")
        return None


def event_list(request):
    # Методы собственного QuerySet: published() + upcoming() + select_related(), свободные места
    queryset = Event.objects.catalog().with_free_slots()

    # Форма получает GET-параметры. Если параметров нет, форма не привязана (is_bound = False)
    form = EventFilterForm(request.GET or None)
    filters = {}
    if form.is_bound:
        form.is_valid()
        # cleaned_data содержит только прошедшие проверку поля: ошибочное поле не влияет на остальные фильтры
        filters = form.cleaned_data

    query = filters.get("q")
    if query:
        # Поиск по нескольким строковым полям
        queryset = queryset.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query)
        )
    if filters.get("category"):
        # Фильтр по полю связанной модели: категория по slug
        queryset = queryset.filter(category__slug=filters["category"].slug)
    if filters.get("organization"):
        queryset = queryset.filter(organization=filters["organization"])
    if filters.get("date_from"):
        queryset = queryset.filter(date__date__gte=filters["date_from"])
    if filters.get("date_to"):
        queryset = queryset.filter(date__date__lte=filters["date_to"])
    if filters.get("only_free"):
        # exclude(): убрать мероприятия, где уже набрано нужное число волонтёров
        queryset = queryset.exclude(free_slots__lte=0)

    sort = filters.get("sort") or DEFAULT_EVENT_SORT
    queryset = queryset.order_by(*EVENT_SORT_FIELDS[sort])

    page_obj = Paginator(queryset, EVENTS_PER_PAGE).get_page(request.GET.get("page"))
    return render(request, "events/list.html", {"page_obj": page_obj, "form": form})


def event_detail(request, slug):
    queryset = Event.objects.published().select_related("organization", "category").with_free_slots()
    event = get_object_or_404(queryset, slug=slug)
    # Другие мероприятия той же организации: срез QuerySet ограничивает выборку тремя записями
    more_events = (
        Event.objects.published().upcoming()
        .filter(organization=event.organization)
        .exclude(pk=event.pk)
        .order_by("date")[:3]
    )
    return render(request, "events/detail.html", {"event": event, "more_events": more_events})


def statistics(request):
    """Сводные показатели проекта: aggregate(), annotate(), values() + Count()."""
    now = timezone.now()
    application_stats = VolunteerApplication.objects.aggregate(
        total=Count("id"),
        pending=Count("id", filter=Q(status=VolunteerApplication.Status.PENDING)),
        accepted=Count("id", filter=Q(status=VolunteerApplication.Status.ACCEPTED)),
        rejected=Count("id", filter=Q(status=VolunteerApplication.Status.REJECTED)),
    )
    event_stats = Event.objects.published().aggregate(
        published=Count("id"),
        upcoming=Count("id", filter=Q(date__gte=now)),
        volunteers_needed=Sum("volunteers_needed", filter=Q(date__gte=now)),
    )
    # Категории вместе с теми, где пока нет мероприятий (Count по обратной связи = LEFT JOIN)
    categories = Category.objects.annotate(
        events_count=Count("events", filter=Q(events__status=Event.Status.PUBLISHED)),
    ).order_by("-events_count", "name")
    organizations = Organization.objects.annotate(
        events_count=Count("events", filter=Q(events__status=Event.Status.PUBLISHED), distinct=True),
        accepted_volunteers=Count(
            "events__applications",
            filter=Q(events__applications__status=VolunteerApplication.Status.ACCEPTED),
            distinct=True,
        ),
    ).order_by("-accepted_volunteers", "name")
    status_labels = dict(VolunteerApplication.Status.choices)
    by_status = [
        {"status": status_labels.get(row["status"], row["status"]), "total": row["total"]}
        for row in VolunteerApplication.objects.values("status").annotate(total=Count("id")).order_by("-total")
    ]
    context = {
        "application_stats": application_stats,
        "event_stats": event_stats,
        "categories": categories,
        "organizations": organizations,
        "by_status": by_status,
    }
    return render(request, "events/statistics.html", context)
