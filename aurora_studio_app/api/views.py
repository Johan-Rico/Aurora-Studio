from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from aurora_studio_app.api.serializers import (
	DisponibilidadConsultaInputSerializer,
	DisponibilidadConsultaOutputSerializer,
	ReservaCancelacionCodigoInputSerializer,
	ReservaCreateInputSerializer,
	ReservaOutputSerializer,
	ServicioOutputSerializer,
)
from aurora_studio_app.infra.factories import FactoriaNotificacion
from aurora_studio_app.infra.repositories import (
	RepositorioClienteDjango,
	RepositorioDisponibilidadDjango,
	RepositorioReservaDjango,
	RepositorioServicioDjango,
)
from aurora_studio_app.infra.servicios import GeneradorCodigoReservaUUID
from aurora_studio_app.services import (
	ClienteService,
	DisponibilidadService,
	ReservaService,
	ServicioService,
)


def _build_reserva_service() -> ReservaService:
	repo_servicio = RepositorioServicioDjango()
	repo_cliente = RepositorioClienteDjango()
	repo_reserva = RepositorioReservaDjango()
	repo_disponibilidad = RepositorioDisponibilidadDjango()

	servicio_service = ServicioService(repositorio_servicio=repo_servicio)
	cliente_service = ClienteService(repositorio_cliente=repo_cliente)
	disponibilidad_service = DisponibilidadService(
		repositorio_reserva=repo_reserva,
		repositorio_disponibilidad=repo_disponibilidad,
	)

	return ReservaService(
		cliente_service=cliente_service,
		servicio_service=servicio_service,
		disponibilidad_service=disponibilidad_service,
		repositorio_reserva=repo_reserva,
		enviador_notificacion=FactoriaNotificacion.crear_enviador(),
		generador_codigo=GeneradorCodigoReservaUUID(),
	)


class ServicioListAPIView(APIView):
	def get(self, request):
		repo_servicio = RepositorioServicioDjango()
		servicio_service = ServicioService(repositorio_servicio=repo_servicio)
		servicios = servicio_service.listar_servicios_activos()
		data = ServicioOutputSerializer(servicios, many=True).data
		return Response(data, status=status.HTTP_200_OK)


class ReservaCreateAPIView(APIView):
	def post(self, request):
		serializer = ReservaCreateInputSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		reserva_service = _build_reserva_service()

		try:
			reserva = reserva_service.crear_reserva_completa(serializer.validated_data)
			output = ReservaOutputSerializer(reserva).data
			return Response(output, status=status.HTTP_201_CREATED)
		except ValueError as exc:
			message = str(exc).lower()
			if "no existe" in message:
				return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
			if "ocupado" in message or "fuera del horario" in message:
				return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


class DisponibilidadFechaAPIView(APIView):
	def get(self, request):
		serializer = DisponibilidadConsultaInputSerializer(data=request.query_params)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		repo_reserva = RepositorioReservaDjango()
		repo_disponibilidad = RepositorioDisponibilidadDjango()
		disponibilidad_service = DisponibilidadService(
			repositorio_reserva=repo_reserva,
			repositorio_disponibilidad=repo_disponibilidad,
		)

		try:
			horarios = disponibilidad_service.consultar_horarios_disponibles(
				fecha=serializer.validated_data["fecha"],
				duracion_horas=serializer.validated_data["duracion_horas"],
			)
		except ValueError as exc:
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

		payload = {
			"fecha": serializer.validated_data["fecha"],
			"duracion_horas": serializer.validated_data["duracion_horas"],
			"horarios_disponibles": horarios,
		}
		output = DisponibilidadConsultaOutputSerializer(payload)
		return Response(output.data, status=status.HTTP_200_OK)


class ReservaCancelByCodeAPIView(APIView):
	def post(self, request):
		serializer = ReservaCancelacionCodigoInputSerializer(data=request.data)
		if not serializer.is_valid():
			return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		reserva_service = _build_reserva_service()

		try:
			reserva_service.cancelar_reserva_por_codigo(
				email=serializer.validated_data["email"],
				codigo_reserva=serializer.validated_data["codigo"],
			)
			return Response(status=status.HTTP_204_NO_CONTENT)
		except ValueError as exc:
			message = str(exc).lower()
			if "no existe" in message:
				return Response({"detail": str(exc)}, status=status.HTTP_404_NOT_FOUND)
			if "no se pueden cancelar reservas pasadas" in message:
				return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
			return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
