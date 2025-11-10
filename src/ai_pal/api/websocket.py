"""
WebSocket implementation for real-time dashboard updates

Provides real-time notifications for:
- Background task status changes
- Goal progress updates
- System health changes
- Audit events (critical only)
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Set, Dict, Any, Optional
from datetime import datetime
import json
import asyncio
from enum import Enum
from pydantic import BaseModel, Field
from ai_pal.monitoring import get_logger

logger = get_logger("ai_pal.api.websocket")


class EventType(str, Enum):
    """WebSocket event types"""
    TASK_STATUS_CHANGED = "task_status_changed"
    GOAL_UPDATED = "goal_updated"
    GOAL_COMPLETED = "goal_completed"
    SYSTEM_HEALTH_CHANGED = "system_health_changed"
    CRITICAL_EVENT = "critical_event"
    HEARTBEAT = "heartbeat"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"


class WebSocketEvent(BaseModel):
    """WebSocket event message"""
    type: EventType = Field(..., description="Event type")
    timestamp: str = Field(..., description="Event timestamp")
    user_id: Optional[str] = Field(None, description="User ID (if applicable)")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps({
            "type": self.type.value,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "data": self.data,
            "metadata": self.metadata,
        })


class ConnectionManager:
    """Manages WebSocket connections and broadcasting"""

    def __init__(self):
        """Initialize connection manager"""
        # Store active connections: {user_id: set(websockets)}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Broadcast connections (not user-specific)
        self.broadcast_connections: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None):
        """
        Register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: User ID if connection is user-specific
        """
        await websocket.accept()

        async with self._lock:
            if user_id:
                if user_id not in self.active_connections:
                    self.active_connections[user_id] = set()
                self.active_connections[user_id].add(websocket)
                logger.info(f"User {user_id} connected. Total connections: {len(self.active_connections[user_id])}")
            else:
                self.broadcast_connections.add(websocket)
                logger.info(f"Broadcast connection added. Total: {len(self.broadcast_connections)}")

        # Send welcome message
        welcome_event = WebSocketEvent(
            type=EventType.CONNECTED,
            timestamp=datetime.utcnow().isoformat() + "Z",
            user_id=user_id,
            data={"message": "Connected to AI-PAL real-time updates"},
        )
        await websocket.send_text(welcome_event.to_json())

    async def disconnect(self, websocket: WebSocket, user_id: Optional[str] = None):
        """
        Unregister a WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: User ID if connection is user-specific
        """
        async with self._lock:
            if user_id and user_id in self.active_connections:
                self.active_connections[user_id].discard(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                logger.info(f"User {user_id} disconnected")
            else:
                self.broadcast_connections.discard(websocket)
                logger.info(f"Broadcast connection removed")

    async def send_personal_message(self, user_id: str, event: WebSocketEvent):
        """
        Send a message to a specific user's connections.

        Args:
            user_id: User ID
            event: Event to send
        """
        async with self._lock:
            if user_id in self.active_connections:
                disconnected = set()
                for connection in self.active_connections[user_id]:
                    try:
                        await connection.send_text(event.to_json())
                    except Exception as e:
                        logger.error(f"Error sending message to {user_id}: {e}")
                        disconnected.add(connection)

                # Clean up disconnected connections
                self.active_connections[user_id] -= disconnected

    async def broadcast(self, event: WebSocketEvent):
        """
        Broadcast a message to all connections.

        Args:
            event: Event to broadcast
        """
        async with self._lock:
            # Broadcast to broadcast connections
            disconnected = set()
            for connection in self.broadcast_connections:
                try:
                    await connection.send_text(event.to_json())
                except Exception as e:
                    logger.error(f"Error broadcasting: {e}")
                    disconnected.add(connection)

            self.broadcast_connections -= disconnected

            # Also broadcast to all user connections
            for user_id, connections in self.active_connections.items():
                user_disconnected = set()
                for connection in connections:
                    try:
                        await connection.send_text(event.to_json())
                    except Exception as e:
                        logger.error(f"Error sending to {user_id}: {e}")
                        user_disconnected.add(connection)

                self.active_connections[user_id] -= user_disconnected

    async def heartbeat(self, user_id: Optional[str] = None):
        """
        Send periodic heartbeat to keep connections alive.

        Args:
            user_id: User ID (if None, broadcasts to all)
        """
        event = WebSocketEvent(
            type=EventType.HEARTBEAT,
            timestamp=datetime.utcnow().isoformat() + "Z",
            user_id=user_id,
            data={"status": "alive"},
        )

        if user_id:
            await self.send_personal_message(user_id, event)
        else:
            await self.broadcast(event)

    def get_connection_count(self, user_id: Optional[str] = None) -> int:
        """
        Get the number of active connections.

        Args:
            user_id: User ID (if None, returns total count)

        Returns:
            Number of active connections
        """
        if user_id:
            return len(self.active_connections.get(user_id, set()))
        return len(self.broadcast_connections) + sum(
            len(conns) for conns in self.active_connections.values()
        )


# Global connection manager
manager = ConnectionManager()


# ===== EVENT CREATORS =====

def create_task_status_event(
    task_id: str,
    task_type: str,
    status: str,
    user_id: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
) -> WebSocketEvent:
    """Create a task status changed event"""
    return WebSocketEvent(
        type=EventType.TASK_STATUS_CHANGED,
        timestamp=datetime.utcnow().isoformat() + "Z",
        user_id=user_id,
        data={
            "task_id": task_id,
            "task_type": task_type,
            "status": status,
            "result": result,
        },
        metadata={"category": "task"},
    )


def create_goal_update_event(
    goal_id: str,
    goal_title: str,
    progress: float,
    user_id: Optional[str] = None,
) -> WebSocketEvent:
    """Create a goal update event"""
    return WebSocketEvent(
        type=EventType.GOAL_UPDATED,
        timestamp=datetime.utcnow().isoformat() + "Z",
        user_id=user_id,
        data={
            "goal_id": goal_id,
            "goal_title": goal_title,
            "progress": progress,
        },
        metadata={"category": "goal"},
    )


def create_goal_completed_event(
    goal_id: str,
    goal_title: str,
    user_id: Optional[str] = None,
) -> WebSocketEvent:
    """Create a goal completed event"""
    return WebSocketEvent(
        type=EventType.GOAL_COMPLETED,
        timestamp=datetime.utcnow().isoformat() + "Z",
        user_id=user_id,
        data={
            "goal_id": goal_id,
            "goal_title": goal_title,
        },
        metadata={"category": "goal", "importance": "high"},
    )


def create_health_changed_event(
    service: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
) -> WebSocketEvent:
    """Create a system health changed event"""
    return WebSocketEvent(
        type=EventType.SYSTEM_HEALTH_CHANGED,
        timestamp=datetime.utcnow().isoformat() + "Z",
        data={
            "service": service,
            "status": status,
            "details": details or {},
        },
        metadata={"category": "system"},
    )


def create_critical_event(
    event_type: str,
    message: str,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> WebSocketEvent:
    """Create a critical event notification"""
    return WebSocketEvent(
        type=EventType.CRITICAL_EVENT,
        timestamp=datetime.utcnow().isoformat() + "Z",
        user_id=user_id,
        data={
            "event_type": event_type,
            "message": message,
            "details": details or {},
        },
        metadata={"category": "alert", "severity": "critical"},
    )


# ===== BACKGROUND TASKS =====

async def heartbeat_loop():
    """Background task: send periodic heartbeats to keep connections alive"""
    while True:
        try:
            await asyncio.sleep(30)  # Every 30 seconds
            await manager.heartbeat()
        except Exception as e:
            logger.error(f"Error in heartbeat loop: {e}")


async def start_heartbeat_task():
    """Start the heartbeat background task"""
    try:
        asyncio.create_task(heartbeat_loop())
        logger.info("Heartbeat task started")
    except Exception as e:
        logger.error(f"Failed to start heartbeat task: {e}")


# ===== WEBSOCKET HELPER FUNCTIONS =====

async def notify_task_status_change(
    task_id: str,
    task_type: str,
    status: str,
    user_id: Optional[str] = None,
    result: Optional[Dict[str, Any]] = None,
):
    """
    Notify about a task status change.

    Used by task endpoints to notify connected clients.

    Args:
        task_id: Task ID
        task_type: Type of task
        status: New status
        user_id: User ID (if applicable)
        result: Task result (if applicable)
    """
    event = create_task_status_event(task_id, task_type, status, user_id, result)

    if user_id:
        await manager.send_personal_message(user_id, event)
    else:
        await manager.broadcast(event)

    logger.info(f"Task {task_id} status changed to {status}")


async def notify_goal_update(
    goal_id: str,
    goal_title: str,
    progress: float,
    user_id: Optional[str] = None,
):
    """
    Notify about a goal update.

    Used by goal endpoints to notify connected clients.

    Args:
        goal_id: Goal ID
        goal_title: Goal title
        progress: Progress percentage
        user_id: User ID (if applicable)
    """
    event = create_goal_update_event(goal_id, goal_title, progress, user_id)

    if user_id:
        await manager.send_personal_message(user_id, event)
    else:
        await manager.broadcast(event)

    logger.info(f"Goal {goal_id} progress updated to {progress}%")


async def notify_goal_completed(
    goal_id: str,
    goal_title: str,
    user_id: Optional[str] = None,
):
    """
    Notify about a goal completion.

    Used by goal endpoints to notify connected clients.

    Args:
        goal_id: Goal ID
        goal_title: Goal title
        user_id: User ID (if applicable)
    """
    event = create_goal_completed_event(goal_id, goal_title, user_id)

    if user_id:
        await manager.send_personal_message(user_id, event)
    else:
        await manager.broadcast(event)

    logger.info(f"Goal {goal_id} completed")


async def notify_critical_event(
    event_type: str,
    message: str,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
):
    """
    Notify about a critical event.

    Used throughout the system to alert about critical issues.

    Args:
        event_type: Type of critical event
        message: Event message
        user_id: User ID (if applicable)
        details: Additional details
    """
    event = create_critical_event(event_type, message, user_id, details)

    if user_id:
        await manager.send_personal_message(user_id, event)
    else:
        await manager.broadcast(event)

    logger.warning(f"Critical event: {event_type} - {message}")
