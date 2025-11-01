"""
AI-PAL Main REST API

FastAPI application providing access to all AI-PAL features.

Endpoints:
- /health - Health check
- /api/chat - Process AC system requests
- /api/users - User profile management
- /api/ffe - Fractal Flow Engine
- /api/social - Social features
- /api/personality - Personality discovery
- /metrics - Prometheus metrics

Authentication: Bearer token (JWT)
Rate limiting: Configured per endpoint
"""

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import os

# Import AI-PAL components
from ai_pal.core.integrated_system import IntegratedACSystem, ACConfig
from ai_pal.monitoring import get_health_checker, get_metrics, get_logger

# Initialize
logger = get_logger("ai_pal.api")

app = FastAPI(
    title="AI-PAL API",
    description="Privacy-first AC-AI cognitive partner system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AC system (singleton)
_ac_system: Optional[IntegratedACSystem] = None


def get_ac_system() -> IntegratedACSystem:
    """Get or create AC system instance"""
    global _ac_system
    if _ac_system is None:
        config = ACConfig(
            enable_four_gates=True,
            enable_ari_monitoring=True,
            enable_edm_monitoring=True,
            enable_ffe=True
        )
        _ac_system = IntegratedACSystem(config=config)
    return _ac_system


# ===== REQUEST/RESPONSE MODELS =====

class ChatRequest(BaseModel):
    """Request for chat/AC processing"""
    query: str = Field(..., description="User's request/question", min_length=1)
    session_id: str = Field(..., description="Session identifier")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional context")


class ChatResponse(BaseModel):
    """Response from AC system"""
    response: str
    gate_results: Dict[str, Any]
    ari_snapshot: Dict[str, Any]
    edm_analysis: Dict[str, Any]
    metadata: Dict[str, Any]


class GoalRequest(BaseModel):
    """Request to create FFE goal"""
    description: str = Field(..., description="Goal description")
    deadline: Optional[str] = Field(default=None, description="ISO format deadline")
    priority: str = Field(default="medium", description="Priority: low, medium, high")


class GoalResponse(BaseModel):
    """FFE goal response"""
    goal_id: str
    description: str
    clarity_score: float
    estimated_difficulty: float
    status: str


# ===== AUTHENTICATION =====

async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    """
    Extract user from authorization header

    In production, this would validate JWT tokens.
    For now, we extract user_id from bearer token.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Format: "Bearer <token>"
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
            )

        # In production: validate JWT and extract user_id
        # For now: use token as user_id (for development/testing)
        user_id = token

        return user_id

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        )


# ===== HEALTH & METRICS =====

@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint

    Returns system health status.
    """
    checker = get_health_checker()
    health = await checker.check_health()

    return JSONResponse(
        status_code=200 if health.status.value == "healthy" else 503,
        content=health.to_dict()
    )


@app.get("/metrics", response_class=PlainTextResponse, tags=["System"])
async def metrics():
    """
    Prometheus metrics endpoint

    Returns metrics in Prometheus text format.
    """
    metrics_collector = get_metrics()
    return metrics_collector.export_prometheus()


# ===== CORE AC SYSTEM =====

@app.post("/api/chat", response_model=ChatResponse, tags=["Core"])
async def process_chat(
    request: ChatRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Process a chat request through the AC system

    This is the main entry point for AI-PAL interactions.
    Request goes through all Four Gates and returns response with
    ARI, EDM, and other metadata.
    """
    logger.info(
        "Processing chat request",
        user_id=user_id,
        session_id=request.session_id,
        context={"query_length": len(request.query)}
    )

    ac_system = get_ac_system()

    try:
        # Process through AC system
        result = await ac_system.process_request(
            user_id=user_id,
            query=request.query,
            session_id=request.session_id,
            context=request.context
        )

        # Record metrics
        metrics = get_metrics()
        metrics.record_request(
            endpoint="/api/chat",
            method="POST",
            status_code=200,
            latency_seconds=result.execution_time_ms / 1000,
            model_used=result.model_used
        )

        # Return response
        return ChatResponse(
            response=result.response,
            gate_results={
                "all_passed": result.gate_results.all_passed,
                "gate1_passed": result.gate_results.gate1_passed,
                "gate2_passed": result.gate_results.gate2_passed,
                "gate3_passed": result.gate_results.gate3_passed,
                "gate4_passed": result.gate_results.gate4_passed,
                "violations": [v.__dict__ for v in result.gate_results.violations]
            },
            ari_snapshot={
                "autonomy_retention": result.ari_snapshot.autonomy_retention,
                "trend": result.ari_snapshot.trend,
                "total_interactions": result.ari_snapshot.total_interactions
            },
            edm_analysis={
                "debt_score": result.edm_analysis.debt_score,
                "flagged_claims": len(result.edm_analysis.flagged_claims),
                "requires_review": result.edm_analysis.requires_review
            },
            metadata={
                "execution_time_ms": result.execution_time_ms,
                "model_used": result.model_used,
                "cost_usd": result.cost_usd
            }
        )

    except Exception as e:
        logger.error(
            "Chat request failed",
            user_id=user_id,
            session_id=request.session_id,
            exc_info=True
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Request processing failed: {str(e)}"
        )


@app.get("/api/users/{user_id}/profile", tags=["Users"])
async def get_user_profile(
    user_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Get user profile

    Returns user's ARI history, skills, preferences.
    """
    # Verify user can only access their own profile
    if user_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other users' profiles"
        )

    ac_system = get_ac_system()

    try:
        profile = await ac_system.get_user_profile(user_id)

        return {
            "user_id": profile.user_id,
            "ari_score": profile.ari_score,
            "ari_history": [
                {
                    "timestamp": snapshot.timestamp.isoformat(),
                    "score": snapshot.autonomy_retention,
                    "trend": snapshot.trend
                }
                for snapshot in profile.ari_history[-10:]  # Last 10
            ],
            "skills": profile.skills,
            "total_interactions": profile.total_interactions,
            "created_at": profile.created_at.isoformat()
        }

    except Exception as e:
        logger.error("Profile retrieval failed", user_id=user_id, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile retrieval failed: {str(e)}"
        )


# ===== FFE ENDPOINTS =====

@app.post("/api/ffe/goals", response_model=GoalResponse, tags=["FFE"])
async def create_goal(
    request: GoalRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Create a new FFE goal

    Ingests a goal and returns structured goal with clarity score.
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="FFE not available"
        )

    try:
        context = {}
        if request.deadline:
            context["deadline"] = request.deadline
        context["priority"] = request.priority

        goal = await ac_system.ffe_engine.ingest_goal(
            user_id=user_id,
            goal_description=request.description,
            context=context
        )

        return GoalResponse(
            goal_id=goal.goal_id,
            description=goal.description,
            clarity_score=goal.clarity_score,
            estimated_difficulty=goal.estimated_difficulty,
            status=goal.status.value
        )

    except Exception as e:
        logger.error("Goal creation failed", user_id=user_id, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Goal creation failed: {str(e)}"
        )


@app.get("/api/ffe/goals/{goal_id}", tags=["FFE"])
async def get_goal(
    goal_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get FFE goal details
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine:
        raise HTTPException(status_code=503, detail="FFE not available")

    try:
        goal = ac_system.ffe_engine.goal_ingestor.get_goal(goal_id)

        if not goal or goal.user_id != user_id:
            raise HTTPException(status_code=404, detail="Goal not found")

        return {
            "goal_id": goal.goal_id,
            "description": goal.description,
            "clarity_score": goal.clarity_score,
            "estimated_difficulty": goal.estimated_difficulty,
            "status": goal.status.value,
            "category": goal.category,
            "deadline": goal.deadline.isoformat() if goal.deadline else None,
            "priority": goal.priority
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Goal retrieval failed", goal_id=goal_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ffe/goals/{goal_id}/plan", tags=["FFE"])
async def create_5_block_plan(
    goal_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Create 5-block plan for a goal

    Returns: Tiny → Small → Medium → Large → STOP
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine:
        raise HTTPException(status_code=503, detail="FFE not available")

    try:
        plan = await ac_system.ffe_engine.create_5_block_plan(
            goal_id=goal_id,
            user_id=user_id
        )

        return {
            "goal_id": plan.goal_id,
            "blocks": [
                {
                    "block_number": block.block_number,
                    "duration_minutes": block.duration_minutes,
                    "task": block.task.description if block.task else None,
                    "status": block.status
                }
                for block in plan.blocks
            ],
            "total_estimated_time_minutes": plan.total_estimated_time_minutes,
            "created_at": plan.created_at.isoformat()
        }

    except Exception as e:
        logger.error("Plan creation failed", goal_id=goal_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===== STARTUP/SHUTDOWN =====

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("AI-PAL API starting up")

    # Initialize AC system
    get_ac_system()

    logger.info("AI-PAL API ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("AI-PAL API shutting down")


# ===== ERROR HANDLERS =====

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    logger.error("Unhandled exception", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "ai_pal.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
