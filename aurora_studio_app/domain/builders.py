from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from aurora_studio_app.models import Cliente, DetalleCita, Reserva, Servicio

from .interfaces import GeneradorCodigoReserva


class ErrorConstructorReserva(Exception):
	"""Excepción personalizada para errores en el constructor de reservas."""
	pass


class ConstructorReserva:
	"""Constructor para crear reservas de citas con validaciones."""
	
	def __init__(self, generador_codigo: GeneradorCodigoReserva | None = None) -> None:
		self._generador_codigo = generador_codigo
		self.reiniciar()

	def reiniciar(self) -> ConstructorReserva:
		"""Reinicia todos los atributos del constructor."""
		self._cliente: Cliente | None = None
		self._fecha: date | None = None
		self._hora_inicio: time | None = None
		self._servicios: list[Servicio] = []
		return self

	def para_cliente(self, cliente: Cliente) -> ConstructorReserva:
		self._cliente = cliente
		return self

	def para_fecha_hora(self, fecha_reserva: date, hora_inicio: time) -> ConstructorReserva:
		self._fecha = fecha_reserva
		self._hora_inicio = hora_inicio
		return self

	def agregar_servicio(self, servicio: Servicio) -> ConstructorReserva:
		self._servicios.append(servicio)
		return self

	def agregar_servicios(self, servicios: list[Servicio]) -> ConstructorReserva:
		self._servicios.extend(servicios)
		return self

	def construir(self) -> Reserva:
		"""Construye y guarda la reserva con sus detalles."""
		
		# 1. Validar campos requeridos
		self._validar_campos_requeridos()

		# 2. Calcular duración y hora de fin
		minutos_totales = self._calcular_minutos_totales(self._servicios)
		hora_fin = self._calcular_hora_fin(self._fecha, self._hora_inicio, minutos_totales)

		# 3. Crear y guardar la reserva
		reserva = Reserva.objects.create(
			cliente=self._cliente,
			fecha=self._fecha,
			hora_inicio=self._hora_inicio,
			hora_fin=hora_fin,
			tipo="cita",
		)

		# 4. Crear y guardar los detalles
		for servicio in self._servicios:
			DetalleCita.objects.create(
				reserva=reserva,
				servicio=servicio,
				precio_aplicado=servicio.precio,
			)

		# 5. Reiniciar el constructor para poder reutilizarlo
		self.reiniciar()

		# 6. Retornar la reserva creada
		return reserva

	def _validar_campos_requeridos(self) -> None:
		if self._cliente is None:
			raise ErrorConstructorReserva("El cliente es obligatorio para construir una reserva")
		if self._fecha is None:
			raise ErrorConstructorReserva("La fecha es obligatoria para construir una reserva")
		if self._hora_inicio is None:
			raise ErrorConstructorReserva("La hora de inicio es obligatoria para construir una reserva")
		if not self._servicios:
			raise ErrorConstructorReserva("Debe seleccionar al menos un servicio")

	@staticmethod
	def _calcular_minutos_totales(servicios: list[Servicio]) -> int:
		minutos_totales = 0
		for servicio in servicios:
			horas_duracion = Decimal(servicio.duracion)
			minutos = int(horas_duracion * Decimal("60"))
			if minutos <= 0:
				raise ErrorConstructorReserva(
					f"El servicio '{servicio.nombre}' tiene una duración inválida"
				)
			minutos_totales += minutos
		return minutos_totales

	@staticmethod
	def _calcular_hora_fin(fecha_reserva: date, hora_inicio: time, minutos: int) -> time:
		fecha_hora_inicio = datetime.combine(fecha_reserva, hora_inicio)
		fecha_hora_fin = fecha_hora_inicio + timedelta(minutes=minutos)
		if fecha_hora_fin.date() != fecha_reserva:
			raise ErrorConstructorReserva("La cita no puede terminar en un día distinto")
		return fecha_hora_fin.time()


class ConstructorBloqueoReserva:
	"""Constructor para crear bloqueos administrativos de horarios."""
	
	def __init__(self) -> None:
		self.reiniciar()

	def reiniciar(self) -> ConstructorBloqueoReserva:
		"""Reinicia todos los atributos del constructor."""
		self._fecha: date | None = None
		self._hora_inicio: time | None = None
		self._hora_fin: time | None = None
		return self

	def para_fecha(self, fecha_bloqueo: date) -> ConstructorBloqueoReserva:
		self._fecha = fecha_bloqueo
		return self

	def desde_hora(self, hora_inicio: time) -> ConstructorBloqueoReserva:
		self._hora_inicio = hora_inicio
		return self

	def hasta_hora(self, hora_fin: time) -> ConstructorBloqueoReserva:
		self._hora_fin = hora_fin
		return self

	def construir(self) -> Reserva:
		"""Construye y guarda el bloqueo de reserva."""
		
		# 1. Validar
		if self._fecha is None:
			raise ErrorConstructorReserva("La fecha del bloqueo es obligatoria")
		if self._hora_inicio is None or self._hora_fin is None:
			raise ErrorConstructorReserva("Debe definir hora de inicio y fin del bloqueo")
		if self._hora_inicio >= self._hora_fin:
			raise ErrorConstructorReserva("La hora de inicio del bloqueo debe ser menor a la hora fin")

		# 2. Crear y guardar
		reserva = Reserva.objects.create(
			fecha=self._fecha,
			hora_inicio=self._hora_inicio,
			hora_fin=self._hora_fin,
			tipo="bloqueo",
		)

		# 3. Reiniciar
		self.reiniciar()
		return reserva

