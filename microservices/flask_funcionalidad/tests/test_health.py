import unittest

from app import create_app


class FuncionalidadHealthTestCase(unittest.TestCase):
	def setUp(self) -> None:
		self.client = create_app({"TESTING": True}).test_client()

	def test_health_endpoint(self) -> None:
		response = self.client.get("/api/v2/funcionalidad/health")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.get_json()["status"], "ok")

	def test_notification_endpoint(self) -> None:
		response = self.client.post(
			"/api/v2/funcionalidad/notificaciones/reserva",
			json={
				"canal": "email",
				"destinatario": "maria@example.com",
				"nombre_cliente": "Maria Garcia",
				"codigo_reserva": "A3F7B2C9",
				"fecha_reserva": "2026-04-13",
				"hora_inicio": "10:00:00",
				"hora_fin": "11:00:00",
				"nombres_servicios": ["Corte", "Peinado"],
				"precio_total": "45.00",
			},
		)
		self.assertEqual(response.status_code, 202)
		self.assertEqual(response.get_json()["status"], "enviada")

	def test_notification_endpoint_returns_structured_400(self) -> None:
		response = self.client.post(
			"/api/v2/funcionalidad/notificaciones/reserva",
			json={
				"canal": "email",
				"destinatario": "maria@example.com",
				"nombre_cliente": "Maria Garcia",
				"codigo_reserva": "A3F7B2C9",
				"fecha_reserva": "2026-04-13",
				"hora_inicio": "10:00:00",
				"hora_fin": "11:00:00",
				"precio_total": "45.00",
			},
		)
		payload = response.get_json()
		self.assertEqual(response.status_code, 400)
		self.assertEqual(payload["error"]["code"], "BAD_REQUEST")
		self.assertIn("nombres_servicios", payload["error"]["errors"])

	def test_notification_endpoint_returns_structured_500(self) -> None:
		app = create_app({"TESTING": True, "PROPAGATE_EXCEPTIONS": False})

		@app.route("/boom")
		def boom():
			raise RuntimeError("boom")

		client = app.test_client()
		response = client.get("/boom")
		payload = response.get_json()
		self.assertEqual(response.status_code, 500)
		self.assertEqual(payload["error"]["code"], "INTERNAL_SERVER_ERROR")