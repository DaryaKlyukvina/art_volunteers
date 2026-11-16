from django import forms
from django.utils import timezone

from organizations.models import Organization

from .models import Category, Event

SORT_CHOICES = [
    ("date", "Сначала ближайшие"),
    ("-date", "Сначала поздние"),
    ("title", "По названию"),
    ("free", "Больше свободных мест"),
    ("organization", "По организации"),
]


class BootstrapFormMixin:
    """Добавляет CSS-классы Bootstrap всем полям формы."""

    def apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                css = "form-check-input"
            elif isinstance(widget, forms.Select):
                css = "form-select"
            else:
                css = "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()


class EventFilterForm(BootstrapFormMixin, forms.Form):
    """Фильтр каталога мероприятий. Данные приходят из GET-параметров."""
    q = forms.CharField(
        label="Поиск", required=False, max_length=100,
        widget=forms.TextInput(attrs={"placeholder": "Название, описание или место", "type": "search"}),
    )
    category = forms.ModelChoiceField(
        label="Категория", required=False, queryset=Category.objects.all(),
        to_field_name="slug", empty_label="Все категории",
    )
    organization = forms.ModelChoiceField(
        label="Организация", required=False, queryset=Organization.objects.order_by("name"),
        empty_label="Все организации",
    )
    date_from = forms.DateField(label="Дата с", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(label="Дата по", required=False, widget=forms.DateInput(attrs={"type": "date"}))
    sort = forms.ChoiceField(label="Сортировка", required=False, choices=SORT_CHOICES)
    only_free = forms.BooleanField(label="Только со свободными местами", required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean_q(self):
        query = self.cleaned_data["q"].strip()
        if query and len(query) < 2:
            raise forms.ValidationError("Введите для поиска не меньше двух символов.")
        return query

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get("date_from")
        date_to = cleaned_data.get("date_to")
        if date_from and date_to and date_from > date_to:
            # Общая ошибка формы (не относится к одному полю); обе даты не применяются
            cleaned_data.pop("date_from")
            cleaned_data.pop("date_to")
            raise forms.ValidationError("Начальная дата не может быть позже конечной.")
        return cleaned_data


class EventAdminForm(forms.ModelForm):
    """ModelForm для создания и редактирования мероприятий в Django Admin."""
    class Meta:
        model = Event
        fields = "__all__"

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        event_date = cleaned_data.get("date")
        volunteers_needed = cleaned_data.get("volunteers_needed")
        if status == Event.Status.PUBLISHED and event_date and event_date < timezone.now():
            self.add_error("date", "Нельзя публиковать мероприятие с датой в прошлом.")
        if volunteers_needed is not None and volunteers_needed < 0:
            self.add_error("volunteers_needed", "Количество волонтёров не может быть отрицательным.")
        return cleaned_data
