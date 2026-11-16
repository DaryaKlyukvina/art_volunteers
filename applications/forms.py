from django import forms
from .models import VolunteerApplication

class VolunteerApplicationForm(forms.ModelForm):
    class Meta:
        model = VolunteerApplication
        fields = ("applicant_name", "contact", "experience")
        widgets = {"experience": forms.Textarea(attrs={"rows": 4})}
        labels = {"applicant_name": "Как к вам обращаться", "contact": "Телефон или электронная почта", "experience": "Расскажите о своём опыте"}

    def clean_contact(self):
        value = self.cleaned_data["contact"].strip()
        if len(value) < 5:
            raise forms.ValidationError("Укажите корректный контакт для связи.")
        return value
