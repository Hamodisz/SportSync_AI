"""
SportSync AI - MCP (Model Context Protocol) Server with INTERNET RESEARCH
Bulletproof analysis powered by real web research

ARCHITECTURE:
- Internet Research Engine: Web search + Scientific papers
- Reasoning AI (o1-preview): Deep personality analysis
- Intelligence AI (GPT-4): Creative sport generation
- Adaptive Chat: Asks follow-up questions if data insufficient
- MCP Protocol: Standard communication interface
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any
import json
import asyncio
from datetime import datetime
import openai
import os

# Import research engine
from mcp_research import MCPResearchEngine

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

# Initialize research engine
research_engine = MCPResearchEngine()

# Adaptive Chat Engine
class AdaptiveChatEngine:
    """
    Asks follow-up questions when initial data is insufficient
    """

    def __init__(self):
        self.openai_key = os.environ.get("OPENAI_API_KEY")

    def check_data_sufficiency(self, research_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if research data is sufficient for bulletproof analysis
        """
        total_sources = research_results.get("total_sources_consulted", 0)
        specific_sports = len(research_results.get("specific_sport_research", []))

        is_sufficient = total_sources >= 10 and specific_sports >= 3

        return {
            "is_sufficient": is_sufficient,
            "total_sources": total_sources,
            "specific_sports_found": specific_sports,
            "confidence": "HIGH" if is_sufficient else "LOW",
            "needs_follow_up": not is_sufficient
        }

    async def generate_follow_up_questions(
        self,
        z_scores: Dict[str, float],
        personality_type: str,
        current_answers: List[Dict],
        research_gaps: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate intelligent follow-up questions using GPT-4
        """
        if not self.openai_key:
            # Default follow-up questions
            return [
                {
                    "question_en": "Can you describe a recent physical activity that made you feel truly alive?",
                    "question_ar": "هل يمكنك وصف نشاط بدني حديث جعلك تشعر بأنك على قيد الحياة حقًا؟",
                    "purpose": "Identify peak experiences"
                },
                {
                    "question_en": "What environments make you feel most comfortable during physical activities?",
                    "question_ar": "ما هي البيئات التي تجعلك تشعر بأكبر قدر من الراحة أثناء الأنشطة البدنية؟",
                    "purpose": "Environmental preferences"
                }
            ]

        openai.api_key = self.openai_key

        # Build context
        context = f"""
Personality Type: {personality_type}
Z-Scores: {json.dumps(z_scores, indent=2)}
Current Answers: {len(current_answers)} questions answered
Research Gaps: {', '.join(research_gaps)}

The initial 10 questions didn't provide enough specific data for a bulletproof recommendation.
We need 2-3 targeted follow-up questions to fill these gaps.
"""

        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert sports psychologist. Generate 2-3 specific follow-up questions to better understand this person's ideal sports match. Return JSON only."
                    },
                    {
                        "role": "user",
                        "content": f"{context}\n\nGenerate questions as JSON:\n[{{\"question_en\": \"...\", \"question_ar\": \"...\", \"purpose\": \"...\"}}]"
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )

            content = response.choices[0].message.content
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                questions = json.loads(json_match.group())
                return questions[:3]

        except Exception as e:
            print(f"Follow-up question generation error: {e}")

        # Fallback questions
        return [
            {
                "question_en": "Do you prefer structured training or spontaneous movement?",
                "question_ar": "هل تفضل التدريب المنظم أو الحركة العفوية؟",
                "purpose": "Training style preference"
            },
            {
                "question_en": "How important is competition vs. personal achievement to you?",
                "question_ar": "ما مدى أهمية المنافسة مقابل الإنجاز الشخصي بالنسبة لك؟",
                "purpose": "Motivation clarification"
            }
        ]

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
chat_engine = AdaptiveChatEngine()

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
    MCP Analyze Endpoint with INTERNET RESEARCH

    1. Calculate personality scores
    2. Do bulletproof internet research
    3. Check if data is sufficient
    4. If not sufficient → return follow-up questions for chat
    5. If sufficient → return evidence-based recommendations
    """
    try:
        answers = request.get("answers", [])
        language = request.get("language", "ar")
        session_id = request.get("session_id", "")
        follow_up_answers = request.get("follow_up_answers", [])

        # Import main API functions
        from api.index import calculate_personality_scores, determine_profile_type

        # Calculate personality
        z_scores = calculate_personality_scores(answers)
        personality_type = determine_profile_type(z_scores)

        # STEP 1: Internet Research
        research_results = research_engine.bulletproof_analysis(z_scores, personality_type)

        # STEP 2: Check data sufficiency
        sufficiency = chat_engine.check_data_sufficiency(research_results)

        # STEP 3: If insufficient, generate follow-up questions
        if sufficiency["needs_follow_up"] and not follow_up_answers:
            follow_up_questions = await chat_engine.generate_follow_up_questions(
                z_scores,
                personality_type,
                answers,
                ["Not enough specific sports found", "Limited research data"]
            )

            return {
                "success": True,
                "session_id": session_id,
                "protocol": "MCP v1.0 - RESEARCH POWERED",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "NEEDS_MORE_DATA",
                "sufficiency": sufficiency,
                "follow_up_required": True,
                "follow_up_questions": follow_up_questions,
                "partial_research": {
                    "sources_found": research_results.get("total_sources_consulted", 0),
                    "sports_identified": len(research_results.get("specific_sport_research", []))
                }
            }

        # STEP 4: Generate evidence-based recommendations
        recommendations = research_engine.generate_evidence_based_recommendations(
            z_scores,
            personality_type,
            language
        )

        return {
            "success": True,
            "session_id": session_id,
            "protocol": "MCP v1.0 - BULLETPROOF",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "COMPLETE",
            "sufficiency": sufficiency,
            "data": {
                "personality_scores": z_scores,
                "personality_type": personality_type,
                "research_summary": {
                    "total_sources": research_results.get("total_sources_consulted", 0),
                    "confidence": "HIGH - Evidence-Based"
                },
                "recommendations": recommendations,
                "research_details": research_results
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
