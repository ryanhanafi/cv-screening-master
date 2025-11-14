from django.urls import path
from .views import UploadView, EvaluateView, ResultView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('upload/', UploadView.as_view(), name='upload'),
    path('evaluate/', EvaluateView.as_view(), name='evaluate'),
    path('result/<str:job_id>/', ResultView.as_view(), name='result'),
]
