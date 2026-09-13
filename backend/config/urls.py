from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("api/health/", lambda request: JsonResponse({"status": "ok"}), name="health"),
    path("admin/", admin.site.urls),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/admin/", include("apps.accounts.admin_urls")),
    path("api/", include("apps.ingredients.urls")),
    path("api/", include("apps.recipes.urls")),
    path("api/", include("apps.planning.urls")),
    path("api/", include("apps.shopping.urls")),
    path("api/", include("apps.importer.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
