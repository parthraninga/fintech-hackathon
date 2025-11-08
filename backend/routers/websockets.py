"""
WebSocket router for real-time updates
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, Set
import json
import asyncio

from database import get_db
from models.invoice import Invoice
from models.batch import Batch

router = APIRouter()


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        # Store connections by type and ID
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, connection_type: str, connection_id: int):
        """Accept and store new connection"""
        await websocket.accept()
        
        key = f"{connection_type}:{connection_id}"
        if key not in self.active_connections:
            self.active_connections[key] = set()
        
        self.active_connections[key].add(websocket)
    
    def disconnect(self, websocket: WebSocket, connection_type: str, connection_id: int):
        """Remove connection"""
        key = f"{connection_type}:{connection_id}"
        if key in self.active_connections:
            self.active_connections[key].discard(websocket)
            
            # Clean up empty sets
            if not self.active_connections[key]:
                del self.active_connections[key]
    
    async def send_message(self, message: dict, connection_type: str, connection_id: int):
        """Send message to all connections of a specific type/ID"""
        key = f"{connection_type}:{connection_id}"
        
        if key in self.active_connections:
            dead_connections = set()
            
            for connection in self.active_connections[key]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.add(connection)
            
            # Clean up dead connections
            for connection in dead_connections:
                self.active_connections[key].discard(connection)


# Create global connection manager
manager = ConnectionManager()


@router.websocket("/invoices/{invoice_id}")
async def invoice_websocket(websocket: WebSocket, invoice_id: int):
    """
    WebSocket endpoint for real-time invoice updates
    """
    await manager.connect(websocket, "invoice", invoice_id)
    
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            
            # Echo back for testing
            await websocket.send_json({
                "type": "ack",
                "invoice_id": invoice_id,
                "message": f"Received: {data}"
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "invoice", invoice_id)


@router.websocket("/batches/{batch_id}")
async def batch_websocket(websocket: WebSocket, batch_id: int):
    """
    WebSocket endpoint for real-time batch updates
    """
    await manager.connect(websocket, "batch", batch_id)
    
    try:
        # Send initial batch status
        # In production, get actual batch data from database
        await websocket.send_json({
            "type": "status",
            "batch_id": batch_id,
            "status": "processing",
            "progress": 0
        })
        
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Echo back
            await websocket.send_json({
                "type": "ack",
                "batch_id": batch_id,
                "message": f"Received: {data}"
            })
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, "batch", batch_id)


@router.websocket("/dashboard/metrics")
async def dashboard_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for streaming dashboard metrics
    """
    await websocket.accept()
    
    try:
        # Stream metrics every 5 seconds
        while True:
            # In production, get actual metrics from database
            metrics = {
                "type": "metrics_update",
                "timestamp": str(asyncio.get_event_loop().time()),
                "total_invoices": 1250,
                "processed": 980,
                "flagged": 45,
                "processing_rate": 125.5
            }
            
            await websocket.send_json(metrics)
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        pass


@router.websocket("/chat")
async def chat_websocket(websocket: WebSocket, batch_id: int = Query(...)):
    """
    WebSocket endpoint for streaming chat responses
    """
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Simulate streaming response
            response_text = f"Processing your request: {message.get('content', '')}"
            
            # Send response in chunks (simulate streaming)
            words = response_text.split()
            for i, word in enumerate(words):
                await websocket.send_json({
                    "type": "content",
                    "content": word + " ",
                    "done": False
                })
                await asyncio.sleep(0.1)  # Simulate typing delay
            
            # Send completion message
            await websocket.send_json({
                "type": "complete",
                "done": True
            })
            
    except WebSocketDisconnect:
        pass


# Helper function to broadcast invoice updates
async def broadcast_invoice_update(invoice_id: int, update_data: dict):
    """
    Broadcast invoice update to all connected clients
    Call this from your invoice processing service
    """
    await manager.send_message(update_data, "invoice", invoice_id)


# Helper function to broadcast batch updates
async def broadcast_batch_update(batch_id: int, update_data: dict):
    """
    Broadcast batch update to all connected clients
    Call this from your batch processing service
    """
    await manager.send_message(update_data, "batch", batch_id)
