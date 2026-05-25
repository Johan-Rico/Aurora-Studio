from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, RegexValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class Usuario(models.Model):
    """Usuario base del sistema."""
    nombre = models.CharField(max_length=200)
    email = models.EmailField(unique=True, validators=[EmailValidator()])

    class Meta:
        verbose_name_plural = _("Usuarios")

    def __str__(self) -> str:
        return f"{self.nombre} - {self.email}"


class Cliente(Usuario):
    """Cliente que realiza reservas."""
    telefono = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Número de teléfono inválido")]
    )

    class Meta:
        verbose_name_plural = _("Clientes")

    def __str__(self) -> str:
        return f"Cliente: {self.nombre} - {self.telefono}"


class Servicio(models.Model):
    """Servicios ofrecidos por el negocio."""
    nombre = models.CharField(max_length=200)
    categoria = models.CharField(
        max_length=100,
        default="General",
        help_text=_("Categoría del servicio (ej: Uñas, Cejas, Pestañas, Facial)"),
    )
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion = models.DecimalField(
        max_digits=4, 
        decimal_places=2,
        help_text=_("Duración del servicio en horas")
    )

    def __str__(self) -> str:
        return f"[{self.categoria}] {self.nombre} - ${self.precio} ({self.duracion}h)"


class Reserva(models.Model):
    """Representa un bloque de tiempo ocupado (cita o bloqueo administrativo)."""
    TIPO_CHOICES = [
        ('cita', _("Cita")),
        ('bloqueo', _("Bloqueo Administrativo")),
    ]
    
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='reservas',
        null=True,
        blank=True,
        help_text=_("Cliente que hace la reserva (null para bloqueos administrativos)")
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    codigo_reserva = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text=_("Código único para que la clienta gestione su cita"),
    )
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='cita')

    class Meta:
        ordering = ['fecha', 'hora_inicio']
        verbose_name_plural = _("Reservas")

    def __str__(self) -> str:
        cliente_info = f" - {self.cliente.nombre}" if self.cliente else ""
        codigo_info = f" [{self.codigo_reserva}]" if self.codigo_reserva else ""
        return f"{self.get_tipo_display()} - {self.fecha} {self.hora_inicio}-{self.hora_fin}{cliente_info}{codigo_info}"


class DetalleCita(models.Model):
    """Tabla intermedia: relación muchos a muchos entre Servicio y Reserva."""
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name="detalles")
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE, related_name="detalles")
    precio_aplicado = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text=_("Precio del servicio en el momento de la reserva")
    )

    class Meta:
        verbose_name_plural = _("Detalles de Citas")

    def __str__(self) -> str:
        return f"{self.servicio.nombre} en {self.reserva}"


class Disponibilidad(models.Model):
    """Define horarios de atención por día de la semana."""
    DIAS_SEMANA = [
        (0, _("Lunes")),
        (1, _("Martes")),
        (2, _("Miércoles")),
        (3, _("Jueves")),
        (4, _("Viernes")),
        (5, _("Sábado")),
        (6, _("Domingo")),
    ]
    
    dia_semana = models.IntegerField(choices=DIAS_SEMANA)
    hora_apertura = models.TimeField()
    hora_cierre = models.TimeField()
    horas_bloqueadas = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Lista de horas bloqueadas en formato [9, 10, 14] representando las 9:00, 10:00, 14:00")
    )

    class Meta:
        ordering = ['dia_semana', 'hora_apertura']
        verbose_name_plural = _("Disponibilidades")

    def __str__(self) -> str:
        return f"{self.get_dia_semana_display()}: {self.hora_apertura} - {self.hora_cierre}"


class ContenidoVisual(models.Model):
    """Archivos visuales para mostrar en los espacios de la app."""

    TIPO_IMAGEN = 'imagen'
    TIPO_VIDEO = 'video'
    TIPO_CHOICES = [
        (TIPO_IMAGEN, _('Imagen')),
        (TIPO_VIDEO, _('Video')),
    ]

    EXTENSIONES_IMAGEN = ('.jpg', '.jpeg', '.png', '.webp', '.gif')
    EXTENSIONES_VIDEO = ('.mp4', '.mov', '.webm', '.mkv', '.avi')

    titulo = models.CharField(max_length=160)
    descripcion = models.CharField(max_length=255, blank=True)
    archivo = models.FileField(upload_to='espacios/')
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, editable=False)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name_plural = _('Contenidos visuales')

    def save(self, *args, **kwargs):
        if self.archivo:
            archivo_nombre = self.archivo.name.lower()
            if archivo_nombre.endswith(self.EXTENSIONES_IMAGEN):
                self.tipo = self.TIPO_IMAGEN
            elif archivo_nombre.endswith(self.EXTENSIONES_VIDEO):
                self.tipo = self.TIPO_VIDEO
            else:
                raise ValidationError(
                    _('Solo se permiten imágenes o videos en formato común (jpg, png, mp4, webm, mov).')
                )
        super().save(*args, **kwargs)

    @property
    def es_video(self) -> bool:
        return self.tipo == self.TIPO_VIDEO

    @property
    def es_imagen(self) -> bool:
        return self.tipo == self.TIPO_IMAGEN

    def __str__(self) -> str:
        return self.titulo

