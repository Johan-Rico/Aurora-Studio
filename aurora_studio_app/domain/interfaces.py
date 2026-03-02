from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, time
from decimal import Decimal
from typing import Optional

# TYPE_CHECKING import para evitar imports circulares
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from aurora_studio_app.models import Servicio, Cliente, Reserva, Disponibilidad, DetalleCita


# ========== INTERFACES DE NOTIFICACIÓN ==========

class EnviadorNotificacion(ABC):
	
	@abstractmethod
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
		raise NotImplementedError


class GeneradorCodigoReserva(ABC):
	
	@abstractmethod
	def generar(self) -> str:
		raise NotImplementedError


# ========== INTERFACES DE REPOSITORIOS ==========

class RepositorioServicio(ABC):
	"""Repositorio para operaciones con Servicio."""
	
	@abstractmethod
	def obtener_todos_ordenados_por_nombre(self) -> list[Servicio]:
		raise NotImplementedError
	
	@abstractmethod
	def obtener_por_id(self, servicio_id: int) -> Optional[Servicio]:
		raise NotImplementedError


class RepositorioCliente(ABC):
	"""Repositorio para operaciones con Cliente."""
	
	@abstractmethod
	def buscar_por_email(self, email: str) -> Optional[Cliente]:
		raise NotImplementedError
	
	@abstractmethod
	def crear(self, nombre: str, email: str, telefono: str) -> Cliente:
		raise NotImplementedError
	
	@abstractmethod
	def actualizar_telefono(self, cliente: Cliente, telefono: str) -> None:
		raise NotImplementedError


class RepositorioReserva(ABC):
	"""Repositorio para operaciones con Reserva."""

	@abstractmethod
	def guardar_reserva_con_detalles(self, reserva: Reserva, detalles: list[DetalleCita]) -> Reserva:
		raise NotImplementedError

	@abstractmethod
	def obtener_por_email_y_codigo(self, email: str, codigo_reserva: str) -> Optional[Reserva]:
		raise NotImplementedError
	
	@abstractmethod
	def buscar_por_fecha(self, fecha: date) -> list[Reserva]:
		raise NotImplementedError
	
	@abstractmethod
	def obtener_por_id(self, reserva_id: int) -> Optional[Reserva]:
		raise NotImplementedError
	
	@abstractmethod
	def eliminar(self, reserva: Reserva) -> None:
		raise NotImplementedError


class RepositorioDisponibilidad(ABC):
	"""Repositorio para operaciones con Disponibilidad."""
	
	@abstractmethod
	def obtener_por_dia_semana(self, dia_semana: int) -> Optional[Disponibilidad]:
		raise NotImplementedError

