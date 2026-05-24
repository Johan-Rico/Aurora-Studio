from __future__ import annotations

from decimal import Decimal
from datetime import date, time
from types import SimpleNamespace

from aurora_studio_app.infra.factories import FactoriaNotificacion

# Intentar usar shared_task de Celery cuando esté disponible; si no,
# definir un decorador fallback que ejecuta la función sincrónicamente
try:
    from celery import shared_task
except Exception:  # pragma: no cover - celery may not be installed in test env
    def shared_task(*args, **kwargs):
        def _decorator(func):
            def _dummy_retry(exc=None):
                raise exc if exc else RuntimeError('Celery no está disponible')

            def wrapper(*f_args, **f_kwargs):
                return func(SimpleNamespace(retry=_dummy_retry), *f_args, **f_kwargs)

            # proporcionar `.delay` para compatibilidad con código que
            # encola tareas; en modo fallback, `.delay` ejecuta síncrono.
            wrapper.delay = lambda *a, **k: wrapper(*a, **k)
            return wrapper

        return _decorator


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def enviar_confirmacion_reserva_task(
    self,
    correo_destino: str,
    nombre_cliente: str,
    codigo_reserva: str,
    fecha_reserva: str,
    hora_inicio: str,
    hora_fin: str,
    nombres_servicios: list,
    precio_total: str,
):
    """Tarea Celery que delega envío de notificación al enviador configurado."""
    try:
        enviador = FactoriaNotificacion.crear_enviador()
        # Normalizar cadenas ISO a objetos date/time antes de llamar al enviador
        if isinstance(fecha_reserva, str):
            try:
                fecha_obj = date.fromisoformat(fecha_reserva)
            except Exception:
                fecha_obj = fecha_reserva
        else:
            fecha_obj = fecha_reserva

        if isinstance(hora_inicio, str):
            try:
                hora_inicio_obj = time.fromisoformat(hora_inicio)
            except Exception:
                hora_inicio_obj = hora_inicio
        else:
            hora_inicio_obj = hora_inicio

        if isinstance(hora_fin, str):
            try:
                hora_fin_obj = time.fromisoformat(hora_fin)
            except Exception:
                hora_fin_obj = hora_fin
        else:
            hora_fin_obj = hora_fin

        precio = Decimal(precio_total) if not isinstance(precio_total, Decimal) else precio_total

        enviador.enviar_confirmacion_reserva(
            correo_destino=correo_destino,
            nombre_cliente=nombre_cliente,
            codigo_reserva=codigo_reserva,
            fecha_reserva=fecha_obj,
            hora_inicio=hora_inicio_obj,
            hora_fin=hora_fin_obj,
            nombres_servicios=nombres_servicios,
            precio_total=precio,
        )
    except Exception as exc:  # pragma: no cover - retry on any failure
        # Si estamos en modo fallback (sin celery), `self` puede no exponer retry
        try:
            raise self.retry(exc=exc)
        except Exception:
            raise
