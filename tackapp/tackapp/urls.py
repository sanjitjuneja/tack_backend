from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
import debug_toolbar
from drf_spectacular.views import SpectacularSwaggerView, SpectacularAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView, TokenBlacklistView

from tackapp import consumers
from tackapp.views import HealthCheck
from user.auth_backend import CustomJWTSerializer, CustomTokenObtainPairView

urlpatterns = [
    # re_path(r"^jet/", include("jet.urls", "jet")),
    # re_path(r"jet/dashboard/", include("jet.dashboard.urls", "jet-dashboard")),
    re_path(r'^advanced_filters/', include('advanced_filters.urls')),
    re_path(r"admin/", admin.site.urls),
    re_path(r"api/v1/", include("tack.urls")),
    re_path(r"api/v1/", include("user.urls")),
    re_path(r"api/v1/", include("group.urls")),
    re_path(r"api/v1/", include("review.urls")),
    re_path(r"api/v1/", include("payment.urls")),
    re_path(r"api/v1/", include("socials.urls")),
    re_path(r"api/v1/tokens/obtain/",
            CustomTokenObtainPairView.as_view(
                serializer_class=CustomJWTSerializer
            ),
            name='token_obtain_pair'),
    re_path(r"api/v1/tokens/refresh/", TokenRefreshView.as_view(), name='token_refresh'),
    re_path(r"api/v1/tokens/verify/", TokenVerifyView.as_view(), name='token_verify'),
    re_path(r"api/v1/tokens/blacklist/", TokenBlacklistView.as_view(), name='token_blacklist'),
    re_path(r"stripe/", include("djstripe.urls", namespace="djstripe")),
    re_path(r"healthcheck/", HealthCheck.as_view()),

    re_path(r'api/schema/', SpectacularAPIView.as_view(), name='schema'),
    # Optional UI:
    re_path(r'swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

websocket_urlpatterns = [
    re_path(r'ws/', consumers.MainConsumer.as_asgi()),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += path("__debug__/", include(debug_toolbar.urls)),
