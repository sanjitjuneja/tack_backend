from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from django.conf import settings
import debug_toolbar
from rest_framework import permissions
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

# schema_view = get_schema_view(
#     openapi.Info(
#         title="Snippets API",
#         default_version="v1",
#         description="Test description",
#         terms_of_service="https://www.google.com/policies/terms/",
#         contact=openapi.Contact(email="contact@snippets.local"),
#         license=openapi.License(name="BSD License"),
#     ),
#     public=True,
#     permission_classes=(permissions.AllowAny,),
# )

urlpatterns = [
    re_path(r"admin/", admin.site.urls),
    re_path(r"api/v1/", include("tack.urls")),
    re_path(r"api/v1/", include("socials.urls")),
    re_path(r"api/v1/", include("user.urls")),
    re_path(r"api/v1/", include("group.urls")),
    re_path(r"api/v1/", include("review.urls")),
    re_path(r"api/v1/", include("payment.urls")),
    # re_path(r"", include("social_django.urls", namespace="social")),

    # re_path(
    #     r"^(?P<format>\.json|\.yaml)$",
    #     schema_view.without_ui(cache_timeout=0),
    #     name="schema-json",
    # ),
    # re_path(
    #     r"^$", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"
    # ),

    path("__debug__/", include(debug_toolbar.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
