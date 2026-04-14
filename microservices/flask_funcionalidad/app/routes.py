from __future__ import annotations

from datetime import date, time
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request


funcionalidad_bp = Blueprint("funcionalidad", __name__)


class ApiError(ValueError):
	def __init__(self, detail: str, status_code: int = 400, errors: dict | None = None):
		super().__init__(detail)
		self.detail = detail
		self.status_code = status_code
		self.errors = errors or {}


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


@funcionalidad_bp.get("/health")
def health() -> tuple[dict, int]:
	return jsonify(status="ok", service="flask_funcionalidad"), 200


@funcionalidad_bp.errorhandler(ApiError)
def handle_api_error(exc: ApiError):
	payload = {
		"error": {
			"code": "BAD_REQUEST",
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
		if campo not in payload or payload[campo] in {None, "", []}:
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
	print(
		"\n".join(
			[
				"[flask_funcionalidad] notificacion recibida",
				f"canal={canal}",
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
