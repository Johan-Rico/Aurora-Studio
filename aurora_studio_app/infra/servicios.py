from __future__ import annotations

from datetime import date, time
from decimal import Decimal
import json
from urllib import error as urllib_error
from urllib import request as urllib_request
import uuid

from django.conf import settings

from aurora_studio_app.domain.interfaces import EnviadorNotificacion, GeneradorCodigoReserva


class EnviadorNotificacionFlask(EnviadorNotificacion):
	"""Implementación de EnviadorNotificacion que delega el envío al microservicio Flask."""

	def __init__(self, base_url: str | None = None, timeout_seconds: float = 8.0):
		self.base_url = (
			base_url
			or getattr(settings, "NOTIFICATIONS_SERVICE_URL", "http://localhost:5001/api/v2/funcionalidad")
		).rstrip("/")
		self.timeout_seconds = timeout_seconds

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
		payload = {
			"canal": "email",
			"destinatario": correo_destino,
			"nombre_cliente": nombre_cliente,
			"codigo_reserva": codigo_reserva,
			"fecha_reserva": fecha_reserva.isoformat(),
			"hora_inicio": hora_inicio.isoformat(),
			"hora_fin": hora_fin.isoformat(),
			"nombres_servicios": nombres_servicios,
			"precio_total": str(precio_total),
		}

		solicitud = urllib_request.Request(
			url=f"{self.base_url}/notificaciones/reserva",
			data=json.dumps(payload).encode("utf-8"),
			headers={"Content-Type": "application/json"},
			method="POST",
		)
		# asegurar que el header esté disponible también vía `get_header`
		solicitud.add_header("Content-Type", "application/json")
		
		# asegurar compatibilidad con distintas implementaciones: exponer
		# un `get_header` que consulte el diccionario interno de headers
		def _get_header(name: str, default=None):
			try:
				h = getattr(solicitud, 'headers', None) or getattr(solicitud, 'header_items', None)
				if isinstance(h, dict):
					return h.get(name) or h.get(name.lower()) or h.get(name.title()) or default
				# fallback: Request puede exponer header_items() como lista de tuplas
				if callable(getattr(solicitud, 'header_items', None)):
					for k, v in solicitud.header_items():
						if k.lower() == name.lower():
							return v
			except Exception:
				return default
			return default
		
		solicitud.get_header = _get_header

		# fallback directo: exponer un dict y header_items() por si la
		# implementación de Request los consulta directamente
		try:
			solicitud.headers = {"Content-Type": "application/json", "Content-type": "application/json"}
			def _header_items():
				return list(solicitud.headers.items())
			solicitud.header_items = _header_items
		except Exception:
			pass

		try:
			with urllib_request.urlopen(solicitud, timeout=self.timeout_seconds) as response:
				if response.status not in {200, 201, 202, 204}:
					raise RuntimeError(
						f"El microservicio de notificaciones respondió con estado {response.status}"
					)
		except urllib_error.HTTPError as exc:
			body = exc.read().decode("utf-8", errors="replace")
			raise RuntimeError(
				f"Error HTTP del microservicio de notificaciones: {exc.code} {body}"
			) from exc
		except (urllib_error.URLError, OSError) as exc:
			raise RuntimeError("No se pudo conectar con el microservicio de notificaciones") from exc


class EnviadorNotificacionMock(EnviadorNotificacion):
	"""Implementación de EnviadorNotificacion para pruebas (imprime en consola)."""
	
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
		"""
		Imprime la notificación en consola (para desarrollo/testing).
		"""
		print("\n" + "=" * 60)
		print("📧 NOTIFICACIÓN DE RESERVA (MODO DESARROLLO)")
		print("=" * 60)
		print(f"Para: {correo_destino}")
		print(f"Cliente: {nombre_cliente}")
		print(f"Código: {codigo_reserva}")
		print(f"Fecha: {fecha_reserva.strftime('%d/%m/%Y')}")
		print(f"Hora: {hora_inicio.strftime('%H:%M')} - {hora_fin.strftime('%H:%M')}")
		print(f"Servicios: {', '.join(nombres_servicios)}")
		print(f"Total: ${precio_total}")
		print("=" * 60 + "\n")


class GeneradorCodigoReservaUUID(GeneradorCodigoReserva):
	"""Implementación de GeneradorCodigoReserva usando UUID cortos."""
	
	def generar(self) -> str:
		"""
		Genera un código de reserva único usando UUID4 (versión corta).
		Formato: Primeros 8 caracteres del UUID en mayúsculas.
		Ejemplo: "A3F7B2C9"
		"""
		return str(uuid.uuid4()).replace('-', '').upper()[:8]


class EnviadorNotificacionCelery(EnviadorNotificacion):
	"""Enviador que encola la tarea Celery para envío de notificaciones.

	Esto permite delegar la entrega real (sincrónica) a la tarea, que a su vez
	usa la `FactoriaNotificacion` para realizar la llamada (manteniendo mocks
	y adaptadores existentes para pruebas y para SMTP/Flask).
	"""

	def enviar_confirmacion_reserva(
		self,
		*,
		correo_destino: str,
		nombre_cliente: str,
		codigo_reserva: str,
		fecha_reserva: date | str,
		hora_inicio: time | str,
		hora_fin: time | str,
		nombres_servicios: list[str],
		precio_total: Decimal | str,
	) -> None:
		# Import local to evitar ciclos en tiempo de import
		from aurora_studio_app.tasks import enviar_confirmacion_reserva_task

		# Normalizar a strings para serialización en Celery
		enviar_confirmacion_reserva_task.delay(
			correo_destino,
			nombre_cliente,
			codigo_reserva,
			getattr(fecha_reserva, 'isoformat', lambda: str(fecha_reserva))(),
			getattr(hora_inicio, 'isoformat', lambda: str(hora_inicio))(),
			getattr(hora_fin, 'isoformat', lambda: str(hora_fin))(),
			nombres_servicios,
			str(precio_total),
		)
