"""
Solicitudes Service
Business logic for solicitudes management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

from tortoise.expressions import Q
from tortoise.queryset import QuerySet

from models.solicitud import Solicitud, RepuestoSolicitado
from models.user import Cliente
from models.enums import EstadoSolicitud
from services.geografia_service import GeografiaService


class SolicitudesService:
    """Service for managing solicitudes"""
    
    @staticmethod
    async def get_solicitudes_paginated(
        page: int = 1,
        page_size: int = 25,
        estado: Optional[EstadoSolicitud] = None,
        search: Optional[str] = None,
        fecha_desde: Optional[datetime] = None,
        fecha_hasta: Optional[datetime] = None,
        ciudad: Optional[str] = None,
        departamento: Optional[str] = None,
        user_rol: Optional[str] = None,
        asesor_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """
        Get paginated solicitudes with filters
        
        For ASESORES: Only show solicitudes where they were evaluated/notified OR made an offer
        For ADMIN: Show all solicitudes
        """
        # Build query
        query = Solicitud.all()
        
        # For advisors, filter by assigned solicitudes (evaluated or offered)
        if user_rol == "ASESOR" and asesor_id:
            # Solicitudes where the asesor was evaluated/notified OR made an offer
            query = query.filter(
                Q(evaluaciones_asesores__asesor_id=asesor_id) |
                Q(ofertas__asesor_id=asesor_id)
            ).distinct()
        
        # Apply filters
        if estado:
            query = query.filter(estado=estado)
        
        if search:
            query = query.filter(
                Q(cliente__usuario__nombre__icontains=search) |
                Q(cliente__usuario__apellido__icontains=search) |
                Q(cliente__usuario__telefono__icontains=search) |
                Q(ciudad_origen__icontains=search)
            )
        
        if fecha_desde:
            query = query.filter(created_at__gte=fecha_desde)
        
        if fecha_hasta:
            # Add one day to include the entire day
            fecha_hasta_end = fecha_hasta + timedelta(days=1)
            query = query.filter(created_at__lt=fecha_hasta_end)
        
        if ciudad:
            query = query.filter(ciudad_origen__iexact=ciudad)
        
        if departamento:
            query = query.filter(departamento_origen__iexact=departamento)
        
        # Order by creation date (newest first)
        query = query.order_by("-created_at")
        
        # Get total count
        total = await query.count()
        
        # Calculate pagination
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size
        
        # Get paginated results
        solicitudes = await query.offset(offset).limit(page_size).prefetch_related(
            "cliente",
            "cliente__usuario",
            "repuestos_solicitados",
            "ofertas"
        )
        
        # Format response
        items = []
        for sol in solicitudes:
            items.append({
                "id": str(sol.id),
                "cliente_id": str(sol.cliente.id),
                "cliente_nombre": sol.cliente.usuario.nombre_completo,
                "cliente_telefono": sol.cliente.usuario.telefono,
                "estado": sol.estado.value,
                "nivel_actual": sol.nivel_actual,
                "ciudad_origen": sol.ciudad_origen,
                "departamento_origen": sol.departamento_origen,
                "ofertas_minimas_deseadas": sol.ofertas_minimas_deseadas,
                "timeout_horas": sol.timeout_horas,
                "fecha_creacion": sol.created_at.isoformat(),
                "fecha_escalamiento": sol.fecha_escalamiento.isoformat() if sol.fecha_escalamiento else None,
                "fecha_evaluacion": sol.fecha_evaluacion.isoformat() if sol.fecha_evaluacion else None,
                "fecha_expiracion": sol.fecha_expiracion.isoformat() if sol.fecha_expiracion else None,
                "total_repuestos": sol.total_repuestos,
                "monto_total_adjudicado": float(sol.monto_total_adjudicado),
                "repuestos_solicitados": [
                    {
                        "id": str(rep.id),
                        "nombre": rep.nombre,
                        "codigo": rep.codigo,
                        "descripcion": rep.descripcion,
                        "cantidad": rep.cantidad,
                        "marca_vehiculo": rep.marca_vehiculo,
                        "linea_vehiculo": rep.linea_vehiculo,
                        "anio_vehiculo": rep.anio_vehiculo,
                        "observaciones": rep.observaciones,
                        "es_urgente": rep.es_urgente
                    }
                    for rep in sol.repuestos_solicitados
                ] if hasattr(sol, 'repuestos_solicitados') else []
            })
        
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }

    
    @staticmethod
    async def get_solicitud_by_id(solicitud_id: uuid.UUID) -> Optional[Dict[str, Any]]:
        """
        Get solicitud by ID with full details
        """
        solicitud = await Solicitud.get_or_none(id=solicitud_id).prefetch_related(
            "cliente",
            "cliente__usuario",
            "repuestos_solicitados",
            "ofertas",
            "ofertas__asesor"
        )
        
        if not solicitud:
            return None
        
        return {
            "id": str(solicitud.id),
            "cliente_id": str(solicitud.cliente.id),
            "cliente_nombre": solicitud.cliente.usuario.nombre_completo,
            "cliente_telefono": solicitud.cliente.usuario.telefono,
            "estado": solicitud.estado.value,
            "nivel_actual": solicitud.nivel_actual,
            "ciudad_origen": solicitud.ciudad_origen,
            "departamento_origen": solicitud.departamento_origen,
            "ofertas_minimas_deseadas": solicitud.ofertas_minimas_deseadas,
            "timeout_horas": solicitud.timeout_horas,
            "fecha_creacion": solicitud.created_at.isoformat(),
            "fecha_escalamiento": solicitud.fecha_escalamiento.isoformat() if solicitud.fecha_escalamiento else None,
            "fecha_evaluacion": solicitud.fecha_evaluacion.isoformat() if solicitud.fecha_evaluacion else None,
            "fecha_expiracion": solicitud.fecha_expiracion.isoformat() if solicitud.fecha_expiracion else None,
            "total_repuestos": solicitud.total_repuestos,
            "monto_total_adjudicado": float(solicitud.monto_total_adjudicado),
            "repuestos_solicitados": [
                {
                    "id": str(rep.id),
                    "nombre": rep.nombre,
                    "codigo": rep.codigo,
                    "descripcion": rep.descripcion,
                    "cantidad": rep.cantidad,
                    "marca_vehiculo": rep.marca_vehiculo,
                    "linea_vehiculo": rep.linea_vehiculo,
                    "anio_vehiculo": rep.anio_vehiculo,
                    "observaciones": rep.observaciones,
                    "es_urgente": rep.es_urgente
                }
                for rep in solicitud.repuestos_solicitados
            ] if hasattr(solicitud, 'repuestos_solicitados') else []
        }
    
    @staticmethod
    async def create_solicitud(
        cliente_data: Dict[str, Any],
        ciudad_origen: str,
        departamento_origen: str,
        repuestos: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create new solicitud with cliente and repuestos
        """
        from models.user import Usuario, Cliente
        from models.enums import RolUsuario, EstadoUsuario
        
        # Validate geography (optional for development)
        geografia_service = GeografiaService()
        ciudad_valida = await geografia_service.validar_ciudad(ciudad_origen, departamento_origen)
        
        if not ciudad_valida:
            # Log warning but allow creation for development
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Ciudad {ciudad_origen} no encontrada en base de datos geográfica. Ciudades disponibles: BOGOTA, MEDELLIN, CALI, BARRANQUILLA")
            # TODO: Enable strict validation in production
            # raise ValueError(f"Ciudad {ciudad_origen} no válida. Ciudades disponibles: BOGOTA, MEDELLIN, CALI, BARRANQUILLA")
        
        # Normalize phone number to Colombian format
        telefono = cliente_data["telefono"]
        if not telefono.startswith("+57"):
            # Remove any non-digit characters
            telefono_digits = ''.join(filter(str.isdigit, telefono))
            # Add Colombian prefix
            telefono = f"+57{telefono_digits[-10:]}"
        
        # Get or create usuario and cliente (telefono is now unique)
        usuario = await Usuario.get_or_none(telefono=telefono)
        
        if not usuario:
            # Create new usuario
            usuario = await Usuario.create(
                email=cliente_data.get("email", f"{telefono}@teloo.temp"),
                password_hash="temp_hash",  # Will be set when user registers
                nombre=cliente_data["nombre"].split()[0] if cliente_data["nombre"] else "Cliente",
                apellido=" ".join(cliente_data["nombre"].split()[1:]) if len(cliente_data["nombre"].split()) > 1 else "",
                telefono=telefono,
                rol=RolUsuario.CLIENT,
                estado=EstadoUsuario.ACTIVO
            )
            
            # Create cliente profile
            cliente = await Cliente.create(
                usuario=usuario,
                ciudad=ciudad_origen,
                departamento=departamento_origen
            )
        else:
            # Get existing cliente
            cliente = await Cliente.get_or_none(usuario=usuario)
            if not cliente:
                # Create cliente profile if doesn't exist
                cliente = await Cliente.create(
                    usuario=usuario,
                    ciudad=ciudad_origen,
                    departamento=departamento_origen
                )
        
        # Create solicitud
        solicitud = await Solicitud.create(
            cliente=cliente,
            estado=EstadoSolicitud.ABIERTA,
            nivel_actual=1,
            ciudad_origen=ciudad_origen,
            departamento_origen=departamento_origen,
            ofertas_minimas_deseadas=2,
            timeout_horas=20,
            total_repuestos=len(repuestos),
            monto_total_adjudicado=Decimal("0.00")
        )
        
        # Create repuestos
        repuestos_created = []
        for rep_data in repuestos:
            repuesto = await RepuestoSolicitado.create(
                solicitud=solicitud,
                nombre=rep_data["nombre"],
                codigo=rep_data.get("codigo"),
                descripcion=rep_data.get("descripcion"),
                cantidad=rep_data["cantidad"],
                marca_vehiculo=rep_data["marca_vehiculo"],
                linea_vehiculo=rep_data["linea_vehiculo"],
                anio_vehiculo=rep_data["anio_vehiculo"],
                observaciones=rep_data.get("observaciones"),
                es_urgente=rep_data.get("es_urgente", False)
            )
            repuestos_created.append(repuesto)
        
        # Reload with relations
        await solicitud.fetch_related("cliente", "cliente__usuario", "repuestos_solicitados")
        
        return {
            "id": str(solicitud.id),
            "cliente_id": str(solicitud.cliente.id),
            "cliente_nombre": solicitud.cliente.usuario.nombre_completo,
            "cliente_telefono": solicitud.cliente.usuario.telefono,
            "estado": solicitud.estado.value,
            "nivel_actual": solicitud.nivel_actual,
            "ciudad_origen": solicitud.ciudad_origen,
            "departamento_origen": solicitud.departamento_origen,
            "ofertas_minimas_deseadas": solicitud.ofertas_minimas_deseadas,
            "timeout_horas": solicitud.timeout_horas,
            "fecha_creacion": solicitud.created_at.isoformat(),
            "fecha_escalamiento": None,
            "fecha_evaluacion": None,
            "fecha_expiracion": None,
            "total_repuestos": solicitud.total_repuestos,
            "monto_total_adjudicado": float(solicitud.monto_total_adjudicado),
            "repuestos_solicitados": [
                {
                    "id": str(rep.id),
                    "nombre": rep.nombre,
                    "codigo": rep.codigo,
                    "descripcion": rep.descripcion,
                    "cantidad": rep.cantidad,
                    "marca_vehiculo": rep.marca_vehiculo,
                    "linea_vehiculo": rep.linea_vehiculo,
                    "anio_vehiculo": rep.anio_vehiculo,
                    "observaciones": rep.observaciones,
                    "es_urgente": rep.es_urgente
                }
                for rep in solicitud.repuestos_solicitados
            ]
        }
    
    @staticmethod
    async def get_stats() -> Dict[str, int]:
        """
        Get statistics by estado
        """
        total = await Solicitud.all().count()
        abiertas = await Solicitud.filter(estado=EstadoSolicitud.ABIERTA).count()
        evaluadas = await Solicitud.filter(estado=EstadoSolicitud.EVALUADA).count()
        aceptadas = await Solicitud.filter(estado=EstadoSolicitud.ACEPTADA).count()
        
        rechazadas = await Solicitud.filter(estado=EstadoSolicitud.RECHAZADA).count()
        expiradas = await Solicitud.filter(estado=EstadoSolicitud.EXPIRADA).count()
        cerradas = await Solicitud.filter(estado=EstadoSolicitud.CERRADA_SIN_OFERTAS).count()
        
        return {
            "total": total,
            "abiertas": abiertas,
            "evaluadas": evaluadas,
            "aceptadas": aceptadas,
            "rechazadas_expiradas": rechazadas + expiradas + cerradas
        }
