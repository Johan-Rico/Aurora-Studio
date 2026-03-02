from django.urls import path

from .views import (
    DisponibilidadFechaAPIView,
    ReservaCancelByCodeAPIView,
    ReservaCreateAPIView,
    ServicioListAPIView,
)

urlpatterns = [
    path("servicios/", ServicioListAPIView.as_view(), name="api-servicios-list"),
    path("reservas/", ReservaCreateAPIView.as_view(), name="api-reservas-create"),
    path("reservas/cancel/", ReservaCancelByCodeAPIView.as_view(), name="api-reservas-cancel-by-code"),
    path("disponibilidad/", DisponibilidadFechaAPIView.as_view(), name="api-disponibilidad-fecha"),
]
