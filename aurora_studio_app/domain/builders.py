from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from aurora_studio_app.models import Cliente, DetalleCita, Reserva, Servicio

from .interfaces import ReservationCodeGenerator


class ReservationBuilderError(ValueError):
	pass


@dataclass(frozen=True)
class ReservationBuildResult:
	reservation: Reserva
	details: list[DetalleCita]
	total_price: Decimal
	total_minutes: int
	reservation_code: str | None


class ReservationBuilder:
	def __init__(self, code_generator: ReservationCodeGenerator | None = None) -> None:
		self._code_generator = code_generator
		self._client: Cliente | None = None
		self._date: date | None = None
		self._start_time: time | None = None
		self._services: list[Servicio] = []

	def for_client(self, client: Cliente) -> ReservationBuilder:
		self._client = client
		return self

	def for_datetime(self, booking_date: date, start_time: time) -> ReservationBuilder:
		self._date = booking_date
		self._start_time = start_time
		return self

	def with_service(self, service: Servicio) -> ReservationBuilder:
		self._services.append(service)
		return self

	def with_services(self, services: list[Servicio]) -> ReservationBuilder:
		self._services.extend(services)
		return self

	def build(self) -> ReservationBuildResult:
		self._validate_required_fields()

		total_minutes = self._calculate_total_minutes(self._services)
		total_price = self._calculate_total_price(self._services)
		end_time = self._calculate_end_time(self._date, self._start_time, total_minutes)

		reservation = Reserva(
			fecha=self._date,
			hora_inicio=self._start_time,
			hora_fin=end_time,
			tipo="cita",
		)

		details = [
			DetalleCita(
				reserva=reservation,
				servicio=service,
				precio_aplicado=service.precio,
			)
			for service in self._services
		]

		reservation_code = self._code_generator.generate() if self._code_generator else None

		return ReservationBuildResult(
			reservation=reservation,
			details=details,
			total_price=total_price,
			total_minutes=total_minutes,
			reservation_code=reservation_code,
		)

	def _validate_required_fields(self) -> None:
		if self._client is None:
			raise ReservationBuilderError("El cliente es obligatorio para construir una reserva")
		if self._date is None:
			raise ReservationBuilderError("La fecha es obligatoria para construir una reserva")
		if self._start_time is None:
			raise ReservationBuilderError("La hora de inicio es obligatoria para construir una reserva")
		if not self._services:
			raise ReservationBuilderError("Debe seleccionar al menos un servicio")

	@staticmethod
	def _calculate_total_minutes(services: list[Servicio]) -> int:
		total_minutes = 0
		for service in services:
			duration_hours = Decimal(service.duracion)
			minutes = int(duration_hours * Decimal("60"))
			if minutes <= 0:
				raise ReservationBuilderError(
					f"El servicio '{service.nombre}' tiene una duración inválida"
				)
			total_minutes += minutes
		return total_minutes

	@staticmethod
	def _calculate_total_price(services: list[Servicio]) -> Decimal:
		total = Decimal("0")
		for service in services:
			total += Decimal(service.precio)
		return total

	@staticmethod
	def _calculate_end_time(booking_date: date, start_time: time, minutes: int) -> time:
		start_dt = datetime.combine(booking_date, start_time)
		end_dt = start_dt + timedelta(minutes=minutes)
		if end_dt.date() != booking_date:
			raise ReservationBuilderError("La cita no puede terminar en un día distinto")
		return end_dt.time()


class BlockReservationBuilder:
	def __init__(self) -> None:
		self._date: date | None = None
		self._start_time: time | None = None
		self._end_time: time | None = None

	def for_date(self, block_date: date) -> BlockReservationBuilder:
		self._date = block_date
		return self

	def from_time(self, start_time: time) -> BlockReservationBuilder:
		self._start_time = start_time
		return self

	def to_time(self, end_time: time) -> BlockReservationBuilder:
		self._end_time = end_time
		return self

	def build(self) -> Reserva:
		if self._date is None:
			raise ReservationBuilderError("La fecha del bloqueo es obligatoria")
		if self._start_time is None or self._end_time is None:
			raise ReservationBuilderError("Debe definir hora de inicio y fin del bloqueo")
		if self._start_time >= self._end_time:
			raise ReservationBuilderError("La hora de inicio del bloqueo debe ser menor a la hora fin")

		return Reserva(
			fecha=self._date,
			hora_inicio=self._start_time,
			hora_fin=self._end_time,
			tipo="bloqueo",
		)

