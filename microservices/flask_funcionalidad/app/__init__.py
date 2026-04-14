from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from .routes import ApiError, funcionalidad_bp


def create_app(config: dict | None = None) -> Flask:
	app = Flask(__name__)
	app.config.update(JSON_SORT_KEYS=False)

	if config:
		app.config.update(config)

	app.register_blueprint(funcionalidad_bp, url_prefix="/api/v2/funcionalidad")

	@app.errorhandler(ApiError)
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

	@app.errorhandler(HTTPException)
	def handle_http_exception(exc: HTTPException):
		return (
			jsonify(
				error={
					"code": exc.name.replace(" ", "_").upper(),
					"detail": exc.description,
				},
			),
			exc.code,
		)

	@app.errorhandler(Exception)
	def handle_unexpected_exception(exc: Exception):
		app.logger.exception("Unexpected error in notification microservice")
		return (
			jsonify(
				error={
					"code": "INTERNAL_SERVER_ERROR",
					"detail": "Ocurrió un error inesperado en el microservicio de notificaciones",
				},
			),
			500,
		)

	return app
