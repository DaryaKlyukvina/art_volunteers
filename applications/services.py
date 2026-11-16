from django.core.exceptions import ValidationError
from django.db import transaction
from .models import VolunteerApplication


@transaction.atomic
def set_application_status(application, status):
    if status not in {VolunteerApplication.Status.ACCEPTED, VolunteerApplication.Status.REJECTED}:
        raise ValidationError("Недопустимый статус заявки.")
    application = VolunteerApplication.objects.select_for_update().select_related("event").get(pk=application.pk)
    if status == VolunteerApplication.Status.ACCEPTED and application.status != status:
        accepted = VolunteerApplication.objects.filter(
            event=application.event, status=VolunteerApplication.Status.ACCEPTED).count()
        if accepted >= application.event.volunteers_needed:
            raise ValidationError("На мероприятие уже принято нужное количество волонтёров.")
    application.status = status
    application.save(update_fields=["status", "updated_at"])
    return application
