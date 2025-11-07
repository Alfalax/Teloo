"""
Conversation management data models
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from app.models.llm import ProcessedData


class ConversationState(str, Enum):
    """Conversation states"""
    STARTED = "started"
    GATHERING_INFO = "gathering_info"
    COMPLETE = "complete"
    CREATING_SOLICITUD = "creating_solicitud"
    SOLICITUD_CREATED = "solicitud_created"
    AWAITING_RESULTS = "awaiting_results"
    RESULTS_SENT = "results_sent"
    CLOSED = "closed"


class MessageTurn(BaseModel):
    """Single message turn in conversation"""
    message_id: str
    timestamp: datetime
    from_user: bool  # True if from user, False if from system
    content: str
    message_type: str = "text"
    processed_data: Optional[ProcessedData] = None


class ConversationContext(BaseModel):
    """Conversation context and state"""
    phone_number: str
    state: ConversationState = ConversationState.STARTED
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Message history
    turns: List[MessageTurn] = []
    
    # Accumulated data
    accumulated_repuestos: List[Dict[str, Any]] = []
    accumulated_vehiculo: Optional[Dict[str, str]] = None
    accumulated_cliente: Optional[Dict[str, str]] = None
    
    # Completeness tracking
    missing_fields: List[str] = []
    completeness_score: float = 0.0
    
    # Solicitud tracking
    solicitud_id: Optional[str] = None
    
    # Metadata
    total_turns: int = 0
    last_activity: datetime = Field(default_factory=datetime.now)
    
    def add_turn(self, turn: MessageTurn):
        """Add a turn to the conversation"""
        self.turns.append(turn)
        self.total_turns += 1
        self.last_activity = datetime.now()
        self.updated_at = datetime.now()
    
    def get_latest_user_message(self) -> Optional[MessageTurn]:
        """Get the latest message from user"""
        for turn in reversed(self.turns):
            if turn.from_user:
                return turn
        return None
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation"""
        summary_parts = []
        
        if self.accumulated_repuestos:
            repuestos_names = [r.get("nombre", "repuesto") for r in self.accumulated_repuestos]
            summary_parts.append(f"Repuestos: {', '.join(repuestos_names)}")
        
        if self.accumulated_vehiculo:
            vehiculo_str = f"{self.accumulated_vehiculo.get('marca', '')} {self.accumulated_vehiculo.get('linea', '')} {self.accumulated_vehiculo.get('anio', '')}".strip()
            if vehiculo_str:
                summary_parts.append(f"Vehículo: {vehiculo_str}")
        
        if self.accumulated_cliente:
            cliente_parts = []
            if self.accumulated_cliente.get("nombre"):
                cliente_parts.append(self.accumulated_cliente["nombre"])
            if self.accumulated_cliente.get("ciudad"):
                cliente_parts.append(self.accumulated_cliente["ciudad"])
            if cliente_parts:
                summary_parts.append(f"Cliente: {', '.join(cliente_parts)}")
        
        return " | ".join(summary_parts) if summary_parts else "Conversación iniciada"


class ConversationStats(BaseModel):
    """Conversation statistics"""
    total_conversations: int = 0
    active_conversations: int = 0
    completed_conversations: int = 0
    avg_turns_per_conversation: float = 0.0
    avg_completion_time_minutes: float = 0.0
    completion_rate: float = 0.0