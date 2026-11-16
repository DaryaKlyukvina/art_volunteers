from django.urls import path
from . import views
urlpatterns = [
    path("event/<int:event_id>/apply/", views.apply_to_event, name="apply_to_event"),
    path("mine/", views.my_applications, name="my_applications"),
    path("organization/", views.organization_applications, name="organization_applications"),
    path("<int:application_id>/status/", views.change_application_status, name="change_application_status"),
]
