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

### Configuracion del entorno raiz

Antes de levantar Docker Compose, crea el archivo raiz `.env` a partir del ejemplo:

```powershell
Copy-Item .env.example .env
```

Edita `.env` y ajusta al menos:
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS`
- `DJANGO_CSRF_TRUSTED_ORIGINS`
- `NGINX_HOST_PORT`

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

Si no vas a usar SMTP todavía, deja `NOTIFICATION_SENDER=mock`. Para AWS/producción, usa `smtp` y completa las credenciales.

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

## Despliegue en AWS EC2

La forma más simple es usar una instancia Ubuntu con Docker y Docker Compose.

### 1) Instalar Docker

En la EC2:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
```

Cierra sesión y vuelve a entrar para aplicar el grupo `docker`.

### 2) Subir el proyecto

Clona el repo o copia los archivos al servidor.

### 3) Crear archivos de entorno

En la raíz del proyecto:

```bash
cp .env.example .env
cp microservices/flask_funcionalidad/.env.example microservices/flask_funcionalidad/.env
```

Edita `.env` y, como mínimo, ajusta:
- `DJANGO_SECRET_KEY`
- `DJANGO_ALLOWED_HOSTS` con la IP pública o dominio
- `DJANGO_CSRF_TRUSTED_ORIGINS` con el origen público
- `NGINX_HOST_PORT=80` si quieres exponer el sitio en el puerto estándar

Edita `microservices/flask_funcionalidad/.env` y define SMTP si quieres correo real.

### 4) Levantar la plataforma

```bash
docker compose up --build -d
```

### 5) Probar desde el navegador

- `http://TU_IP_PUBLICA:80/` si `NGINX_HOST_PORT=80`
- `http://TU_IP_PUBLICA:8080/` si mantienes el valor por defecto

### 6) Comandos útiles

```bash
docker compose ps
docker compose logs -f nginx
docker compose logs -f django
docker compose logs -f flask
docker compose logs -f celery-worker
```

### 7) Seguridad mínima en AWS

- Abre en el Security Group solo el puerto de Nginx que vayas a usar (`80` o `8080`).
- No expongas Redis, Django ni Flask al público si no hace falta.
- Mantén `DEBUG=0` y usa secretos reales en `.env`.

### 8) Prueba funcional

Puedes correr la verificación E2E local o en la EC2:

```bash
./scripts/integration_test.ps1
```

Si estás en Linux, haz una prueba manual con `curl` al endpoint de health y al endpoint de notificación.

## Variables de Entorno Clave

### Django

- `USE_POSTGRES=0` para usar SQLite
- `DJANGO_DEBUG=1`
- `DJANGO_ALLOWED_HOSTS=*`
- `NOTIFICATION_SENDER=mock|smtp`
- `NOTIFICATIONS_SERVICE_URL=http://flask:5001/api/v2/funcionalidad`

### Flask

- `NOTIFICATION_SENDER=mock|smtp`
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

## Prueba E2E (nginx → flask → django)

Se incluye un script para levantar los contenedores y ejecutar una verificación automática:

PowerShell (desde la raíz del repo):

```powershell
.\scripts\integration_test.ps1
```

El script hará:
- `docker compose up --build -d`
- Esperar al endpoint de health vía `http://localhost:8080/api/v2/funcionalidad/health`
- Enviar un `POST` de prueba a `http://localhost:8080/api/v2/funcionalidad/notificaciones/reserva`

Si prefieres ejecutar manualmente:

```powershell
docker compose up --build -d
# esperar a que los servicios respondan
curl http://localhost:8080/api/v2/funcionalidad/health
curl -X POST http://localhost:8080/api/v2/funcionalidad/notificaciones/reserva -H "Content-Type: application/json" -d '{...}'
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

## Patrones Aplicados

Los patrones que realmente aportan valor aquí y ya están aplicados son:

- Repository: aislar el acceso a Django ORM en `aurora_studio_app/infra/repositories.py`.
- Service: contener la lógica de negocio en `aurora_studio_app/services.py`.
- Builder: construir reservas y bloqueos en `aurora_studio_app/domain/builders.py`.
- Factory: decidir el tipo de enviador en `aurora_studio_app/infra/factories.py`.
- Adapter: delegar notificaciones hacia Flask en `aurora_studio_app/infra/servicios.py`.
- Strategy: cambiar entre `mock`, Flask y Celery sin tocar la lógica de negocio.
- Composition Root: centralizar el armado de dependencias en `aurora_studio_app/infra/composition.py`.
- Command/Worker: encolar notificaciones con Celery cuando `NOTIFICATIONS_ASYNC=1`.

No añadí patrones por estética; solo los que simplifican el flujo o preparan el despliegue.

## Notas de Seguridad

- Nunca subir credenciales reales al repositorio
- Mantener archivos `.env` fuera de Git
- Rotar cualquier credencial usada durante pruebas

