"""
SportSync AI - MCP (Model Context Protocol) Server
Exposes Dual-AI system through standardized protocol

ARCHITECTURE:
- Reasoning AI (o1-preview): Deep personality analysis
- Intelligence AI (GPT-4): Creative sport generation
- MCP Protocol: Standard communication interface
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any
import json
import asyncio
from datetime import datetime

# Create MCP server
mcp_app = FastAPI(
    title="SportSync AI - MCP Server",
    description="Model Context Protocol server for Dual-AI sports recommendation system",
    version="1.0"
)

# CORS
mcp_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection manager for WebSocket
class MCPConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.session_data: Dict[str, Any] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.session_data[client_id] = {
            "connected_at": datetime.utcnow().isoformat(),
            "messages": []
        }

    def disconnect(self, websocket: WebSocket, client_id: str):
        self.active_connections.remove(websocket)
        if client_id in self.session_data:
            del self.session_data[client_id]

    async def send_message(self, websocket: WebSocket, message: Dict[str, Any]):
        await websocket.send_json(message)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = MCPConnectionManager()

# ═══════════════════════════════════════════════════════════════
# MCP PROTOCOL ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@mcp_app.get("/mcp/health")
async def mcp_health():
    """MCP Health Check"""
    return {
        "status": "healthy",
        "protocol": "MCP v1.0",
        "services": {
            "reasoning_ai": "o1-preview",
            "intelligence_ai": "gpt-4"
        },
        "active_connections": len(manager.active_connections)
    }

@mcp_app.get("/mcp/capabilities")
async def mcp_capabilities():
    """Expose MCP capabilities"""
    return {
        "version": "1.0",
        "capabilities": {
            "personality_analysis": {
                "model": "o1-preview",
                "features": ["deep_reasoning", "psychological_insights", "core_drivers", "hidden_motivations"]
            },
            "sport_generation": {
                "model": "gpt-4",
                "features": ["unique_sports", "hybrid_activities", "8_billion_identities", "creative_combinations"]
            },
            "dual_ai_orchestration": True,
            "real_time_communication": True,
            "websocket_support": True
        },
        "supported_languages": ["ar", "en"],
        "max_concurrent_sessions": 100
    }

@mcp_app.post("/mcp/analyze")
async def mcp_analyze(request: dict):
    """
    MCP Analyze Endpoint

    Receives personality data and returns dual-AI analysis
    """
    try:
        answers = request.get("answers", [])
        language = request.get("language", "ar")
        session_id = request.get("session_id", "")

        # Import main API functions
        from api.index import calculate_personality_scores, recommend_sports

        # Calculate personality
        z_scores = calculate_personality_scores(answers)

        # Dual-AI analysis
        ai_results = recommend_sports(z_scores, language, answers)

        return {
            "success": True,
            "session_id": session_id,
            "protocol": "MCP v1.0",
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "personality_scores": z_scores,
                "reasoning_analysis": ai_results["reasoning_analysis"],
                "recommended_sports": ai_results["sports"]
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "protocol": "MCP v1.0"
        }

@mcp_app.websocket("/mcp/stream/{client_id}")
async def mcp_websocket(websocket: WebSocket, client_id: str):
    """
    MCP WebSocket Streaming

    Real-time communication with dual-AI system
    """
    await manager.connect(websocket, client_id)

    try:
        # Send connection confirmation
        await manager.send_message(websocket, {
            "type": "connection_established",
            "client_id": client_id,
            "protocol": "MCP v1.0",
            "timestamp": datetime.utcnow().isoformat()
        })

        while True:
            # Receive data from client
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == "analyze":
                # Stream analysis progress
                await manager.send_message(websocket, {
                    "type": "analysis_started",
                    "timestamp": datetime.utcnow().isoformat()
                })

                # Step 1: Reasoning AI
                await manager.send_message(websocket, {
                    "type": "reasoning_ai_processing",
                    "message": "Analyzing personality with o1-preview...",
                    "timestamp": datetime.utcnow().isoformat()
                })

                # Import and calculate
                from api.index import calculate_personality_scores, analyze_personality_with_reasoning_ai

                answers = data.get("answers", [])
                language = data.get("language", "ar")

                z_scores = calculate_personality_scores(answers)
                reasoning = analyze_personality_with_reasoning_ai(z_scores, answers, language)

                await manager.send_message(websocket, {
                    "type": "reasoning_complete",
                    "data": reasoning,
                    "timestamp": datetime.utcnow().isoformat()
                })

                # Step 2: Intelligence AI
                await manager.send_message(websocket, {
                    "type": "intelligence_ai_processing",
                    "message": "Generating unique sports with GPT-4...",
                    "timestamp": datetime.utcnow().isoformat()
                })

                from api.index import generate_unique_sports_with_ai
                sports = generate_unique_sports_with_ai(z_scores, language, reasoning)

                await manager.send_message(websocket, {
                    "type": "intelligence_complete",
                    "data": sports,
                    "timestamp": datetime.utcnow().isoformat()
                })

                # Final result
                await manager.send_message(websocket, {
                    "type": "analysis_complete",
                    "data": {
                        "personality_scores": z_scores,
                        "reasoning_analysis": reasoning,
                        "recommended_sports": sports
                    },
                    "timestamp": datetime.utcnow().isoformat()
                })

            elif message_type == "ping":
                await manager.send_message(websocket, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, client_id)
        print(f"Client {client_id} disconnected from MCP server")

# ═══════════════════════════════════════════════════════════════
# MCP SERVER INFO
# ═══════════════════════════════════════════════════════════════

@mcp_app.get("/")
def mcp_root():
    return {
        "name": "SportSync AI - MCP Server",
        "version": "1.0",
        "protocol": "Model Context Protocol",
        "description": "Dual-AI sports recommendation system with real-time communication",
        "endpoints": {
            "/mcp/health": "Health check",
            "/mcp/capabilities": "Server capabilities",
            "/mcp/analyze": "Personality analysis (POST)",
            "/mcp/stream/{client_id}": "WebSocket streaming"
        },
        "architecture": {
            "reasoning_ai": "o1-preview (Deep personality analysis)",
            "intelligence_ai": "gpt-4 (Creative sport generation)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mcp_app, host="0.0.0.0", port=8000)
