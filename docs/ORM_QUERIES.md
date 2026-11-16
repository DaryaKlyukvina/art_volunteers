# ORM-запросы проекта (ПР9)

Все запросы ниже используются в работающих страницах проекта, а не только в демонстрационных функциях.

| № | Вид запроса | Выражение | Где используется |
|---|---|---|---|
| 1 | Получение набора, несколько условий | `Event.objects.filter(status=Event.Status.PUBLISHED, date__gte=timezone.now())` | `events/views.py`, `event_list` — каталог |
| 2 | Получение одного объекта | `get_object_or_404(queryset, pk=pk, status=Event.Status.PUBLISHED)` | `events/views.py`, `event_detail` |
| 3 | Поиск по нескольким полям | `filter(Q(title__icontains=q) \| Q(description__icontains=q) \| Q(location__icontains=q))` | `event_list`, параметр `q` |
| 4 | Фильтр по полю связанной модели | `filter(category__slug=category_slug)` | `event_list`, параметр `category` |
| 5 | Фильтр по внешнему ключу | `filter(organization_id=int(organization_id))` | `event_list`, параметр `organization` |
| 6 | Фильтр по диапазону дат | `filter(date__date__gte=date_from)`, `filter(date__date__lte=date_to)` | `event_list`, параметры `date_from`, `date_to` |
| 7 | Исключение записей | `exclude(free_slots__lte=0)` | `event_list`, флажок `only_free` |
| 8 | Сортировка по нескольким полям / по полю связанной модели | `order_by(*EVENT_SORT_OPTIONS[sort][1])`, например `("organization__name", "date")` | `event_list`, параметр `sort` (словарь допустимых значений) |
| 9 | Оптимизация связей | `select_related("organization", "category")` | `event_list`, `event_detail` |
| 10 | Аннотирование | `annotate(accepted_count=Count("applications", filter=Q(...)))` и `annotate(free_slots=F("volunteers_needed") - F("accepted_count"))` | `annotate_free_slots()` в `events/views.py` |
| 11 | Постраничный вывод | `Paginator(queryset, EVENTS_PER_PAGE).get_page(request.GET.get("page"))` | `event_list`, `organization_applications` |
| 12 | Ограничение выборки срезом | `filter(...).exclude(pk=event.pk).order_by("date")[:3]` | `event_detail`, блок «Ещё мероприятия организации» |
| 13 | Агрегирование с условиями | `VolunteerApplication.objects.aggregate(total=Count("id"), accepted=Count("id", filter=Q(...)), ...)` | `events/views.py`, `statistics` |
| 14 | Агрегирование суммы | `aggregate(volunteers_needed=Sum("volunteers_needed", filter=Q(date__gte=now)))` | `statistics` |
| 15 | Аннотирование по обратной связи (LEFT JOIN) | `Category.objects.annotate(events_count=Count("events", filter=Q(...))).order_by("-events_count", "name")` | `statistics` — категории без мероприятий тоже выводятся |
| 16 | Группировка через values() | `VolunteerApplication.objects.values("status").annotate(total=Count("id")).order_by("-total")` | `statistics` |
| 17 | Фильтр по полю связанной модели через две связи | `VolunteerApplication.objects.filter(event__organization_id__in=organization_ids)` | `applications/views.py`, `organization_applications` |
| 18 | Только нужные поля из связанных таблиц | `annotate(event_title=F("event__title"), username=F("user__username")).values(...)` | `organization_applications` |
| 19 | Исключение по статусу | `exclude(status=VolunteerApplication.Status.REJECTED)` | `organization_applications`, флажок «Скрыть отклонённые» |
| 20 | Обратная связь | `organization.events.filter(...)` | `organizations/views.py`, `organization_detail` |
| 21 | Список значений одного поля | `memberships.values_list("organization_id", flat=True)` | `organization_applications` |
| 22 | Проверка существования | `VolunteerApplication.objects.filter(user=..., event=...).exists()` | `applications/views.py`, `apply_to_event` |
| 23 | Создание | `form.save(commit=False)` → `application.save()` | `apply_to_event` |
| 24 | Изменение | `application.status = status`; `application.save(update_fields=[...])` | `applications/services.py` |

Удаление объектов выполняется через административную панель (`delete()`); при удалении мероприятия
заявки удаляются каскадно (`on_delete=CASCADE`), а организацию с мероприятиями удалить нельзя (`PROTECT`).

## Просмотр SQL

```python
python manage.py shell
>>> from events.models import Event
>>> qs = Event.objects.filter(status="published").select_related("organization")
>>> print(qs.query)
```

`select_related` выполняет SQL JOIN и получает организацию и категорию вместе с мероприятием.
Без него обращение к `event.organization` в цикле вызывало бы отдельный запрос для каждого мероприятия (N+1).
