from datetime import date

from django.core.paginator import Paginator
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from applications.models import VolunteerApplication
from organizations.models import Organization

from .models import Category, Event

# Допустимые варианты сортировки: значение параметра sort -> поля order_by().
# Пользовательский ввод никогда не передаётся в order_by() напрямую.
EVENT_SORT_OPTIONS = {
    "date": ("Сначала ближайшие", ("date",)),
    "-date": ("Сначала поздние", ("-date",)),
    "title": ("По названию", ("title", "date")),
    "free": ("Больше свободных мест", ("-free_slots", "date")),
    "organization": ("По организации", ("organization__name", "date")),
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
    errors = []
    # Методы собственного QuerySet: published() + upcoming() + select_related(), свободные места
    queryset = Event.objects.catalog().with_free_slots()

    # Поиск по нескольким строковым полям
    query = request.GET.get("q", "").strip()
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query)
        )

    # Фильтр по полю связанной модели: категория по slug
    category_slug = request.GET.get("category", "").strip()
    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)

    # Фильтр по связанной модели: организация
    organization_id = request.GET.get("organization", "")
    if organization_id.isdigit():
        queryset = queryset.filter(organization_id=int(organization_id))

    # Фильтр по диапазону дат
    date_from = parse_date(request.GET.get("date_from"), errors, "Дата с")
    date_to = parse_date(request.GET.get("date_to"), errors, "Дата по")
    if date_from and date_to and date_from > date_to:
        errors.append("Начальная дата не может быть позже конечной.")
        date_from = date_to = None
    if date_from:
        queryset = queryset.filter(date__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(date__date__lte=date_to)

    # exclude(): убрать мероприятия, где уже набрано нужное число волонтёров
    only_free = request.GET.get("only_free") == "1"
    if only_free:
        queryset = queryset.exclude(free_slots__lte=0)

    # Сортировка только по разрешённым значениям
    sort = request.GET.get("sort", DEFAULT_EVENT_SORT)
    if sort not in EVENT_SORT_OPTIONS:
        sort = DEFAULT_EVENT_SORT
    queryset = queryset.order_by(*EVENT_SORT_OPTIONS[sort][1])

    paginator = Paginator(queryset, EVENTS_PER_PAGE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "categories": Category.objects.all(),
        "organizations": Organization.objects.order_by("name"),
        "sort_options": [(key, label) for key, (label, _fields) in EVENT_SORT_OPTIONS.items()],
        "query": query,
        "selected_category": category_slug,
        "selected_organization": organization_id,
        "date_from": request.GET.get("date_from", ""),
        "date_to": request.GET.get("date_to", ""),
        "only_free": only_free,
        "sort": sort,
        "errors": errors,
    }
    return render(request, "events/list.html", context)


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
