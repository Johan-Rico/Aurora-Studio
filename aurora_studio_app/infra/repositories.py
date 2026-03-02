from __future__ import annotations

from datetime import date
from typing import Optional

from aurora_studio_app.domain.interfaces import (
	RepositorioServicio,
	RepositorioCliente,
	RepositorioReserva,
	RepositorioDisponibilidad,
)
from aurora_studio_app.models import Servicio, Cliente, Reserva, Disponibilidad, Usuario, DetalleCita


class RepositorioServicioDjango(RepositorioServicio):
	"""Implementación de RepositorioServicio usando Django ORM."""
	
	def obtener_todos_ordenados_por_nombre(self) -> list[Servicio]:
		return list(Servicio.objects.all().order_by('nombre'))
	
	def obtener_por_id(self, servicio_id: int) -> Optional[Servicio]:
		try:
			return Servicio.objects.get(id=servicio_id)
		except Servicio.DoesNotExist:
			return None


class RepositorioClienteDjango(RepositorioCliente):
	"""Implementación de RepositorioCliente usando Django ORM."""
	
	def buscar_por_email(self, email: str) -> Optional[Cliente]:
		try:
			usuario = Usuario.objects.get(email=email)
			if hasattr(usuario, 'cliente'):
				return usuario.cliente
			return None
		except Usuario.DoesNotExist:
			return None
	
	def crear(self, nombre: str, email: str, telefono: str) -> Cliente:
		return Cliente.objects.create(
			nombre=nombre,
			email=email,
			telefono=telefono
		)
	
	def actualizar_telefono(self, cliente: Cliente, telefono: str) -> None:
		cliente.telefono = telefono
		cliente.save()


class RepositorioReservaDjango(RepositorioReserva):
	"""Implementación de RepositorioReserva usando Django ORM."""

	def guardar_reserva_con_detalles(self, reserva: Reserva, detalles: list[DetalleCita]) -> Reserva:
		reserva.save()
		for detalle in detalles:
			detalle.reserva = reserva
		DetalleCita.objects.bulk_create(detalles)
		return reserva

	def obtener_por_email_y_codigo(self, email: str, codigo_reserva: str) -> Optional[Reserva]:
		try:
			return Reserva.objects.select_related('cliente').get(
				cliente__email=email,
				codigo_reserva=codigo_reserva,
				tipo='cita',
			)
		except Reserva.DoesNotExist:
			return None
	
	def buscar_por_fecha(self, fecha: date) -> list[Reserva]:
		return list(Reserva.objects.filter(fecha=fecha))
	
	def obtener_por_id(self, reserva_id: int) -> Optional[Reserva]:
		try:
			return Reserva.objects.get(id=reserva_id)
		except Reserva.DoesNotExist:
			return None
	
	def eliminar(self, reserva: Reserva) -> None:
		reserva.delete()


class RepositorioDisponibilidadDjango(RepositorioDisponibilidad):
	"""Implementación de RepositorioDisponibilidad usando Django ORM."""
	
	def obtener_por_dia_semana(self, dia_semana: int) -> Optional[Disponibilidad]:
		try:
			return Disponibilidad.objects.get(dia_semana=dia_semana)
		except Disponibilidad.DoesNotExist:
			return None
