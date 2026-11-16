from django import forms
from django.utils import timezone
from .models import Event


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
