from typing import List, Dict, Optional
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from .models import Servicio, Cliente, Reserva, DetalleCita, Disponibilidad
from .domain.builders import ConstructorReserva, ErrorConstructorReserva
from .domain.interfaces import (
    EnviadorNotificacion,
    GeneradorCodigoReserva,
    RepositorioServicio,
    RepositorioCliente,
    RepositorioReserva,
    RepositorioDisponibilidad,
)


class ServicioService:
    """Servicio de aplicación para gestionar servicios del negocio."""
    
    def __init__(self, repositorio_servicio: RepositorioServicio):
        self.repositorio = repositorio_servicio
    
    def listar_servicios_activos(self) -> List[Servicio]:
        return self.repositorio.obtener_todos_ordenados_por_nombre()
    
    def obtener_servicio(self, servicio_id: int) -> Optional[Servicio]:
        servicio = self.repositorio.obtener_por_id(servicio_id)
        if servicio is None:
            raise ValueError(f"El servicio con ID {servicio_id} no existe")
        return servicio
    
    def calcular_duracion_total(self, servicios_ids: List[int]) -> Decimal:
        """Calcula la duración total de una lista de servicios."""
        duracion_total = Decimal('0')
        
        for servicio_id in servicios_ids:
            servicio = self.obtener_servicio(servicio_id)
            duracion_total += servicio.duracion
        
        return duracion_total


class ClienteService:
    """Servicio de aplicación para gestionar clientes."""
    
    def __init__(self, repositorio_cliente: RepositorioCliente):
        self.repositorio = repositorio_cliente
    
    def obtener_o_crear_cliente(self, nombre: str, email: str, telefono: str) -> Cliente:
        """Obtiene un cliente existente o crea uno nuevo."""
        
        # Validaciones
        if not nombre or not email or not telefono:
            raise ValueError("Todos los campos son requeridos: nombre, email, telefono")
        
        if '@' not in email:
            raise ValueError("Email inválido")
        
        # Buscar cliente existente
        cliente = self.repositorio.buscar_por_email(email)
        
        if cliente:
            # Actualizar teléfono si cambió
            if cliente.telefono != telefono:
                self.repositorio.actualizar_telefono(cliente, telefono)
            return cliente
        
        # Crear nuevo cliente
        return self.repositorio.crear(nombre, email, telefono)


class DisponibilidadService:
    """Servicio de aplicación para validar disponibilidad de horarios."""
    
    def __init__(
        self,
        repositorio_reserva: RepositorioReserva,
        repositorio_disponibilidad: RepositorioDisponibilidad
    ):
        self.repositorio_reserva = repositorio_reserva
        self.repositorio_disponibilidad = repositorio_disponibilidad
    
    def validar_horario_disponible(
        self, 
        fecha: date, 
        hora_inicio: time, 
        duracion_horas: Decimal
    ) -> bool:
        """Valida que un horario esté disponible para reservar."""
        
        # Validar que la fecha no sea pasada
        if fecha < date.today():
            raise ValueError("No se pueden hacer reservas en fechas pasadas")
        
        # Calcular hora de fin
        inicio_datetime = datetime.combine(fecha, hora_inicio)
        fin_datetime = inicio_datetime + timedelta(hours=float(duracion_horas))
        hora_fin = fin_datetime.time()
        
        # 1. Verificar que esté dentro del horario de atención
        if not self._esta_dentro_horario_atencion(fecha.weekday(), hora_inicio, hora_fin):
            raise ValueError("El horario solicitado está fuera del horario de atención")
        
        # 2. Verificar que no haya reservas solapadas
        if self._hay_reservas_solapadas(fecha, hora_inicio, hora_fin):
            raise ValueError("El horario seleccionado ya está ocupado")
        
        return True
    
    def _esta_dentro_horario_atencion(
        self, 
        dia_semana: int, 
        hora_inicio: time, 
        hora_fin: time
    ) -> bool:
        """Verifica si el horario está dentro del horario de atención configurado."""
        
        disponibilidad = self.repositorio_disponibilidad.obtener_por_dia_semana(dia_semana)
        
        if disponibilidad is None:
            # Si no hay disponibilidad configurada para ese día, no se puede reservar
            return False
        
        # Verificar que esté dentro del rango
        if hora_inicio < disponibilidad.hora_apertura or hora_fin > disponibilidad.hora_cierre:
            return False
        
        # Verificar horas bloqueadas
        hora_inicio_int = hora_inicio.hour
        hora_fin_int = hora_fin.hour
        
        for hora_bloqueada in disponibilidad.horas_bloqueadas:
            if hora_inicio_int <= hora_bloqueada < hora_fin_int:
                return False
        
        return True
    
    def _hay_reservas_solapadas(
        self, 
        fecha: date, 
        hora_inicio: time, 
        hora_fin: time
    ) -> bool:
        """Verifica si hay reservas que se solapan con el horario solicitado."""
        
        reservas_dia = self.repositorio_reserva.buscar_por_fecha(fecha)
        
        for reserva in reservas_dia:
            # Verificar solapamiento
            if not (hora_fin <= reserva.hora_inicio or hora_inicio >= reserva.hora_fin):
                return True
        
        return False


class ReservaService:
    """Servicio de aplicación para gestionar reservas (orquestador principal)."""
    
    def __init__(
        self,
        cliente_service: ClienteService,
        servicio_service: ServicioService,
        disponibilidad_service: DisponibilidadService,
        repositorio_reserva: RepositorioReserva,
        enviador_notificacion: EnviadorNotificacion = None,
        generador_codigo: GeneradorCodigoReserva = None
    ):
        self.cliente_service = cliente_service
        self.servicio_service = servicio_service
        self.disponibilidad_service = disponibilidad_service
        self.repositorio_reserva = repositorio_reserva
        self.enviador_notificacion = enviador_notificacion
        self.generador_codigo = generador_codigo
    
    def crear_reserva_completa(self, datos: Dict) -> Reserva:
        """Orquesta la creación completa de una reserva con todas las validaciones."""
        
        # 1. Validar datos básicos
        self._validar_datos_reserva(datos)
        
        # 2. Obtener o crear cliente
        cliente = self.cliente_service.obtener_o_crear_cliente(
            nombre=datos['nombre'],
            email=datos['email'],
            telefono=datos['telefono']
        )
        
        # 3. Calcular duración total de servicios
        duracion_total = self.servicio_service.calcular_duracion_total(
            datos['servicios_ids']
        )
        
        # 4. Validar disponibilidad
        self.disponibilidad_service.validar_horario_disponible(
            fecha=datos['fecha'],
            hora_inicio=datos['hora'],
            duracion_horas=duracion_total
        )
        
        # 5. Obtener servicios completos
        servicios = [self.servicio_service.obtener_servicio(sid) for sid in datos['servicios_ids']]
        
        # 6. Usar Builder para crear la reserva
        try:
            constructor = ConstructorReserva(generador_codigo=self.generador_codigo)
            reserva = (
                constructor
                .para_cliente(cliente)
                .para_fecha_hora(datos['fecha'], datos['hora'])
                .agregar_servicios(servicios)
                .construir()
            )
            # El constructor ya guardó la reserva y los detalles en DB
            
        except ErrorConstructorReserva as e:
            raise ValueError(f"Error al construir la reserva: {str(e)}")
        
        # 7. Enviar notificación usando EnviadorNotificacion
        if self.enviador_notificacion:
            # Calcular precio total
            precio_total = sum(s.precio for s in servicios)
            nombres_servicios = [s.nombre for s in servicios]
            
            # Generar código
            codigo_reserva = self.generador_codigo.generar() if self.generador_codigo else str(reserva.id)
            
            self.enviador_notificacion.enviar_confirmacion_reserva(
                correo_destino=cliente.email,
                nombre_cliente=cliente.nombre,
                codigo_reserva=codigo_reserva,
                fecha_reserva=reserva.fecha,
                hora_inicio=reserva.hora_inicio,
                hora_fin=reserva.hora_fin,
                nombres_servicios=nombres_servicios,
                precio_total=precio_total
            )
        
        return reserva
    
    def _validar_datos_reserva(self, datos: Dict) -> None:
        """Valida que los datos de reserva sean correctos."""
        
        campos_requeridos = ['nombre', 'email', 'telefono', 'fecha', 'hora', 'servicios_ids']
        
        for campo in campos_requeridos:
            if campo not in datos or not datos[campo]:
                raise ValueError(f"El campo '{campo}' es requerido")
        
        if not isinstance(datos['servicios_ids'], list) or len(datos['servicios_ids']) == 0:
            raise ValueError("Debe seleccionar al menos un servicio")
    
    def cancelar_reserva(self, reserva_id: int) -> None:
        """Cancela una reserva existente."""
        
        reserva = self.repositorio_reserva.obtener_por_id(reserva_id)
        
        if reserva is None:
            raise ValueError(f"La reserva con ID {reserva_id} no existe")
        
        # Validar que se pueda cancelar
        if reserva.fecha < date.today():
            raise ValueError("No se pueden cancelar reservas pasadas")
        
        # Eliminar la reserva
        self.repositorio_reserva.eliminar(reserva)
