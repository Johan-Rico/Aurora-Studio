# Sistema de Gestion de Reservas - Aurora

Aplicacion web para gestion de servicios y reservas. El proyecto usa un monolito Django y un microservicio Flask para la funcionalidad estrangulada, con Nginx como gateway.

## Arquitectura Actual

- Django: web + API v1 + logica de negocio principal
- Flask: API v2 de funcionalidad estrangulada (notificaciones)
- Nginx: punto unico de entrada y enrutamiento
- SQLite: base de datos local y tambien en entorno Docker

## Estructura de Proyecto

```text
Aurora-Studio/
│   └── nginx.conf                      # Reglas de ruteo v1/v2
├── docker-compose.yml                  # Orquestacion de servicios
├── Dockerfile                          # Imagen Django
├── requirements.txt                    # Dependencias Django para Docker
└── manage.py
```

## Endpoints Principales

### Web (Django)

- `/`
- `/reserva/`

### API v1 (Django)

- `GET /api/servicios/`
- `POST /api/reservas/`
- `GET /api/disponibilidad/?fecha=YYYY-MM-DD`
- `POST /api/reservas/cancel/`

### API v2 Estrangulada (Flask)

- `GET /api/v2/funcionalidad/health`
- `POST /api/v2/funcionalidad/notificaciones/reserva`

## Enrutamiento por Nginx

- `/api/v1/*` -> Django (`/api/*`)
- `/api/v2/funcionalidad/*` -> Flask
- `/` y demas -> Django

## Ejecutar Sin Docker (Modo Local Rapido)

### Requisitos

- Python 3.11+

### Pasos

1. Instalar dependencias basicas:

```bash
pip install django==5.2.11 djangorestframework
```

1. Migrar base de datos:

```bash
python manage.py migrate
```

1. Levantar servidor:

```bash
python manage.py runserver
```

## Ejecutar Con Docker (Recomendado para Entrega)

### Requisitos Docker

- Docker Desktop encendido
- Docker Compose plugin disponible (`docker compose`)

### Configurar variables de entorno (Flask)

Antes de levantar los contenedores, crea el archivo `.env` del microservicio Flask a partir del ejemplo:

```bash
cp microservices/flask_funcionalidad/.env.example microservices/flask_funcionalidad/.env
```

En Windows PowerShell puedes usar:

```powershell
Copy-Item microservices/flask_funcionalidad/.env.example microservices/flask_funcionalidad/.env
```

Luego edita `microservices/flask_funcionalidad/.env` con tus valores (especialmente SMTP si quieres envio real de correos).

### Levantar todo

```bash
docker compose up --build -d
```

El contenedor Django usa el archivo `db.sqlite3` del proyecto para conservar los datos existentes.

### Ver estado

```bash
docker compose ps
```

### Ver logs

```bash
docker compose logs -f
```

### Bajar servicios

```bash
docker compose down
```

### Bajar servicios y limpiar estado

```bash
docker compose down --remove-orphans
```

## Variables de Entorno Clave

### Django

- `USE_POSTGRES=0` para usar SQLite
- `DJANGO_DEBUG=1`
- `DJANGO_ALLOWED_HOSTS=*`
- `NOTIFICATION_SENDER=flask`
- `NOTIFICATIONS_SERVICE_URL=http://flask:5001/api/v2/funcionalidad`

### Flask

- `NOTIFICATION_SENDER=MOCK|SMTP`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USER`
- `SMTP_PASSWORD`
- `SMTP_FROM_EMAIL`
- `SMTP_USE_TLS`
- `SMTP_USE_SSL`

## Verificacion Rapida

1. Salud del microservicio por gateway:

```bash
curl http://localhost:8080/api/v2/funcionalidad/health
```

1. Servicios API v1 por gateway:

```bash
curl http://localhost:8080/api/v1/servicios/
```

Si necesitas volver a cargar datos manualmente en Docker:

```bash
docker compose exec django python manage.py migrate
```

1. Web principal:

```text
http://localhost:8080/
```

## Problemas Comunes y Soluciones

### 1) `docker` no se reconoce en terminal

- Cierra y abre VS Code despues de instalar Docker Desktop.
- Si persiste, agrega manualmente al PATH:

`C:\Program Files\Docker\Docker\resources\bin`

### 2) `docker-credential-desktop` no encontrado

- Es el mismo problema de PATH. Ver punto anterior.

### 3) Microservicio Flask no envía correo

- Valida `NOTIFICATION_SENDER=SMTP`
- Usa App Password del proveedor (no password normal)
- Revisa logs con `docker compose logs -f flask`

## Estado de Migracion Strangler

- Monolito Django permanece para el core (reservas, disponibilidad, clientes)
- Funcionalidad estrangulada en Flask expuesta como API v2
- Nginx centraliza rutas y permite coexistencia de frameworks

## Notas de Seguridad

- Nunca subir credenciales reales al repositorio
- Mantener archivos `.env` fuera de Git
- Rotar cualquier credencial usada durante pruebas

