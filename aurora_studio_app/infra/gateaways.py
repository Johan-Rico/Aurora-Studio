from datetime import date, time
from decimal import Decimal

from ..domain.interfaces import EnviadorNotificacion


class EnviadorNotificacionConsola(EnviadorNotificacion):
    def enviar_confirmacion_reserva(
        self,
        *,
        correo_destino: str,
        nombre_cliente: str,
        codigo_reserva: str,
        fecha_reserva: date,
        hora_inicio: time,
        hora_fin: time,
        nombres_servicios: list[str],
        precio_total: Decimal,
    ) -> None:
        print(
            f"CONFIRMACION | to={correo_destino} | cliente={nombre_cliente} | "
            f"codigo={codigo_reserva} | fecha={fecha_reserva} | "
            f"hora={hora_inicio}-{hora_fin} | servicios={', '.join(nombres_servicios)} | "
            f"total={precio_total}"
        )