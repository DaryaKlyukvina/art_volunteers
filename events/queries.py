"""Набор демонстрационных ORM-запросов для требований ПР9.

Запросы сгруппированы по типам: получение, фильтрация, поиск,
сортировка, связи, агрегация/аннотация и пагинация.
"""
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from .models import Category, Event

# Базовое получение (2)
def all_events(): return Event.objects.all()
def first_five_events(): return Event.objects.all()[:5]

# Фильтрация (4)
def published_events(): return Event.objects.filter(status=Event.Status.PUBLISHED)
def future_events(): return Event.objects.filter(date__gte=timezone.now())
def events_in_location(city): return Event.objects.filter(location__icontains=city)
def events_needing_volunteers(minimum): return Event.objects.filter(volunteers_needed__gte=minimum)

# Поиск (2)
def search_events(query): return Event.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))
def search_events_by_org(query): return Event.objects.filter(organization__name__icontains=query)

# Сортировка (2)
def events_soonest_first(): return Event.objects.order_by("date")
def events_latest_first(): return Event.objects.order_by("-date")

# Связи (2)
def events_with_organization(): return Event.objects.select_related("organization", "category")
def categories_with_events(): return Category.objects.prefetch_related("events")

# Агрегация и аннотация (2)
def total_events_count(): return Event.objects.count()
def categories_event_counts(): return Category.objects.annotate(events_count=Count("events"))

# Пагинация (1)
def events_page(page_number, per_page=10):
    return Paginator(Event.objects.order_by("date"), per_page).get_page(page_number)
