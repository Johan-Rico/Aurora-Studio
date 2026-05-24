# Integration test script for Aurora-Studio
# Usage: Open PowerShell, cd to repo root and run: .\scripts\integration_test.ps1

param(
    [int]$TimeoutSeconds = 180
)

function Ensure-DockerAvailable {
    try {
        docker --version > $null 2>&1
        return $true
    } catch {
        Write-Error "Docker no está disponible en esta máquina. Instala Docker Desktop y vuelve a intentarlo."
        return $false
    }
}

if (-not (Ensure-DockerAvailable)) { exit 1 }

Write-Host "Levantar contenedores con docker compose (puede pedir permisos)..."
docker compose up --build -d

$start = Get-Date
$healthUrl = 'http://localhost:8080/api/v2/funcionalidad/health'

Write-Host "Esperando a que el gateway (nginx) responda en $healthUrl ..."
$ok = $false
while ((Get-Date) - $start).TotalSeconds -lt $TimeoutSeconds {
    try {
        $r = Invoke-RestMethod -Uri $healthUrl -Method Get -TimeoutSec 5
        Write-Host "Health OK:" ($r | ConvertTo-Json -Compress)
        $ok = $true
        break
    } catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $ok) {
    Write-Error "Servicios no respondieron en $TimeoutSeconds segundos. Revisa 'docker compose ps' y logs."
    docker compose ps
    exit 2
}

Write-Host "Probando endpoint de notificación (POST)."
$payload = @{
    canal = 'email'
    destinatario = 'prueba@example.com'
    nombre_cliente = 'Prueba'
    codigo_reserva = 'TEST1234'
    fecha_reserva = (Get-Date).ToString('yyyy-MM-dd')
    hora_inicio = '10:00'
    hora_fin = '11:00'
    nombres_servicios = @('Corte')
    precio_total = '10.00'
} | ConvertTo-Json -Depth 5

try {
    $response = Invoke-RestMethod -Uri 'http://localhost:8080/api/v2/funcionalidad/notificaciones/reserva' -Method Post -Body $payload -ContentType 'application/json' -TimeoutSec 10
    Write-Host "POST OK:" ($response | ConvertTo-Json -Compress)
} catch {
    Write-Error "POST falló: $($_.Exception.Message)"
    docker compose logs --no-color --tail 200
    exit 3
}

Write-Host "Prueba E2E completada correctamente. Para parar los contenedores: 'docker compose down'" 
