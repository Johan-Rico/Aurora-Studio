from __future__ import annotations

from datetime import date, time
from decimal import Decimal
import json
from urllib.parse import quote_plus
from urllib import error as urllib_error
from urllib import request as urllib_request
import uuid

from django.conf import settings

from aurora_studio_app.domain.interfaces import EnviadorNotificacion, GeneradorCodigoReserva, UbicacionLocal


class UbicacionLocalGoogleMapsAdapter(UbicacionLocal):
	def __init__(self, direccion: str | None = None):
		self.direccion = direccion or getattr(settings, "BUSINESS_ADDRESS", "Cll 63 Sur #43 a12 local Torre Alcántara")

	def obtener_direccion(self) -> str:
		return self.direccion

	def obtener_url_mapa(self) -> str:
		return getattr(
			settings,
			"BUSINESS_MAPS_EMBED_URL",
			f"https://www.google.com/maps?q={quote_plus(self.direccion)}&output=embed",
		)

	def obtener_url_ruta(self) -> str:
		return getattr(
			settings,
			"BUSINESS_MAPS_DIRECTIONS_URL",
			f"https://www.google.com/maps/search/?api=1&query={quote_plus(self.direccion)}",
		)


class ExternalMotosAdapter:
	"""Adaptador para consumir la API externa de motos proporcionada por otro equipo.

	Soporta listar motos con filtros `categoria` y `q` (búsqueda por modelo).
	Usa el header `X-API-Key` según la especificación.
	"""

	def __init__(self, base_url: str | None = None, api_key: str | None = None, timeout_seconds: float = 8.0):
		self.base_url = base_url or getattr(settings, 'EXTERNAL_MOTOS_BASE_URL', 'http://52.54.140.72/api/public/v1/motos/')
		if not self.base_url.endswith('/'):
			self.base_url = f"{self.base_url}/"
		self.api_key = api_key or getattr(settings, 'EXTERNAL_MOTOS_API_KEY', 'yamaha-grupo-2026')
		self.timeout_seconds = timeout_seconds

	def listar_motos(self, *, categoria: str | None = None, q: str | None = None) -> list[dict]:
		# Construir query string simple
		params = []
		if categoria:
			params.append(f"categoria={quote_plus(str(categoria))}")
		if q:
			params.append(f"q={quote_plus(str(q))}")
		query = f"?{'&'.join(params)}" if params else ""

		url = f"{self.base_url}{query}"

		req = urllib_request.Request(url=url, method='GET')
		# Header de autenticación requerido por el otro equipo
		req.add_header('X-API-Key', self.api_key)

		try:
			with urllib_request.urlopen(req, timeout=self.timeout_seconds) as resp:
				if resp.status != 200:
					raise RuntimeError(f"API externa respondió con estado {resp.status}")
				body = resp.read().decode('utf-8')
				try:
					return json.loads(body)
				except (json.JSONDecodeError, ValueError) as exc:
					raise RuntimeError(f"La API externa respondió un cuerpo no JSON: {body[:200]}") from exc
		except urllib_error.HTTPError as exc:
			body = exc.read().decode('utf-8', errors='replace')
			raise RuntimeError(f"Error HTTP al consultar API externa: {exc.code} {body}") from exc
		except (urllib_error.URLError, OSError) as exc:
			raise RuntimeError("No se pudo conectar con la API externa de motos") from exc
		except Exception as exc:
			raise RuntimeError(f"Error inesperado al consultar la API externa de motos: {exc}") from exc


class EnviadorNotificacionTercero(EnviadorNotificacion):
	"""Adaptador para enviar notificaciones a un proveedor externo (tercero).

	Usa `NOTIFICATIONS_THIRD_PARTY_URL` desde `settings` si está presente; si no,
	intenta derivar una URL destino a partir de `NOTIFICATIONS_SERVICE_URL`.
	"""

	def __init__(self, base_url: str | None = None, timeout_seconds: float = 8.0):
		self.base_url = (
			base_url
			or getattr(settings, "NOTIFICATIONS_THIRD_PARTY_URL", None)
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
		# Payload simplificado que muchos proveedores entienden
		payload = {
			"type": "reservation.confirmation",
			"recipient": correo_destino,
			"client_name": nombre_cliente,
			"reservation_code": codigo_reserva,
			"date": fecha_reserva.isoformat(),
			"start_time": hora_inicio.isoformat(),
			"end_time": hora_fin.isoformat(),
			"items": nombres_servicios,
			"amount": str(precio_total),
		}

		solicitud = urllib_request.Request(
			url=f"{self.base_url}/external/notifications",
			data=json.dumps(payload).encode("utf-8"),
			headers={"Content-Type": "application/json"},
			method="POST",
		)

		try:
			with urllib_request.urlopen(solicitud, timeout=self.timeout_seconds) as response:
				if response.status not in {200, 201, 202, 204}:
					raise RuntimeError(f"Proveedor tercero respondió con estado {response.status}")
		except urllib_error.HTTPError as exc:
			body = exc.read().decode("utf-8", errors="replace")
			raise RuntimeError(f"Error HTTP del proveedor tercero: {exc.code} {body}") from exc
		except (urllib_error.URLError, OSError) as exc:
			raise RuntimeError("No se pudo conectar con el proveedor de notificaciones tercero") from exc


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
