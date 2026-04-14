from django.urls import path
from django.urls import include
from .views import HomeView, ReservaView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('reserva/', ReservaView.as_view(), name='reserva'),
    path('api/v1/', include('aurora_studio_app.api.urls')),
    path('api/', include('aurora_studio_app.api.urls')),
]
