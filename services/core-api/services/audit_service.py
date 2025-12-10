"""
Servicio de auditoría para registrar cambios en entidades
"""
from typing import Any, Dict, Optional
from uuid import UUID
from datetime import datetime
from tortoise.transactions import in_transaction

from models.analytics import LogAuditoria
from utils.logger import get_logger

logger = get_logger()


class AuditService:
    """
    Servicio para gestionar logs de auditoría
    """
    
    @staticmethod
    async def log_auditoria(
        actor_id: UUID,
        accion: str,
        entidad: str,
        entidad_id: UUID,
        diff: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LogAuditoria:
        """
        Registra una acción de auditoría
        
        Args:
            actor_id: ID del usuario que realiza la acción
            accion: Tipo de acción (CREATE, UPDATE, DELETE, etc.)
            entidad: Nombre de la entidad afectada (Solicitud, Oferta, etc.)
            entidad_id: ID de la entidad afectada
            diff: Diccionario con cambios realizados (antes/después)
            metadata: Información adicional sobre la acción
        
        Returns:
            LogAuditoria creado
        """
        try:
            async with in_transaction():
                log = await LogAuditoria.create(
                    actor_id=actor_id,
                    accion=accion,
                    entidad=entidad,
                    entidad_id=entidad_id,
                    diff_json=diff or {},
                    metadata_json=metadata or {},
                    ts=datetime.utcnow()
                )
                
                # Log estructurado
                logger.info(
                    f"Auditoría registrada: {accion} en {entidad}",
                    actor_id=str(actor_id),
                    accion=accion,
                    entidad=entidad,
                    entidad_id=str(entidad_id),
                    audit_log_id=str(log.id)
                )
                
                return log
                
        except Exception as e:
            logger.error(
                f"Error al registrar auditoría: {str(e)}",
                actor_id=str(actor_id),
                accion=accion,
                entidad=entidad,
                entidad_id=str(entidad_id),
                error=str(e)
            )
            raise
    
    @staticmethod
    async def log_create(
        actor_id: UUID,
        entidad: str,
        entidad_id: UUID,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> LogAuditoria:
        """
        Registra creación de entidad
        
        Args:
            actor_id: ID del usuario que crea
            entidad: Nombre de la entidad
            entidad_id: ID de la entidad creada
            data: Datos de la entidad creada
            metadata: Información adicional
        
        Returns:
            LogAuditoria creado
        """
        diff = {
            'before': None,
            'after': data
        }
        
        return await AuditService.log_auditoria(
            actor_id=actor_id,
            accion='CREATE',
            entidad=entidad,
            entidad_id=entidad_id,
            diff=diff,
            metadata=metadata
        )
    
    @staticmethod
    async def log_update(
        actor_id: UUID,
        entidad: str,
        entidad_id: UUID,
        before: Dict[str, Any],
        after: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> LogAuditoria:
        """
        Registra actualización de entidad
        
        Args:
            actor_id: ID del usuario que actualiza
            entidad: Nombre de la entidad
            entidad_id: ID de la entidad actualizada
            before: Estado anterior
            after: Estado posterior
            metadata: Información adicional
        
        Returns:
            LogAuditoria creado
        """
        # Calcular diferencias
        changes = {}
        for key in set(list(before.keys()) + list(after.keys())):
            if before.get(key) != after.get(key):
                changes[key] = {
                    'before': before.get(key),
                    'after': after.get(key)
                }
        
        diff = {
            'before': before,
            'after': after,
            'changes': changes
        }
        
        return await AuditService.log_auditoria(
            actor_id=actor_id,
            accion='UPDATE',
            entidad=entidad,
            entidad_id=entidad_id,
            diff=diff,
            metadata=metadata
        )
    
    @staticmethod
    async def log_delete(
        actor_id: UUID,
        entidad: str,
        entidad_id: UUID,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> LogAuditoria:
        """
        Registra eliminación de entidad
        
        Args:
            actor_id: ID del usuario que elimina
            entidad: Nombre de la entidad
            entidad_id: ID de la entidad eliminada
            data: Datos de la entidad eliminada
            metadata: Información adicional
        
        Returns:
            LogAuditoria creado
        """
        diff = {
            'before': data,
            'after': None
        }
        
        return await AuditService.log_auditoria(
            actor_id=actor_id,
            accion='DELETE',
            entidad=entidad,
            entidad_id=entidad_id,
            diff=diff,
            metadata=metadata
        )
    
    @staticmethod
    async def log_estado_change(
        actor_id: UUID,
        entidad: str,
        entidad_id: UUID,
        estado_anterior: str,
        estado_nuevo: str,
        razon: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LogAuditoria:
        """
        Registra cambio de estado de entidad
        
        Args:
            actor_id: ID del usuario que cambia el estado
            entidad: Nombre de la entidad
            entidad_id: ID de la entidad
            estado_anterior: Estado anterior
            estado_nuevo: Estado nuevo
            razon: Razón del cambio
            metadata: Información adicional
        
        Returns:
            LogAuditoria creado
        """
        diff = {
            'before': {'estado': estado_anterior},
            'after': {'estado': estado_nuevo},
            'changes': {
                'estado': {
                    'before': estado_anterior,
                    'after': estado_nuevo
                }
            }
        }
        
        if razon:
            if metadata is None:
                metadata = {}
            metadata['razon'] = razon
        
        return await AuditService.log_auditoria(
            actor_id=actor_id,
            accion='ESTADO_CHANGE',
            entidad=entidad,
            entidad_id=entidad_id,
            diff=diff,
            metadata=metadata
        )
    
    @staticmethod
    async def get_audit_trail(
        entidad: str,
        entidad_id: UUID,
        limit: int = 100
    ) -> list[LogAuditoria]:
        """
        Obtiene el historial de auditoría de una entidad
        
        Args:
            entidad: Nombre de la entidad
            entidad_id: ID de la entidad
            limit: Número máximo de registros
        
        Returns:
            Lista de logs de auditoría ordenados por fecha descendente
        """
        logs = await LogAuditoria.filter(
            entidad=entidad,
            entidad_id=entidad_id
        ).order_by('-ts').limit(limit)
        
        return logs
    
    @staticmethod
    async def get_actor_actions(
        actor_id: UUID,
        limit: int = 100
    ) -> list[LogAuditoria]:
        """
        Obtiene las acciones realizadas por un actor
        
        Args:
            actor_id: ID del actor
            limit: Número máximo de registros
        
        Returns:
            Lista de logs de auditoría ordenados por fecha descendente
        """
        logs = await LogAuditoria.filter(
            actor_id=actor_id
        ).order_by('-ts').limit(limit)
        
        return logs


# Instancia global del servicio
audit_service = AuditService()
