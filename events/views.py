from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from .models import Category, Event


def event_list(request):
    queryset = Event.objects.filter(status=Event.Status.PUBLISHED, date__gte=timezone.now()).select_related("organization", "category")
    query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "")
    if query:
        queryset = queryset.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(location__icontains=query))
    if category_id.isdigit():
        queryset = queryset.filter(category_id=int(category_id))
    paginator = Paginator(queryset.order_by("date"), 9)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "events/list.html", {"page_obj": page_obj, "categories": Category.objects.all(), "query": query, "selected_category": category_id})


def event_detail(request, pk):
    event = get_object_or_404(Event.objects.select_related("organization", "category"), pk=pk, status=Event.Status.PUBLISHED)
    return render(request, "events/detail.html", {"event": event})
