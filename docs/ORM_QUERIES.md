# Примеры ORM-запросов (ПР9)

В `events/queries.py` находятся 15 разных выражений QuerySet, сгруппированных
по категориям задания:

| Категория | Функции | Используемые выражения |
|---|---|---|
| Базовое получение (2) | `all_events`, `first_five_events` | `all()`, срез QuerySet |
| Фильтрация (4) | `published_events`, `future_events`, `events_in_location`, `events_needing_volunteers` | `filter`, `gte`, `icontains` |
| Поиск (2) | `search_events`, `search_events_by_org` | `Q`, `icontains`, поиск по FK-связи |
| Сортировка (2) | `events_soonest_first`, `events_latest_first` | `order_by` по возрастанию и убыванию |
| Связи (2) | `events_with_organization`, `categories_with_events` | `select_related`, `prefetch_related` |
| Агрегация/аннотация (2) | `total_events_count`, `categories_event_counts` | `count`, `annotate`, `Count` |
| Пагинация (1) | `events_page` | `Paginator` |

## Просмотр SQL

В Django shell можно выполнить:

```python
from events.queries import published_events, events_with_organization

qs = published_events()
print(qs.query)  # SQL, который Django построил для QuerySet

optimized = events_with_organization()
print(optimized.query)
```

`select_related` выполняет SQL JOIN и получает организацию и категорию вместе
с мероприятиями. Без него обращение к `event.organization` в цикле может
вызвать дополнительный запрос для каждого мероприятия (N+1). `prefetch_related`
использует отдельный запрос для связанных объектов и связывает их в Python.

В каталоге мероприятий применяется `select_related("organization", "category")`,
поиск через `Q`, фильтрация по категории и постраничный вывод.
