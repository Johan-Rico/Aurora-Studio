from datetime import date, time
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from aurora_studio_app.infra.factories import FactoriaNotificacion
from aurora_studio_app.infra.servicios import EnviadorNotificacionFlask


class FactoriaNotificacionTestCase(TestCase):
	@override_settings(NOTIFICATION_SENDER="flask")
	def test_default_factory_returns_flask_sender(self) -> None:
		enviador = FactoriaNotificacion.crear_enviador()
		self.assertIsInstance(enviador, EnviadorNotificacionFlask)


class EnviadorNotificacionFlaskTestCase(TestCase):
	@override_settings(NOTIFICATIONS_SERVICE_URL="http://notifications:5001/api/v2/funcionalidad")
	@patch("aurora_studio_app.infra.servicios.urllib_request.urlopen")
	def test_envia_payload_json_al_microservicio(self, mock_urlopen: Mock) -> None:
		mock_response = SimpleNamespace(status=202)
		mock_urlopen.return_value.__enter__.return_value = mock_response

		enviador = EnviadorNotificacionFlask()
		enviador.enviar_confirmacion_reserva(
			correo_destino="maria@example.com",
			nombre_cliente="Maria Garcia",
			codigo_reserva="A3F7B2C9",
			fecha_reserva=date(2026, 4, 13),
			hora_inicio=time(10, 0),
			hora_fin=time(11, 0),
			nombres_servicios=["Corte", "Peinado"],
			precio_total=Decimal("45.00"),
		)

		self.assertTrue(mock_urlopen.called)
		solicitud = mock_urlopen.call_args.args[0]
		self.assertEqual(solicitud.full_url, "http://notifications:5001/api/v2/funcionalidad/notificaciones/reserva")
		self.assertEqual(solicitud.get_header("Content-Type"), "application/json")

		import json

		payload = json.loads(solicitud.data.decode("utf-8"))
		self.assertEqual(payload["canal"], "email")
		self.assertEqual(payload["destinatario"], "maria@example.com")
		self.assertEqual(payload["codigo_reserva"], "A3F7B2C9")
		self.assertEqual(payload["nombres_servicios"], ["Corte", "Peinado"])

	@override_settings(NOTIFICATIONS_SERVICE_URL="http://notifications:5001/api/v2/funcionalidad")
	@patch("aurora_studio_app.infra.servicios.urllib_request.urlopen", side_effect=OSError("network down"))
	def test_lanza_error_claro_si_el_microservicio_no_responde(self, mock_urlopen: Mock) -> None:
		enviador = EnviadorNotificacionFlask()

		with self.assertRaises(RuntimeError) as context:
			enviador.enviar_confirmacion_reserva(
				correo_destino="maria@example.com",
				nombre_cliente="Maria Garcia",
				codigo_reserva="A3F7B2C9",
				fecha_reserva=date(2026, 4, 13),
				hora_inicio=time(10, 0),
				hora_fin=time(11, 0),
				nombres_servicios=["Corte"],
				precio_total=Decimal("45.00"),
			)

		self.assertIn("No se pudo conectar", str(context.exception))
		self.assertTrue(mock_urlopen.called)
