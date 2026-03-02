from django.contrib import admin
from .models import Usuario, Cliente, Servicio, Reserva, DetalleCita, Disponibilidad


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email')
    search_fields = ('nombre', 'email')


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'telefono')
    search_fields = ('nombre', 'email', 'telefono')


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'duracion')
    list_filter = ('categoria',)
    search_fields = ('nombre', 'descripcion')


class DetalleCitaInline(admin.TabularInline):
    model = DetalleCita
    extra = 0
    readonly_fields = ('servicio', 'precio_aplicado')


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo_reserva', 'cliente', 'fecha', 'hora_inicio', 'hora_fin', 'tipo')
    list_filter = ('tipo', 'fecha')
    search_fields = ('cliente__nombre', 'cliente__email', 'codigo_reserva')
    readonly_fields = ('codigo_reserva',)
    inlines = [DetalleCitaInline]
    date_hierarchy = 'fecha'


@admin.register(DetalleCita)
class DetalleCitaAdmin(admin.ModelAdmin):
    list_display = ('reserva', 'servicio', 'precio_aplicado')
    list_filter = ('servicio',)


@admin.register(Disponibilidad)
class DisponibilidadAdmin(admin.ModelAdmin):
    list_display = ('dia_semana', 'hora_apertura', 'hora_cierre', 'horas_bloqueadas')
    list_filter = ('dia_semana',)
