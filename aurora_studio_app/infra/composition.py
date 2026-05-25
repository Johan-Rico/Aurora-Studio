from __future__ import annotations

from aurora_studio_app.infra.factories import FactoriaNotificacion
from aurora_studio_app.infra.repositories import (
	RepositorioClienteDjango,
	RepositorioDisponibilidadDjango,
	RepositorioReservaDjango,
	RepositorioServicioDjango,
)
from aurora_studio_app.infra.servicios import ExternalMotosAdapter, GeneradorCodigoReservaUUID, UbicacionLocalGoogleMapsAdapter
from aurora_studio_app.services import (
	ClienteService,
	DisponibilidadService,
	ReservaService,
	ServicioService,
)


def build_servicio_service() -> ServicioService:
	return ServicioService(repositorio_servicio=RepositorioServicioDjango())


def build_disponibilidad_service() -> DisponibilidadService:
	repo_reserva = RepositorioReservaDjango()
	return DisponibilidadService(
		repositorio_reserva=repo_reserva,
		repositorio_disponibilidad=RepositorioDisponibilidadDjango(),
	)


def build_reserva_service() -> ReservaService:
	repo_servicio = RepositorioServicioDjango()
	repo_cliente = RepositorioClienteDjango()
	repo_reserva = RepositorioReservaDjango()

	servicio_service = ServicioService(repositorio_servicio=repo_servicio)
	cliente_service = ClienteService(repositorio_cliente=repo_cliente)
	disponibilidad_service = DisponibilidadService(
		repositorio_reserva=repo_reserva,
		repositorio_disponibilidad=RepositorioDisponibilidadDjango(),
	)

	return ReservaService(
		cliente_service=cliente_service,
		servicio_service=servicio_service,
		disponibilidad_service=disponibilidad_service,
		repositorio_reserva=repo_reserva,
		enviador_notificacion=FactoriaNotificacion.crear_enviador(),
		generador_codigo=GeneradorCodigoReservaUUID(),
	)


def build_motos_adapter() -> ExternalMotosAdapter:
	"""Factory simple para construir el adaptador de motos externas."""
	return ExternalMotosAdapter()


def build_ubicacion_local() -> UbicacionLocalGoogleMapsAdapter:
	"""Factory para la ubicación del local usando el adaptador de Google Maps."""
	return UbicacionLocalGoogleMapsAdapter()
