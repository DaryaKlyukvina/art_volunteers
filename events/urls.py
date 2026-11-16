from django.urls import path

from . import views

urlpatterns = [
    path("", views.event_list, name="event_list"),
    path("events/<slug:slug>/", views.event_detail, name="event_detail"),
    path("statistics/", views.statistics, name="statistics"),
    path("manage/events/", views.organizer_events, name="organizer_events"),
    path("manage/events/new/", views.event_create, name="event_create"),
    path("manage/events/<int:pk>/edit/", views.event_update, name="event_update"),
    path("manage/events/<int:pk>/cancel/", views.event_cancel, name="event_cancel"),
]
