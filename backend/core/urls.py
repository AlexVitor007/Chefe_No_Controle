from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.views.decorators.cache import never_cache

index_view = never_cache(TemplateView.as_view(template_name="index.html"))

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("greeting/", include("api.urls_greeting")),

    re_path(r"^(?:.*)/?$", index_view),
]