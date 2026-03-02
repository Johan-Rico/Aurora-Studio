from __future__ import annotations

from datetime import date, time
from decimal import Decimal
import uuid

from aurora_studio_app.domain.interfaces import EnviadorNotificacion, GeneradorCodigoReserva


class EnviadorNotificacionEmail(EnviadorNotificacion):
	"""Implementación de EnviadorNotificacion que envía emails reales."""
	
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
		Envía un email de confirmación de reserva usando Django Email.
		"""
		from django.core.mail import send_mail
		from django.conf import settings
		
		asunto = f"Confirmación de Reserva - Aurora Studio (Código: {codigo_reserva})"
		
		servicios_texto = "\n".join([f"  - {servicio}" for servicio in nombres_servicios])
		
		mensaje = f"""
Hola {nombre_cliente},

¡Tu reserva ha sido confirmada exitosamente!

Detalles de tu reserva:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Código de Reserva: {codigo_reserva}
Fecha: {fecha_reserva.strftime('%d/%m/%Y')}
Hora: {hora_inicio.strftime('%H:%M')} - {hora_fin.strftime('%H:%M')}

Servicios:
{servicios_texto}

Precio Total: ${precio_total}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Por favor, llega 10 minutos antes de tu cita.

Si necesitas cancelar o modificar tu reserva, contáctanos con anticipación.

¡Te esperamos!

Saludos,
Aurora Studio
"""
		
		send_mail(
			subject=asunto,
			message=mensaje,
			from_email=settings.DEFAULT_FROM_EMAIL,
			recipient_list=[correo_destino],
			fail_silently=False,
		)


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
