from rest_framework import serializers
from decimal import Decimal

from aurora_studio_app.models import Reserva, Servicio


class ServicioOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servicio
        fields = ["id", "nombre", "categoria", "descripcion", "precio", "duracion"]


class ReservaCreateInputSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    telefono = serializers.CharField(max_length=15)
    fecha = serializers.DateField()
    hora = serializers.TimeField()
    servicios_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        allow_empty=False,
    )


class ReservaOutputSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source="cliente.nombre", read_only=True)
    cliente_email = serializers.CharField(source="cliente.email", read_only=True)
    cliente_telefono = serializers.CharField(source="cliente.telefono", read_only=True)
    servicios = serializers.SerializerMethodField()

    class Meta:
        model = Reserva
        fields = [
            "id",
            "codigo_reserva",
            "tipo",
            "fecha",
            "hora_inicio",
            "hora_fin",
            "cliente_nombre",
            "cliente_email",
            "cliente_telefono",
            "servicios",
        ]

    def get_servicios(self, obj: Reserva) -> list[dict]:
        return [
            {
                "id": detalle.servicio.id,
                "nombre": detalle.servicio.nombre,
                "categoria": detalle.servicio.categoria,
                "precio_aplicado": str(detalle.precio_aplicado),
            }
            for detalle in obj.detalles.select_related("servicio").all()
        ]


class DisponibilidadConsultaInputSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    duracion_horas = serializers.DecimalField(
        max_digits=4,
        decimal_places=2,
        required=False,
        default=Decimal("1.00"),
        min_value=Decimal("0.50"),
    )


class DisponibilidadConsultaOutputSerializer(serializers.Serializer):
    fecha = serializers.DateField()
    duracion_horas = serializers.DecimalField(max_digits=4, decimal_places=2)
    horarios_disponibles = serializers.ListField(child=serializers.CharField())


class ReservaCancelacionCodigoInputSerializer(serializers.Serializer):
    email = serializers.EmailField()
    codigo = serializers.CharField(max_length=20)


    