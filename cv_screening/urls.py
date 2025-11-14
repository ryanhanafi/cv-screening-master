from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import custom_404_view, home_view, login_view, upload_cv_view, evaluation_result_view

urlpatterns = [
    path("", home_view, name="home"),
    path("login/", login_view, name="login"),
    path("upload/", upload_cv_view, name="upload"),
    path("evaluation/<int:evaluation_id>/", evaluation_result_view, name="evaluation_result"),
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = custom_404_view
