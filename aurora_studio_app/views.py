from pathlib import Path
from urllib.parse import quote

from django.shortcuts import render, redirect
from django.views import View
from datetime import datetime
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .infra.repositories import (
    RepositorioServicioDjango,
    RepositorioClienteDjango,
    RepositorioReservaDjango,
    RepositorioDisponibilidadDjango
)
from .infra.factories import FactoriaNotificacion
from .infra.composition import build_ubicacion_local
from .infra.servicios import GeneradorCodigoReservaUUID
from .services import ServicioService, ClienteService, DisponibilidadService, ReservaService


MEDIA_VISUAL_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.mp4', '.mov', '.webm', '.mkv', '.avi'}
MEDIA_SLOT_FILES = {
    'hero_principal': 'principal.jpg',
    'hero_secundario_1': 'microblanding.png',
    'hero_secundario_2': 'Blush Lips.jpg',
    'hero_secundario_3': 'Logo.png',
    'galeria_1': 'servicios.mp4',
    'galeria_2': 'tucita.mp4',
    'galeria_3': 'Cuidadosdehenna.png',
    'promo_1': 'microblanding.jpg',
    'promo_2': 'LaminadoCejas.png',
    'promo_3': 'Logo.png',
    'henna_1': 'antesHenna.png',
    'henna_2': 'DespuesHenna.png',
    'henna_3': 'Cuidadosdehenna.png',
    'lifting_1': 'lifting.png',
    'lifting_2': 'lifting1.png',
    'lifting_3': 'lifting2.png',
}


def _build_media_url(relative_path: Path) -> str:
    media_url = getattr(settings, 'MEDIA_URL', '/media/')
    return f"{media_url}{quote(relative_path.as_posix())}"


def _media_item(filename: str) -> dict | None:
    espacios_dir = Path(getattr(settings, 'MEDIA_ROOT', settings.BASE_DIR / 'media')) / 'espacios'
    archivo = espacios_dir / filename

    if not archivo.exists():
        return None

    es_video = archivo.suffix.lower() in {'.mp4', '.mov', '.webm', '.mkv', '.avi'}
    return {
        'titulo': archivo.stem.replace('_', ' ').replace('-', ' ').title(),
        'descripcion': _('Archivo guardado en media/espacios'),
        'url': _build_media_url(Path('espacios') / archivo.name),
        'es_video': es_video,
    }

def _build_slot_context() -> dict:
    return {
        name: _media_item(filename)
        for name, filename in MEDIA_SLOT_FILES.items()
    }


def _build_ubicacion_context() -> dict:
    adaptador = build_ubicacion_local()
    return {
        'ubicacion_local_nombre': getattr(settings, 'BUSINESS_NAME', 'Aurora Studio'),
        'ubicacion_local_direccion': adaptador.obtener_direccion(),
        'ubicacion_local_mapa_url': adaptador.obtener_url_mapa(),
        'ubicacion_local_ruta_url': adaptador.obtener_url_ruta(),
    }


class HomeView(View):
    """Vista principal que muestra los servicios disponibles."""
    template_name = 'aurora_studio_app/home.html'
    
    def get(self, request):
        # Instanciar servicio con su repositorio (DI manual)
        repositorio = RepositorioServicioDjango()
        servicio_service = ServicioService(repositorio_servicio=repositorio)
        
        # Obtener servicios usando el service layer
        servicios = servicio_service.listar_servicios_activos()
        slots = _build_slot_context()
        
        context = {
            'titulo': _('Bienvenido a Aurora Studio'),
            'descripcion': _('Tu belleza, nuestra pasión'),
            'servicios': servicios,
            **slots,
        }
        context.update(_build_ubicacion_context())
        
        return render(request, self.template_name, context)


class ReservaView(View):
    """Vista para crear reservas."""
    template_name = 'aurora_studio_app/reserva.html'
    
    def get(self, request):
        # Obtener servicios para mostrar en el formulario
        repo_servicio = RepositorioServicioDjango()
        servicio_service = ServicioService(repositorio_servicio=repo_servicio)
        servicios = servicio_service.listar_servicios_activos()
        
        context = {
            'servicios': servicios,
            'reserva_video': _media_item('tucita.mp4'),
        }
        context.update(_build_ubicacion_context())
        return render(request, self.template_name, context)
    
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
                'mensaje': _('Error: ') + str(e),
                **_build_ubicacion_context(),
            })


class MotosPageView(View):
    """Página que muestra la lista de motos consumiendo nuestro proxy interno.

    La plantilla usa `fetch()` hacia `/api/v1/motos-externas/` y renderiza tarjetas.
    """
    template_name = 'aurora_studio_app/motos.html'

    def get(self, request):
        context = {
            'titulo': _('Motos disponibles'),
        }
        context.update(_build_ubicacion_context())
        return render(request, self.template_name, context)
