"""
Solicitudes Service
Business logic for solicitudes management
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import logging

from tortoise.expressions import Q
from tortoise.queryset import QuerySet

from models.solicitud import Solicitud, RepuestoSolicitado
from models.user import Cliente
from models.enums import EstadoSolicitud
from services.geografia_service import GeografiaService

logger = logging.getLogger(__name__)


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
        
        # For advisors, filter by assigned solicitudes
        if user_rol == "ADVISOR" and asesor_id:
            # Only show OPEN solicitudes where:
            # 1. The asesor was evaluated AND solicitud.nivel_actual >= evaluacion.nivel_entrega (acumulativo)
            # 2. OR the asesor made an offer (can still see it even if level changed)
            
            # Get IDs of solicitudes where nivel matches
            from tortoise import connections
            conn = connections.get("default")
            
            # Query to get solicitudes where nivel_actual >= asesor's nivel_entrega (acumulativo)
            nivel_match_ids = await conn.execute_query_dict("""
                SELECT DISTINCT s.id 
                FROM solicitudes s
                INNER JOIN evaluaciones_asesores_temp e ON e.solicitud_id = s.id
                WHERE e.asesor_id = $1
                AND s.nivel_actual >= e.nivel_entrega
                AND s.estado = 'ABIERTA'
            """, [str(asesor_id)])
            
            nivel_match_uuids = [row['id'] for row in nivel_match_ids]
            
            # Filter: solicitudes with matching nivel OR where asesor made an offer
            if nivel_match_uuids:
                query = query.filter(
                    Q(id__in=nivel_match_uuids) |
                    Q(ofertas__asesor_id=asesor_id)  # Sin filtro de estado - mostrar todas donde hizo oferta
                ).distinct()
            else:
                # Only show solicitudes where they made an offer (sin importar estado)
                query = query.filter(
                    ofertas__asesor_id=asesor_id
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
            # Find mi_oferta if asesor_id is provided
            mi_oferta = None
            if asesor_id and hasattr(sol, 'ofertas'):
                for oferta in sol.ofertas:
                    if str(oferta.asesor_id) == str(asesor_id):
                        # Load detalles for the oferta
                        await oferta.fetch_related('detalles')
                        mi_oferta = {
                            "id": str(oferta.id),
                            "solicitud_id": str(oferta.solicitud_id),
                            "asesor_id": str(oferta.asesor_id),
                            "tiempo_entrega_dias": oferta.tiempo_entrega_dias,
                            "observaciones": oferta.observaciones,
                            "estado": oferta.estado.value,
                            "created_at": oferta.created_at.isoformat(),
                            "updated_at": oferta.updated_at.isoformat(),
                            "detalles": [
                                {
                                    "id": str(det.id),
                                    "oferta_id": str(det.oferta_id),
                                    "repuesto_solicitado_id": str(det.repuesto_solicitado_id),
                                    "precio_unitario": float(det.precio_unitario),
                                    "cantidad": det.cantidad,
                                    "garantia_meses": det.garantia_meses,
                                    "tiempo_entrega_dias": det.tiempo_entrega_dias
                                }
                                for det in oferta.detalles
                            ] if hasattr(oferta, 'detalles') else []
                        }
                        break
            
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
                "mi_oferta": mi_oferta,
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
    async def _validate_and_normalize_municipio(municipio_id: str, ciudad_origen: str) -> tuple[Any, str]:
        """Validate municipio exists and normalize ciudad name."""
        from models.geografia import Municipio
        
        # Validate municipio_id
        municipio_obj = await Municipio.get_or_none(id=municipio_id)
        if not municipio_obj:
            raise ValueError(f"Municipio con ID {municipio_id} no encontrado en base de datos")
            
        # Normalize comparisons
        ciudad_normalizada = Municipio.normalizar_ciudad(ciudad_origen)
        
        # Warn if mismatch creates ambiguity, but prefer DB name
        if municipio_obj.municipio_norm != ciudad_normalizada:
            logger.warning(
                f"Ciudad origen '{ciudad_origen}' (norm: '{ciudad_normalizada}') "
                f"difiere de municipio_id {municipio_id} ('{municipio_obj.municipio_norm}'). "
                f"Se usará nombre oficial: {municipio_obj.municipio_norm}"
            )
            return municipio_obj, municipio_obj.municipio_norm
            
        return municipio_obj, ciudad_origen

    @staticmethod
    async def _get_or_create_client_user(
        cliente_data: Dict[str, Any], 
        municipio_obj: Any, 
        ciudad_origen: str, 
        departamento_origen: str
    ) -> Any:
        """Get existing client or create new user/client profile."""
        from models.user import Usuario, Cliente
        from models.enums import RolUsuario, EstadoUsuario
        
        # Normalize phone
        telefono = cliente_data["telefono"]
        if not telefono.startswith("+57"):
            telefono_digits = ''.join(filter(str.isdigit, telefono))
            telefono = f"+57{telefono_digits[-10:]}"
            
        # Try getting existing user
        usuario = await Usuario.get_or_none(telefono=telefono)
        
        if not usuario:
            # Create new user
            usuario = await Usuario.create(
                email=cliente_data.get("email"),
                password_hash="temp_hash",
                nombre=cliente_data["nombre"].split()[0] if cliente_data["nombre"] else "Cliente",
                apellido=" ".join(cliente_data["nombre"].split()[1:]) if len(cliente_data["nombre"].split()) > 1 else "",
                telefono=telefono,
                rol=RolUsuario.CLIENT,
                estado=EstadoUsuario.ACTIVO
            )
            
        # Get or create client profile
        cliente = await Cliente.get_or_none(usuario=usuario)
        if not cliente:
            cliente = await Cliente.create(
                usuario=usuario,
                municipio=municipio_obj,
                ciudad=ciudad_origen,
                departamento=departamento_origen
            )
            
        return cliente

    @staticmethod
    async def create_solicitud(
        cliente_data: Dict[str, Any],
        municipio_id: str,
        ciudad_origen: str,
        departamento_origen: str,
        repuestos: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create new solicitud with cliente and repuestos.
        Uses atomic transaction for data integrity.
        """
        from models.solicitud import Solicitud, RepuestoSolicitado
        from models.enums import EstadoSolicitud
        from tortoise.transactions import in_transaction

        # 1. Validate geography
        municipio_obj, ciudad_final = await SolicitudesService._validate_and_normalize_municipio(
            municipio_id, ciudad_origen
        )
        
        # 2. Get/Create Client
        cliente = await SolicitudesService._get_or_create_client_user(
            cliente_data, municipio_obj, ciudad_final, departamento_origen
        )
        
        # 3. Create Solicitud + Repuestos in Transaction
        async with in_transaction() as conn:
            solicitud = await Solicitud.create(
                cliente=cliente,
                municipio=municipio_obj,
                estado=EstadoSolicitud.ABIERTA,
                nivel_actual=1,
                ciudad_origen=ciudad_final,
                departamento_origen=departamento_origen,
                ofertas_minimas_deseadas=2,
                timeout_horas=20,
                total_repuestos=len(repuestos),
                monto_total_adjudicado=Decimal("0.00"),
                using_db=conn
            )
            
            for rep_data in repuestos:
                await RepuestoSolicitado.create(
                    solicitud=solicitud,
                    nombre=rep_data["nombre"],
                    codigo=rep_data.get("codigo"),
                    descripcion=rep_data.get("descripcion"),
                    cantidad=rep_data["cantidad"],
                    marca_vehiculo=rep_data["marca_vehiculo"],
                    linea_vehiculo=rep_data["linea_vehiculo"],
                    anio_vehiculo=rep_data["anio_vehiculo"],
                    observaciones=rep_data.get("observaciones"),
                    es_urgente=rep_data.get("es_urgente", False),
                    using_db=conn
                )
        
        # 4. Reload relations
        await solicitud.fetch_related("cliente", "cliente__usuario", "repuestos_solicitados")
        
        # 5. Trigger Escalation (Async/Fire-and-forget logic handled inside)
        if solicitud.estado == EstadoSolicitud.ABIERTA:
            try:
                from services.escalamiento_service import EscalamientoService
                resultado = await EscalamientoService.ejecutar_escalamiento_con_primera_oleada(str(solicitud.id))
                
                if resultado['success']:
                    await solicitud.refresh_from_db()
                    logger.info(f"✅ Escalamiento ejecutado: Nivel {resultado.get('nivel_actual')}")
                else:
                    logger.warning(f"⚠️ Escalamiento falló: {resultado.get('error')}")
            except Exception as e:
                logger.error(f"❌ Error crítico en escalamiento: {e}")
                # Don't fail the request, just log it
        
        # 6. Format Response
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
