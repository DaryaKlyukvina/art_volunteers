from django import forms
from django.utils import timezone

from organizations.models import Organization

from .models import Category, Event
from .validators import validate_has_letters, validate_image_size

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


class EventForm(BootstrapFormMixin, forms.ModelForm):
    """Создание и редактирование мероприятия сотрудником организации на сайте."""
    title = forms.CharField(
        label="Название", max_length=200, validators=[validate_has_letters],
        widget=forms.TextInput(attrs={"placeholder": "Например: Ночь в галерее"}),
    )

    class Meta:
        model = Event
        # Пользователь управляет только этими полями; slug, created_at, is_large формируются автоматически,
        # статус «Отменено» ставится отдельной кнопкой отмены
        fields = ("organization", "title", "category", "date", "location", "volunteers_needed",
                  "ticket_url", "status", "description", "image")
        labels = {
            "date": "Дата и время начала",
            "volunteers_needed": "Сколько нужно волонтёров",
            "ticket_url": "Ссылка на билеты",
            "image": "Изображение (JPG/PNG, до 3 МБ)",
        }
        help_texts = {
            "location": "Город и площадка. На одной площадке в один день может быть только одно мероприятие.",
        }
        widgets = {
            "date": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Что будет и чем помогут волонтёры"}),
            "ticket_url": forms.URLInput(attrs={"placeholder": "https://"}),
            "image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }

    STATUS_CHOICES = [
        (Event.Status.DRAFT, Event.Status.DRAFT.label),
        (Event.Status.PUBLISHED, Event.Status.PUBLISHED.label),
    ]

    def __init__(self, *args, organizations=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Организацию можно выбрать только из своих
        if organizations is not None:
            self.fields["organization"].queryset = organizations
            if organizations.count() == 1 and not self.instance.pk:
                self.fields["organization"].initial = organizations.first()
        self.fields["organization"].empty_label = None
        self.fields["category"].empty_label = "Без категории"
        self.fields["status"].choices = self.STATUS_CHOICES
        self.fields["image"].validators.append(validate_image_size)
        self.apply_bootstrap()

    def clean_date(self):
        event_date = self.cleaned_data["date"]
        if event_date < timezone.now():
            raise forms.ValidationError("Дата мероприятия не может быть в прошлом.")
        return event_date

    def clean_volunteers_needed(self):
        value = self.cleaned_data["volunteers_needed"]
        if self.instance.pk:
            accepted = self.instance.applications.accepted().count()
            if value < accepted:
                raise forms.ValidationError(
                    f"Уже принято {accepted} волонтёров — нельзя указать меньше."
                )
        return value

    def clean(self):
        cleaned_data = super().clean()
        location = cleaned_data.get("location")
        event_date = cleaned_data.get("date")
        if location and event_date:
            # Площадка занята, если на ней в этот день есть другое неотменённое мероприятие.
            # Редактируемое мероприятие исключается, чтобы не конфликтовать с самим собой.
            conflict = (
                Event.objects.active()
                .filter(location__iexact=location.strip(), date__date=timezone.localdate(event_date))
                .exclude(pk=self.instance.pk)
            )
            if conflict.exists():
                other = conflict.select_related("organization").first()
                raise forms.ValidationError(
                    f"Площадка «{location}» уже занята {timezone.localtime(other.date):%d.%m.%Y}: "
                    f"«{other.title}» ({other.organization}). Выберите другую дату или площадку."
                )
        return cleaned_data
