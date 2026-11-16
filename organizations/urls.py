from django.urls import path
from . import views
urlpatterns = [path("<int:pk>/", views.organization_detail, name="organization_detail")]
