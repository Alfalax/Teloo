"""
Context Manager Service
Maneja el contexto conversacional de cada usuario para interpretación inteligente
"""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import httpx
import os
from app.core.redis import get_redis

import logging
logger = logging.getLogger(__name__)


class ContextManager:
    """Gestiona el contexto conversacional de usuarios"""
    
    def __init__(self):
        self.redis = None
        
    async def _get_redis(self):
        """Get Redis connection"""
        if not self.redis:
            self.redis = await get_redis()
        return self.redis
    
    async def get_conversation_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Obtiene historial de conversación del usuario"""
        try:
            redis = await self._get_redis()
            key = f"conversation:{user_id}"
            
            # Get last N messages
            messages = await redis.lrange(key, -limit, -1)
            
            history = []
            for msg in messages:
                try:
                    history.append(json.loads(msg))
                except:
                    continue
                    
            return history
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def add_message(self, user_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Agrega mensaje al historial"""
        try:
            redis = await self._get_redis()
            key = f"conversation:{user_id}"
            
            message = {
                "role": role,  # user | assistant
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            await redis.rpush(key, json.dumps(message))
            await redis.expire(key, 86400)  # 24 hours
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
    
    async def get_pending_actions(self, user_id: str) -> Dict:
        """Obtiene acciones pendientes del usuario"""
        try:
            redis = await self._get_redis()
            key = f"pending_actions:{user_id}"
            
            data = await redis.get(key)
            if data:
                return json.loads(data)
            return {}
        except Exception as e:
            logger.error(f"Error getting pending actions: {e}")
            return {}
    
    async def set_pending_action(self, user_id: str, action_type: str, data: Dict, ttl: int = 3600):
        """Establece una acción pendiente"""
        try:
            redis = await self._get_redis()
            key = f"pending_actions:{user_id}"
            
            pending = {
                "type": action_type,  # creating_request | awaiting_offer_response | correcting_data
                "data": data,
                "created_at": datetime.now().isoformat()
            }
            
            await redis.setex(key, ttl, json.dumps(pending))
            
        except Exception as e:
            logger.error(f"Error setting pending action: {e}")
    
    async def clear_pending_action(self, user_id: str):
        """Limpia acciones pendientes"""
        try:
            redis = await self._get_redis()
            key = f"pending_actions:{user_id}"
            await redis.delete(key)
        except Exception as e:
            logger.error(f"Error clearing pending action: {e}")
    
    async def interpret_with_context(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Usa GPT-4 para interpretar mensaje con contexto completo
        
        Returns:
            {
                "intent": "create_request|respond_offers|correct_data|query|confirm",
                "action": "descripción",
                "confidence": 0.0-1.0,
                "extracted_data": {...}
            }
        """
        try:
            # Get context
            history = await self.get_conversation_history(user_id, limit=5)
            pending = await self.get_pending_actions(user_id)
            
            # Build context summary
            history_text = "\n".join([
                f"{'Usuario' if h['role'] == 'user' else 'Asistente'}: {h['content'][:100]}"
                for h in history[-5:]
            ])
            
            pending_text = "Ninguna"
            if pending:
                if pending.get("type") == "creating_request":
                    pending_text = f"Creando solicitud - Faltan: {', '.join(pending.get('data', {}).get('missing_fields', []))}"
                elif pending.get("type") == "awaiting_offer_response":
                    pending_text = f"Esperando respuesta a ofertas de solicitud {pending.get('data', {}).get('solicitud_id', 'N/A')}"
            
            # Create prompt for GPT-4
            prompt = f"""Eres un asistente inteligente de TeLOO que ayuda a clientes a cotizar repuestos de vehículos.

HISTORIAL RECIENTE:
{history_text if history_text else "Primera interacción"}

ACCIÓN PENDIENTE:
{pending_text}

MENSAJE ACTUAL DEL USUARIO:
"{message}"

Analiza el mensaje considerando el contexto y determina la intención real del usuario.

INTENCIONES POSIBLES:
- create_request: Usuario quiere crear nueva solicitud de repuestos
- respond_offers: Usuario responde a ofertas recibidas (acepta/rechaza)
- correct_data: Usuario corrige un dato de la solicitud en creación
- confirm: Usuario confirma que los datos están correctos
- query: Usuario hace una pregunta o consulta
- cancel: Usuario quiere CANCELAR COMPLETAMENTE y NO continuar (ej: "ya no quiero", "déjalo", "olvídalo", "no voy a hacer solicitud")

REGLAS CRÍTICAS:
1. CANCEL vs REINICIAR: Si el usuario dice "ya no quiero", "no voy a hacer solicitud", "déjalo", "olvídalo" = es CANCEL (terminar todo)
2. Si dice "empecemos de nuevo", "reiniciar", "otra vez" = es create_request (nueva solicitud)
3. Si hay acción pendiente "creating_request" y el mensaje es un número de teléfono (10 dígitos), es "correct_data"
4. Si hay acción pendiente "awaiting_offer_response" y el mensaje contiene "acepto/si/ok", es "respond_offers"
5. Si el mensaje menciona repuestos/vehículo/marca sin acción pendiente, es "create_request"
6. Palabras como "si/confirmar/correcto/listo" después de mostrar resumen = "confirm"
7. Un número solo (sin contexto claro) probablemente es "correct_data" si falta un dato numérico

Responde SOLO con JSON válido (sin markdown):
{{
    "intent": "create_request|respond_offers|correct_data|query|confirm|cancel",
    "action": "descripción breve de qué hacer",
    "confidence": 0.95,
    "extracted_data": {{
        "field": "telefono|nombre|ciudad|etc",
        "value": "valor extraído si aplica"
    }},
    "reasoning": "breve explicación del razonamiento"
}}"""

            # Call OpenAI API
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if not openai_api_key:
                logger.warning("OPENAI_API_KEY not found, using fallback")
                return self._fallback_interpretation(message, pending)
            
            logger.info(f"🤖 Interpretando con GPT-4: '{message[:50]}...'")
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {openai_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",  # Más barato pero muy capaz
                        "messages": [
                            {
                                "role": "system",
                                "content": "Eres un experto en interpretar intenciones de usuarios en conversaciones. Respondes SOLO con JSON válido."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.3,
                        "max_tokens": 300
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content'].strip()
                    
                    # Remove markdown if present
                    content = content.replace('```json', '').replace('```', '').strip()
                    
                    interpretation = json.loads(content)
                    logger.info(f"✅ Interpretación: {interpretation['intent']} - {interpretation['action']}")
                    
                    return interpretation
                else:
                    logger.error(f"OpenAI API error: {response.status_code}")
                    return self._fallback_interpretation(message, pending)
                    
        except Exception as e:
            logger.error(f"Error in context interpretation: {e}")
            return self._fallback_interpretation(message, pending)
    
    def _fallback_interpretation(self, message: str, pending: Dict) -> Dict:
        """Interpretación simple sin GPT-4"""
        message_lower = message.lower().strip()
        
        # Check for phone number
        if message.isdigit() and len(message) == 10:
            return {
                "intent": "correct_data",
                "action": "Actualizar teléfono",
                "confidence": 0.8,
                "extracted_data": {"field": "telefono", "value": message},
                "reasoning": "Número de 10 dígitos detectado"
            }
        
        # Check for confirmation
        if any(word in message_lower for word in ['si', 'sí', 'confirmar', 'correcto', 'ok', 'listo', 'dale']):
            if pending and pending.get("type") == "creating_request":
                return {
                    "intent": "confirm",
                    "action": "Confirmar datos de solicitud",
                    "confidence": 0.9,
                    "extracted_data": {},
                    "reasoning": "Palabra de confirmación detectada"
                }
            elif pending and pending.get("type") == "awaiting_offer_response":
                return {
                    "intent": "respond_offers",
                    "action": "Aceptar ofertas",
                    "confidence": 0.9,
                    "extracted_data": {"response_type": "accept_all"},
                    "reasoning": "Confirmación en contexto de ofertas"
                }
        
        # Default
        return {
            "intent": "query",
            "action": "Consulta general",
            "confidence": 0.5,
            "extracted_data": {},
            "reasoning": "No se pudo determinar intención clara"
        }


# Singleton instance
_context_manager = None

def get_context_manager() -> ContextManager:
    """Get singleton instance"""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager
