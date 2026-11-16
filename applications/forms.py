from django import forms

from events.forms import BootstrapFormMixin

from .models import VolunteerApplication


class VolunteerApplicationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = VolunteerApplication
        fields = ("applicant_name", "contact", "experience")
        widgets = {
            "experience": forms.Textarea(attrs={"rows": 4, "placeholder": "Например: помогала на ярмарке мастеров"}),
            "contact": forms.TextInput(attrs={"placeholder": "+7 900 000-00-00 или name@example.com"}),
        }
        labels = {
            "applicant_name": "Как к вам обращаться",
            "contact": "Телефон или электронная почта",
            "experience": "Расскажите о своём опыте",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()

    def clean_contact(self):
        value = self.cleaned_data["contact"].strip()
        if len(value) < 5:
            raise forms.ValidationError("Укажите корректный контакт для связи.")
        return value
