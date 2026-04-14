from __future__ import annotations

from typing import Optional
from django.conf import settings

from aurora_studio_app.domain.interfaces import EnviadorNotificacion
from aurora_studio_app.infra.servicios import (
	EnviadorNotificacionFlask,
	EnviadorNotificacionMock,
)


class FactoriaNotificacion:
	"""Factory para crear instancias de EnviadorNotificacion."""
	
	@staticmethod
	def crear_enviador(tipo: Optional[str] = None) -> EnviadorNotificacion:
     
		# Si no se especifica tipo, usar la configuración de settings
		if tipo is None:
			tipo = getattr(settings, 'NOTIFICATION_SENDER', 'mock')
		
		tipo = tipo.lower()
		
		if tipo in {"flask", "http", "email"}:
			return EnviadorNotificacionFlask()
		elif tipo == "mock":
			return EnviadorNotificacionMock()
		else:
			raise ValueError(
				f"Tipo de notificación '{tipo}' no válido. Use 'flask' o 'mock'."
			)
