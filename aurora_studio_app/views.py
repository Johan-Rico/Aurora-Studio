from django.shortcuts import render, redirect
from django.views import View
from datetime import datetime

from .infra.repositories import (
    RepositorioServicioDjango,
    RepositorioClienteDjango,
    RepositorioReservaDjango,
    RepositorioDisponibilidadDjango
)
from .infra.factories import FactoriaNotificacion
from .infra.servicios import GeneradorCodigoReservaUUID
from .services import ServicioService, ClienteService, DisponibilidadService, ReservaService


class HomeView(View):
    """Vista principal que muestra los servicios disponibles."""
    template_name = 'aurora_studio_app/home.html'
    
    def get(self, request):
        # Instanciar servicio con su repositorio (DI manual)
        repositorio = RepositorioServicioDjango()
        servicio_service = ServicioService(repositorio_servicio=repositorio)
        
        # Obtener servicios usando el service layer
        servicios = servicio_service.listar_servicios_activos()
        
        context = {
            'titulo': 'Bienvenido a Aurora Studio',
            'descripcion': 'Tu belleza, nuestra pasión',
            'servicios': servicios,
        }
        
        return render(request, self.template_name, context)


class ReservaView(View):
    """Vista para crear reservas."""
    template_name = 'aurora_studio_app/reserva.html'
    
    def get(self, request):
        # Obtener servicios para mostrar en el formulario
        repo_servicio = RepositorioServicioDjango()
        servicio_service = ServicioService(repositorio_servicio=repo_servicio)
        servicios = servicio_service.listar_servicios_activos()
        
        return render(request, self.template_name, {'servicios': servicios})
    
    def post(self, request):
        try:
            # Obtener datos del formulario
            nombre = request.POST.get('nombre')
            email = request.POST.get('email')
            telefono = request.POST.get('telefono')
            fecha_str = request.POST.get('fecha')
            hora_str = request.POST.get('hora_inicio')
            servicios_ids = request.POST.getlist('servicios')
            
            # Convertir fecha y hora
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hora = datetime.strptime(hora_str, '%H:%M').time()
            servicios_ids = [int(sid) for sid in servicios_ids]
            
            # Instanciar servicios y repositorios
            repo_servicio = RepositorioServicioDjango()
            repo_cliente = RepositorioClienteDjango()
            repo_reserva = RepositorioReservaDjango()
            repo_disponibilidad = RepositorioDisponibilidadDjango()
            
            servicio_service = ServicioService(repositorio_servicio=repo_servicio)
            cliente_service = ClienteService(repositorio_cliente=repo_cliente)
            disponibilidad_service = DisponibilidadService(
                repositorio_reserva=repo_reserva,
                repositorio_disponibilidad=repo_disponibilidad
            )
            
            # Crear enviador de notificaciones y generador de código
            enviador = FactoriaNotificacion.crear_enviador()
            generador = GeneradorCodigoReservaUUID()
            
            reserva_service = ReservaService(
                cliente_service=cliente_service,
                servicio_service=servicio_service,
                disponibilidad_service=disponibilidad_service,
                repositorio_reserva=repo_reserva,
                enviador_notificacion=enviador,
                generador_codigo=generador
            )
            
            # Crear reserva
            datos = {
                'nombre': nombre,
                'email': email,
                'telefono': telefono,
                'fecha': fecha,
                'hora': hora,
                'servicios_ids': servicios_ids
            }
            
            reserva = reserva_service.crear_reserva_completa(datos)
            
            return redirect('home')
            
        except Exception as e:
            # En caso de error, mostrar mensaje
            repo_servicio = RepositorioServicioDjango()
            servicio_service = ServicioService(repositorio_servicio=repo_servicio)
            servicios = servicio_service.listar_servicios_activos()
            
            return render(request, self.template_name, {
                'servicios': servicios,
                'mensaje': f'Error: {str(e)}'
            })
