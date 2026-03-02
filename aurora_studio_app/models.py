from django.db import models
from django.core.validators import EmailValidator, RegexValidator


class Usuario(models.Model):
    """Usuario base del sistema."""
    nombre = models.CharField(max_length=200)
    email = models.EmailField(unique=True, validators=[EmailValidator()])

    class Meta:
        verbose_name_plural = "Usuarios"

    def __str__(self) -> str:
        return f"{self.nombre} - {self.email}"


class Cliente(Usuario):
    """Cliente que realiza reservas."""
    telefono = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Número de teléfono inválido")]
    )

    class Meta:
        verbose_name_plural = "Clientes"

    def __str__(self) -> str:
        return f"Cliente: {self.nombre} - {self.telefono}"


class Servicio(models.Model):
    """Servicios ofrecidos por el negocio."""
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        help_text="Duración del servicio en horas"
    )

    def __str__(self) -> str:
        return f"{self.nombre} - ${self.precio} ({self.duracion}h)"


class Reserva(models.Model):
    """Representa un bloque de tiempo ocupado (cita o bloqueo administrativo)."""
    TIPO_CHOICES = [
        ('cita', 'Cita'),
        ('bloqueo', 'Bloqueo Administrativo'),
    ]
    
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='reservas',
        null=True,
        blank=True,
        help_text="Cliente que hace la reserva (null para bloqueos administrativos)"
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='cita')

    class Meta:
        ordering = ['fecha', 'hora_inicio']
        verbose_name_plural = "Reservas"

    def __str__(self) -> str:
        cliente_info = f" - {self.cliente.nombre}" if self.cliente else ""
        return f"{self.get_tipo_display()} - {self.fecha} {self.hora_inicio}-{self.hora_fin}{cliente_info}"


class DetalleCita(models.Model):
    """Tabla intermedia: relación muchos a muchos entre Servicio y Reserva."""
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name="detalles")
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name="detalles")
    precio_aplicado = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Precio del servicio en el momento de la reserva"
    )

    class Meta:
        verbose_name_plural = "Detalles de Citas"

    def __str__(self) -> str:
        return f"{self.servicio.nombre} en {self.reserva}"


class Disponibilidad(models.Model):
    """Define horarios de atención por día de la semana."""
    DIAS_SEMANA = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_apertura = models.TimeField()
    hora_cierre = models.TimeField()
    horas_bloqueadas = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de horas bloqueadas en formato [9, 10, 14] representando las 9:00, 10:00, 14:00"
    )

    class Meta:
        ordering = ['dia_semana', 'hora_apertura']
        verbose_name_plural = "Disponibilidades"

    def __str__(self) -> str:
        return f"{self.get_dia_semana_display()}: {self.hora_apertura} - {self.hora_cierre}"

