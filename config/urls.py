from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "ArtVolunteers — администрирование"
admin.site.site_title = "ArtVolunteers"
admin.site.index_title = "Управление данными платформы"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("organizations/", include("organizations.urls")),
    path("", include("events.urls")),
    path("applications/", include("applications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
