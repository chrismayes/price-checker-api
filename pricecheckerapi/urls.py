from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from groceriespricechecker.views import CustomTokenObtainPairView, contact_us, signup_view
from groceriespricechecker.serializers import CustomTokenObtainPairSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/contact-us/', contact_us, name='contact_us'),
    path('api/signup/', signup_view, name='signup'),
    path('api/', include('groceriespricechecker.urls')),  # All API endpoints under /api/
]
