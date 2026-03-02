from django.urls import path
from .views import HomeView, ReservaView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('reserva/', ReservaView.as_view(), name='reserva'),
]
