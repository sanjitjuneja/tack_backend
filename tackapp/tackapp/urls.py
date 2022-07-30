from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
import debug_toolbar
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView, TokenBlacklistView


urlpatterns = [
    re_path(r"admin/", admin.site.urls),
    re_path(r"api/v1/", include("tack.urls")),
    re_path(r"api/v1/", include("socials.urls")),
    re_path(r"api/v1/", include("user.urls")),
    re_path(r"api/v1/", include("group.urls")),
    re_path(r"api/v1/", include("review.urls")),
    re_path(r"api/v1/", include("payment.urls")),
    re_path(r"api/v1/tokens/obtain/", TokenObtainPairView.as_view(), name='token_obtain_pair'),
    re_path(r"api/v1/tokens/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r"api/v1/tokens/verify/", TokenVerifyView.as_view(), name='token_verify'),
    re_path(r"api/v1/tokens/blacklist/", TokenBlacklistView.as_view(), name='token_blacklist'),
    # re_path(r"", include("social_django.urls", namespace="social")),

    path("__debug__/", include(debug_toolbar.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
