"""
PQR Service - Business logic for PQR management
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from decimal import Decimal
import math

from tortoise.expressions import Q
from tortoise.functions import Count, Avg

from models.analytics import PQR, Notificacion
from models.user import Usuario, Cliente
from models.enums import TipoPQR, PrioridadPQR, EstadoPQR
from schemas.pqr import (
    PQRCreate, PQRUpdate, PQRResponse, PQRList, 
    PQRMetrics, ClienteInfo, UsuarioInfo
)


class PQRService:
    
    @staticmethod
    async def get_pqrs(
        page: int = 1,
        limit: int = 50,
        estado: Optional[EstadoPQR] = None,
        tipo: Optional[TipoPQR] = None,
        prioridad: Optional[PrioridadPQR] = None,
        search: Optional[str] = None
    ) -> PQRList:
        """
        Obtener lista de PQRs con filtros y paginación
        """
        query = PQR.all().select_related('cliente__usuario', 'respondido_por')
        
        # Aplicar filtros
        if estado:
            query = query.filter(estado=estado)
        if tipo:
            query = query.filter(tipo=tipo)
        if prioridad:
            query = query.filter(prioridad=prioridad)
        if search:
            query = query.filter(
                Q(resumen__icontains=search) |
                Q(detalle__icontains=search) |
                Q(cliente__usuario__nombre_completo__icontains=search) |
                Q(cliente__telefono__icontains=search)
            )
        
        # Contar total
        total = await query.count()
        
        # Aplicar paginación
        offset = (page - 1) * limit
        pqrs = await query.offset(offset).limit(limit).order_by('-created_at')
        
        # Convertir a response models
        pqr_responses = []
        for pqr in pqrs:
            cliente_info = ClienteInfo(
                id=pqr.cliente.id,
                nombre_completo=pqr.cliente.usuario.nombre_completo,
                telefono=pqr.cliente.telefono,
                email=pqr.cliente.usuario.email
            )
            
            respondido_por_info = None
            if pqr.respondido_por:
                respondido_por_info = UsuarioInfo(
                    id=pqr.respondido_por.id,
                    nombre_completo=pqr.respondido_por.nombre_completo,
                    email=pqr.respondido_por.email
                )
            
            pqr_response = PQRResponse(
                id=pqr.id,
                tipo=pqr.tipo,
                prioridad=pqr.prioridad,
                estado=pqr.estado,
                resumen=pqr.resumen,
                detalle=pqr.detalle,
                cliente=cliente_info,
                respuesta=pqr.respuesta,
                fecha_respuesta=pqr.fecha_respuesta,
                respondido_por=respondido_por_info,
                tiempo_resolucion_horas=pqr.tiempo_resolucion_horas,
                created_at=pqr.created_at,
                updated_at=pqr.updated_at
            )
            pqr_responses.append(pqr_response)
        
        total_pages = math.ceil(total / limit)
        
        return PQRList(
            data=pqr_responses,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages
        )
    
    @staticmethod
    async def get_pqr_metrics() -> PQRMetrics:
        """
        Calcular métricas de PQRs para el dashboard
        """
        # Conteos por estado
        total_abiertas = await PQR.filter(estado=EstadoPQR.ABIERTA).count()
        total_en_proceso = await PQR.filter(estado=EstadoPQR.EN_PROCESO).count()
        total_cerradas = await PQR.filter(estado=EstadoPQR.CERRADA).count()
        
        # PQRs de alta prioridad
        pqrs_alta_prioridad = await PQR.filter(prioridad=PrioridadPQR.ALTA).count()
        pqrs_criticas = await PQR.filter(prioridad=PrioridadPQR.CRITICA).count()
        
        # Tiempo promedio de resolución
        avg_resolution = await PQR.filter(
            estado=EstadoPQR.CERRADA,
            tiempo_resolucion_horas__isnull=False
        ).aggregate(avg_time=Avg('tiempo_resolucion_horas'))
        
        tiempo_promedio_resolucion = Decimal(str(avg_resolution['avg_time'] or 0))
        
        # Tasa de resolución en 24h
        pqrs_resueltas_24h = await PQR.filter(
            estado=EstadoPQR.CERRADA,
            tiempo_resolucion_horas__lte=24
        ).count()
        
        total_resueltas = await PQR.filter(estado=EstadoPQR.CERRADA).count()
        tasa_resolucion_24h = Decimal('0')
        if total_resueltas > 0:
            tasa_resolucion_24h = Decimal(str((pqrs_resueltas_24h / total_resueltas) * 100))
        
        # Distribución por tipo
        tipos_count = await PQR.all().group_by('tipo').annotate(count=Count('id')).values('tipo', 'count')
        distribucion_por_tipo = {item['tipo']: item['count'] for item in tipos_count}
        
        # Distribución por prioridad
        prioridades_count = await PQR.all().group_by('prioridad').annotate(count=Count('id')).values('prioridad', 'count')
        distribucion_por_prioridad = {item['prioridad']: item['count'] for item in prioridades_count}
        
        return PQRMetrics(
            total_abiertas=total_abiertas,
            total_en_proceso=total_en_proceso,
            total_cerradas=total_cerradas,
            tiempo_promedio_resolucion_horas=tiempo_promedio_resolucion,
            pqrs_alta_prioridad=pqrs_alta_prioridad,
            pqrs_criticas=pqrs_criticas,
            tasa_resolucion_24h=tasa_resolucion_24h,
            distribucion_por_tipo=distribucion_por_tipo,
            distribucion_por_prioridad=distribucion_por_prioridad
        )
    
    @staticmethod
    async def get_pqr_by_id(pqr_id: UUID) -> Optional[PQRResponse]:
        """
        Obtener una PQR específica por ID
        """
        pqr = await PQR.filter(id=pqr_id).select_related('cliente__usuario', 'respondido_por').first()
        if not pqr:
            return None
        
        cliente_info = ClienteInfo(
            id=pqr.cliente.id,
            nombre_completo=pqr.cliente.usuario.nombre_completo,
            telefono=pqr.cliente.telefono,
            email=pqr.cliente.usuario.email
        )
        
        respondido_por_info = None
        if pqr.respondido_por:
            respondido_por_info = UsuarioInfo(
                id=pqr.respondido_por.id,
                nombre_completo=pqr.respondido_por.nombre_completo,
                email=pqr.respondido_por.email
            )
        
        return PQRResponse(
            id=pqr.id,
            tipo=pqr.tipo,
            prioridad=pqr.prioridad,
            estado=pqr.estado,
            resumen=pqr.resumen,
            detalle=pqr.detalle,
            cliente=cliente_info,
            respuesta=pqr.respuesta,
            fecha_respuesta=pqr.fecha_respuesta,
            respondido_por=respondido_por_info,
            tiempo_resolucion_horas=pqr.tiempo_resolucion_horas,
            created_at=pqr.created_at,
            updated_at=pqr.updated_at
        )
    
    @staticmethod
    async def create_pqr(pqr_data: PQRCreate) -> PQRResponse:
        """
        Crear una nueva PQR
        """
        # Verificar que el cliente existe
        cliente = await Cliente.filter(id=pqr_data.cliente_id).select_related('usuario').first()
        if not cliente:
            raise ValueError("Cliente no encontrado")
        
        # Crear la PQR
        pqr = await PQR.create(
            cliente_id=pqr_data.cliente_id,
            tipo=pqr_data.tipo,
            prioridad=pqr_data.prioridad,
            resumen=pqr_data.resumen,
            detalle=pqr_data.detalle,
            estado=EstadoPQR.ABIERTA
        )
        
        # Crear notificaciones automáticas para PQRs de alta prioridad
        if pqr_data.prioridad in [PrioridadPQR.ALTA, PrioridadPQR.CRITICA]:
            await PQRService._crear_notificaciones_alta_prioridad(pqr)
        
        # Publicar evento en Redis
        await PQRService._publicar_evento_pqr("pqr.created", pqr.id, {
            "tipo": pqr_data.tipo.value,
            "prioridad": pqr_data.prioridad.value,
            "cliente_id": str(pqr_data.cliente_id)
        }, None)
        
        return await PQRService.get_pqr_by_id(pqr.id)
    
    @staticmethod
    async def update_pqr(pqr_id: UUID, pqr_data: PQRUpdate, usuario_id: UUID) -> Optional[PQRResponse]:
        """
        Actualizar una PQR existente
        """
        pqr = await PQR.filter(id=pqr_id).first()
        if not pqr:
            return None
        
        # Actualizar campos si se proporcionan
        if pqr_data.tipo is not None:
            pqr.tipo = pqr_data.tipo
        if pqr_data.prioridad is not None:
            pqr.prioridad = pqr_data.prioridad
        if pqr_data.resumen is not None:
            pqr.resumen = pqr_data.resumen
        if pqr_data.detalle is not None:
            pqr.detalle = pqr_data.detalle
        if pqr_data.respuesta is not None:
            pqr.respuesta = pqr_data.respuesta
            pqr.fecha_respuesta = datetime.now()
            pqr.respondido_por_id = usuario_id
            pqr.estado = EstadoPQR.EN_PROCESO
            pqr.calcular_tiempo_resolucion()
        
        await pqr.save()
        
        # Publicar evento
        await PQRService._publicar_evento_pqr("pqr.updated", pqr.id, {
            "usuario_id": str(usuario_id)
        }, None)
        
        return await PQRService.get_pqr_by_id(pqr.id)
    
    @staticmethod
    async def responder_pqr(pqr_id: UUID, respuesta: str, usuario_id: UUID) -> Optional[PQRResponse]:
        """
        Responder a una PQR
        """
        pqr = await PQR.filter(id=pqr_id).first()
        if not pqr:
            return None
        
        pqr.respuesta = respuesta
        pqr.fecha_respuesta = datetime.now()
        pqr.respondido_por_id = usuario_id
        pqr.estado = EstadoPQR.EN_PROCESO
        pqr.calcular_tiempo_resolucion()
        
        await pqr.save()
        
        # Publicar evento
        await PQRService._publicar_evento_pqr("pqr.responded", pqr.id, {
            "usuario_id": str(usuario_id),
            "tiempo_resolucion_horas": pqr.tiempo_resolucion_horas
        }, None)
        
        return await PQRService.get_pqr_by_id(pqr.id)
    
    @staticmethod
    async def cambiar_estado(pqr_id: UUID, nuevo_estado: EstadoPQR, usuario_id: UUID) -> Optional[PQRResponse]:
        """
        Cambiar el estado de una PQR
        """
        pqr = await PQR.filter(id=pqr_id).first()
        if not pqr:
            return None
        
        estado_anterior = pqr.estado
        pqr.estado = nuevo_estado
        
        # Si se cierra la PQR, calcular tiempo de resolución
        if nuevo_estado == EstadoPQR.CERRADA and estado_anterior != EstadoPQR.CERRADA:
            pqr.calcular_tiempo_resolucion()
        
        await pqr.save()
        
        # Publicar evento
        await PQRService._publicar_evento_pqr("pqr.status_changed", pqr.id, {
            "estado_anterior": estado_anterior.value,
            "nuevo_estado": nuevo_estado.value,
            "usuario_id": str(usuario_id)
        }, None)
        
        return await PQRService.get_pqr_by_id(pqr.id)
    
    @staticmethod
    async def cambiar_prioridad(pqr_id: UUID, nueva_prioridad: PrioridadPQR, usuario_id: UUID) -> Optional[PQRResponse]:
        """
        Cambiar la prioridad de una PQR
        """
        pqr = await PQR.filter(id=pqr_id).first()
        if not pqr:
            return None
        
        prioridad_anterior = pqr.prioridad
        pqr.prioridad = nueva_prioridad
        await pqr.save()
        
        # Crear notificaciones si se eleva a alta prioridad
        if nueva_prioridad in [PrioridadPQR.ALTA, PrioridadPQR.CRITICA] and prioridad_anterior not in [PrioridadPQR.ALTA, PrioridadPQR.CRITICA]:
            await PQRService._crear_notificaciones_alta_prioridad(pqr)
        
        # Publicar evento
        await PQRService._publicar_evento_pqr("pqr.priority_changed", pqr.id, {
            "prioridad_anterior": prioridad_anterior.value,
            "nueva_prioridad": nueva_prioridad.value,
            "usuario_id": str(usuario_id)
        }, None)
        
        return await PQRService.get_pqr_by_id(pqr.id)
    
    @staticmethod
    async def delete_pqr(pqr_id: UUID) -> bool:
        """
        Eliminar una PQR (soft delete)
        """
        pqr = await PQR.filter(id=pqr_id).first()
        if not pqr:
            return False
        
        await pqr.delete()
        
        # Publicar evento
        await PQRService._publicar_evento_pqr("pqr.deleted", pqr_id, {}, None)
        
        return True
    
    @staticmethod
    async def get_pqrs_by_cliente(cliente_id: UUID) -> List[PQRResponse]:
        """
        Obtener todas las PQRs de un cliente específico
        """
        pqrs = await PQR.filter(cliente_id=cliente_id).select_related('cliente__usuario', 'respondido_por').order_by('-created_at')
        
        pqr_responses = []
        for pqr in pqrs:
            cliente_info = ClienteInfo(
                id=pqr.cliente.id,
                nombre_completo=pqr.cliente.usuario.nombre_completo,
                telefono=pqr.cliente.telefono,
                email=pqr.cliente.usuario.email
            )
            
            respondido_por_info = None
            if pqr.respondido_por:
                respondido_por_info = UsuarioInfo(
                    id=pqr.respondido_por.id,
                    nombre_completo=pqr.respondido_por.nombre_completo,
                    email=pqr.respondido_por.email
                )
            
            pqr_response = PQRResponse(
                id=pqr.id,
                tipo=pqr.tipo,
                prioridad=pqr.prioridad,
                estado=pqr.estado,
                resumen=pqr.resumen,
                detalle=pqr.detalle,
                cliente=cliente_info,
                respuesta=pqr.respuesta,
                fecha_respuesta=pqr.fecha_respuesta,
                respondido_por=respondido_por_info,
                tiempo_resolucion_horas=pqr.tiempo_resolucion_horas,
                created_at=pqr.created_at,
                updated_at=pqr.updated_at
            )
            pqr_responses.append(pqr_response)
        
        return pqr_responses
    
    @staticmethod
    async def _crear_notificaciones_alta_prioridad(pqr: PQR):
        """
        Crear notificaciones automáticas para PQRs de alta prioridad
        """
        # Obtener usuarios administradores y de soporte
        usuarios_soporte = await Usuario.filter(
            rol__in=['ADMIN', 'SUPPORT']
        ).all()
        
        mensaje = f"Nueva PQR de prioridad {pqr.prioridad.value}: {pqr.resumen}"
        
        for usuario in usuarios_soporte:
            await Notificacion.create(
                usuario_id=usuario.id,
                tipo="pqr_alta_prioridad",
                titulo=f"PQR {pqr.prioridad.value}",
                mensaje=mensaje,
                datos_adicionales={
                    "pqr_id": str(pqr.id),
                    "prioridad": pqr.prioridad.value,
                    "tipo": pqr.tipo.value
                },
                url_accion=f"/pqr/{pqr.id}"
            )
    
    @staticmethod
    async def _publicar_evento_pqr(evento: str, pqr_id: UUID, datos: dict, redis_client=None):
        """
        Publicar evento de PQR en Redis
        """
        if not redis_client:
            return
            
        try:
            evento_data = {
                "evento": evento,
                "pqr_id": str(pqr_id),
                "timestamp": datetime.now().isoformat(),
                **datos
            }
            await redis_client.publish("pqr.events", str(evento_data))
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Error publishing PQR event: {e}")