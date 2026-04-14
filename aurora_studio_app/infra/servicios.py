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
		except urllib_error.URLError as exc:
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
