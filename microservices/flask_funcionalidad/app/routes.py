from __future__ import annotations

from datetime import date, time
from decimal import Decimal, InvalidOperation
from email.message import EmailMessage
import os
import smtplib

from flask import Blueprint, jsonify, request


funcionalidad_bp = Blueprint("funcionalidad", __name__)


class ApiError(ValueError):
	def __init__(
		self,
		detail: str,
		status_code: int = 400,
		errors: dict | None = None,
		code: str = "BAD_REQUEST",
	):
		super().__init__(detail)
		self.detail = detail
		self.status_code = status_code
		self.errors = errors or {}
		self.code = code


def _env_bool(name: str, default: bool = False) -> bool:
	value = os.getenv(name)
	if value is None:
		return default
	return value.strip().lower() in {"1", "true", "yes", "on"}


def _parse_date(value: str) -> date:
	try:
		return date.fromisoformat(value)
	except ValueError as exc:
		raise ApiError("'fecha_reserva' debe estar en formato YYYY-MM-DD") from exc


def _parse_time(value: str) -> time:
	try:
		return time.fromisoformat(value)
	except ValueError as exc:
		raise ApiError("'hora_inicio' y 'hora_fin' deben estar en formato HH:MM[:SS]") from exc


def _parse_decimal(value: str) -> Decimal:
	try:
		return Decimal(str(value))
	except (InvalidOperation, ValueError) as exc:
		raise ApiError("'precio_total' debe ser un número válido") from exc


def _build_message(payload: dict) -> str:
	servicios = "\n".join(f"- {servicio}" for servicio in payload["nombres_servicios"])
	return (
		f"Hola {payload['nombre_cliente']},\n\n"
		"Tu reserva ha sido confirmada.\n\n"
		f"Codigo: {payload['codigo_reserva']}\n"
		f"Fecha: {payload['fecha_reserva']}\n"
		f"Hora: {payload['hora_inicio']} - {payload['hora_fin']}\n\n"
		"Servicios:\n"
		f"{servicios}\n\n"
		f"Total: ${payload['precio_total']}"
	)


def _send_email_via_smtp(*, destinatario: str, asunto: str, mensaje: str) -> None:
	modo = os.getenv("NOTIFICATION_SENDER", "MOCK").strip().upper()
	if modo == "MOCK":
		print(
			"\n".join(
				[
					"[flask_funcionalidad][MOCK] email generado",
					f"to={destinatario}",
					f"subject={asunto}",
					mensaje,
				]
			)
		)
		return

	if modo != "SMTP":
		raise ApiError(
			"NOTIFICATION_SENDER debe ser MOCK o SMTP",
			status_code=500,
			code="MISCONFIGURED_NOTIFICATION_MODE",
		)

	host = os.getenv("SMTP_HOST", "").strip()
	port_raw = os.getenv("SMTP_PORT", "").strip()
	from_email = os.getenv("SMTP_FROM_EMAIL", "").strip()
	user = os.getenv("SMTP_USER", "").strip()
	password = os.getenv("SMTP_PASSWORD", "")
	use_tls = _env_bool("SMTP_USE_TLS", default=True)
	use_ssl = _env_bool("SMTP_USE_SSL", default=False)

	if not host or not port_raw or not from_email:
		raise ApiError(
			"Faltan variables SMTP_HOST, SMTP_PORT o SMTP_FROM_EMAIL",
			status_code=500,
			code="SMTP_CONFIGURATION_ERROR",
		)

	try:
		port = int(port_raw)
	except ValueError as exc:
		raise ApiError(
			"SMTP_PORT debe ser un entero válido",
			status_code=500,
			code="SMTP_CONFIGURATION_ERROR",
		) from exc

	email = EmailMessage()
	email["Subject"] = asunto
	email["From"] = from_email
	email["To"] = destinatario
	email.set_content(mensaje)

	try:
		if use_ssl:
			with smtplib.SMTP_SSL(host, port, timeout=20) as server:
				if user:
					server.login(user, password)
				server.send_message(email)
		else:
			with smtplib.SMTP(host, port, timeout=20) as server:
				if use_tls:
					server.starttls()
				if user:
					server.login(user, password)
				server.send_message(email)
	except Exception as exc:
		raise ApiError(
			"No se pudo enviar el correo de notificación",
			status_code=500,
			code="NOTIFICATION_DELIVERY_FAILED",
		) from exc


@funcionalidad_bp.get("/health")
def health() -> tuple[dict, int]:
	return jsonify(status="ok", service="flask_funcionalidad"), 200


@funcionalidad_bp.errorhandler(ApiError)
def handle_api_error(exc: ApiError):
	payload = {
		"error": {
			"code": exc.code,
			"detail": exc.detail,
		},
	}
	if exc.errors:
		payload["error"]["errors"] = exc.errors
	return jsonify(payload), exc.status_code


@funcionalidad_bp.post("/notificaciones/reserva")
def enviar_notificacion_reserva() -> tuple[dict, int]:
	payload = request.get_json(silent=True)
	if not isinstance(payload, dict):
		raise ApiError("El cuerpo debe ser JSON válido")

	campos_requeridos = [
		"canal",
		"destinatario",
		"nombre_cliente",
		"codigo_reserva",
		"fecha_reserva",
		"hora_inicio",
		"hora_fin",
		"nombres_servicios",
		"precio_total",
	]
	errores = {}

	for campo in campos_requeridos:
		valor = payload.get(campo)
		if valor is None:
			errores[campo] = "Este campo es requerido"
		elif isinstance(valor, str) and not valor.strip():
			errores[campo] = "Este campo es requerido"
		elif isinstance(valor, list) and not valor:
			errores[campo] = "Este campo es requerido"

	if errores:
		raise ApiError("Datos de notificación incompletos", errors=errores)

	canal = str(payload["canal"]).lower()
	if canal not in {"email", "whatsapp"}:
		raise ApiError("'canal' debe ser 'email' o 'whatsapp'")

	if not isinstance(payload["nombres_servicios"], list) or not payload["nombres_servicios"]:
		raise ApiError("'nombres_servicios' debe ser una lista no vacia")

	try:
		_parse_date(payload["fecha_reserva"])
		_parse_time(payload["hora_inicio"])
		_parse_time(payload["hora_fin"])
		_parse_decimal(payload["precio_total"])
	except ApiError:
		raise

	message = _build_message(payload)
	asunto = f"Confirmacion de reserva aurora ({payload['codigo_reserva']})"

	if canal == "email":
		_send_email_via_smtp(
			destinatario=payload["destinatario"],
			asunto=asunto,
			mensaje=message,
		)
	else:
		print(
			"\n".join(
				[
					"[flask_funcionalidad][MOCK] notificacion whatsapp",
					f"destinatario={payload['destinatario']}",
					message,
				]
			)
		)

	return (
		jsonify(
			status="enviada",
			canal=canal,
			destinatario=payload["destinatario"],
			mensaje=message,
		),
		202,
	)
