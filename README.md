# Sistema de Gestión de Reservas - Aurora

Sistema web de gestión de citas y reservas desarrollado para Aurora, negocio de servicios de belleza. Implementa arquitectura limpia con separación por capas y cumplimiento de principios SOLID.

## Descripción del Proyecto

Aplicación Django que permite la gestión completa de reservas para un estudio de belleza. Incluye validación de disponibilidad, gestión de clientes, servicios, y notificaciones. Provee tanto interfaz web como API REST para integración con otros sistemas.

## Funcionalidades Principales

- Gestión de servicios con precio y duración configurable
- Sistema de reservas con validación de horarios y disponibilidad
- Generación de código único por reserva para seguimiento
- Notificaciones automáticas por email (configurable mock/real)
- Cancelación de reservas mediante email + código
- API REST completa para integración externa
- Configuración de horarios de atención por día de la semana

## Tecnologías y Arquitectura

### Stack Tecnológico
- Django 5.2.11
- Django REST Framework
- Python 3.x
- SQLite (desarrollo)

### Arquitectura
- **Domain-Driven Design (DDD)**: Separación por capas (Domain, Application, Infrastructure, Presentation)
- **SOLID Principles**: Aplicados en todo el código
- **Repository Pattern**: Abstracción de acceso a datos
- **Builder Pattern**: Construcción compleja de objetos (Reserva)
- **Factory Pattern**: Creación dinámica de servicios según configuración

## Estructura del Proyecto

```
aurora_studio/
├── aurora_studio/          # Configuración Django
│   ├── settings.py         # Configuración general
│   └── urls.py             # URLs principales
│
├── aurora_studio_app/      # Aplicación principal
│   ├── models.py           # Modelos de datos
│   ├── views.py            # Vistas web (HTML)
│   ├── urls.py             # URLs de la app
│   │
│   ├── domain/             # Capa de dominio
│   │   ├── interfaces.py   # Interfaces abstractas
│   │   └── builders.py     # Constructores de objetos
│   │
│   ├── infra/              # Capa de infraestructura
│   │   ├── repositories.py # Implementaciones de repositorios
│   │   ├── servicios.py    # Servicios externos (email, UUID)
│   │   └── factories.py    # Fábricas de objetos
│   │
│   ├── api/                # API REST
│   │   ├── views.py        # Endpoints API
│   │   ├── serializers.py  # Serializadores JSON
│   │   └── urls.py         # URLs API
│   │
│   ├── services.py         # Capa de aplicación (lógica de negocio)
│   └── templates/          # Plantillas HTML
│
└── db.sqlite3              # Base de datos
```

## Instalación y Configuración

### Prerrequisitos
- Python 3.8+

### Pasos de Instalación

1. Clonar el repositorio
```bash
git clone https://github.com/tuusuario/Aurora-Studio.git
cd Aurora-Studio
```

2. Instalar dependencias
```bash
pip install django==5.2.11
pip install djangorestframework
```

3. Aplicar migraciones
```bash
python manage.py migrate
```

4. Iniciar servidor
```bash
python manage.py runserver
```

## Configuración

### Notificaciones
Por defecto, las notificaciones se imprimen en consola (modo desarrollo):
```bash
$env:NOTIFICATION_SENDER="MOCK"   # Windows PowerShell
NOTIFICATION_SENDER=MOCK # Linux/Mac
```

## Uso del Sistema

### Interfaz Web
- `/` - Listado de servicios disponibles
- `/reserva/` - Formulario de creación de reserva

### API REST

#### Listar Servicios
```http
GET /api/servicios/
```

#### Crear Reserva
```http
POST /api/reservas/
Content-Type: application/json

{
  "nombre": "María García",
  "email": "maria@example.com",
  "telefono": "+1234567890",
  "fecha": "2026-03-18",
  "hora": "10:00",
  "servicios_ids": [1, 3]
}
```

#### Consultar Disponibilidad
```http
GET /api/disponibilidad/?fecha=2026-03-18
```

#### Cancelar Reserva
```http
POST /api/reservas/cancel/
Content-Type: application/json

{
  "email": "maria@example.com",
  "codigo": "A3F7B2C9"
}
```

## Modelos de Datos

- **Usuario**: Usuarios base del sistema
- **Cliente**: Clientes que realizan reservas (hereda de Usuario)
- **Servicio**: Servicios ofrecidos con precio y duración
- **Reserva**: Citas o bloqueos administrativos
- **DetalleCita**: Relación muchos-a-muchos entre Reserva y Servicio
- **Disponibilidad**: Horarios de atención por día de la semana

## Arquitectura en Capas

El proyecto implementa Domain-Driven Design con 4 capas bien definidas:

1. **Domain** (`domain/`): Lógica de negocio pura, interfaces abstractas, sin dependencias externas
2. **Application** (`services.py`): Orquestación de casos de uso, lógica de aplicación
3. **Infrastructure** (`infra/`): Implementaciones concretas (repositorios Django ORM, email, UUID)
4. **Presentation** (`views.py`, `api/`): Vistas web y endpoints REST

