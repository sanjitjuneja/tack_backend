from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from django.conf import settings
import debug_toolbar
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="TackApp API",
        default_version="v1",
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    re_path(r"admin/", admin.site.urls),
    re_path(r"api/v1/", include("tack.urls")),
    re_path(r"api/v1/", include("socials.urls")),
    re_path(r"api/v1/", include("group.urls")),
    re_path(r"api/v1/", include("review.urls")),
    re_path(r"api/v1/", include("user.urls")),
    re_path(
        r"^(?P<format>\.json|\.yaml)$",
        schema_view.without_ui(cache_timeout=0),
        name="schema-json",
    ),
    re_path(
        r"^$", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"
    ),
    re_path(r"", include("social_django.urls", namespace="social")),
]

if settings.DEBUG:
    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))
