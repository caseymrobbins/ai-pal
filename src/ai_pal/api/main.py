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


# ===== SOCIAL FEATURES =====

@app.post("/api/social/groups", tags=["Social"])
async def create_social_group(
    name: str,
    description: str,
    is_open: bool = False,
    user_id: str = Depends(get_current_user)
):
    """
    Create a new sharing group

    User-initiated group creation for win sharing.
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'social_interface'):
        raise HTTPException(status_code=503, detail="Social features not available")

    try:
        result = await ac_system.ffe_engine.social_interface.create_group(
            user_id=user_id,
            name=name,
            description=description,
            is_open=is_open
        )

        return result

    except Exception as e:
        logger.error("Group creation failed", user_id=user_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/social/groups/{group_id}/join", tags=["Social"])
async def join_social_group(
    group_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Join an open group
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'social_interface'):
        raise HTTPException(status_code=503, detail="Social features not available")

    try:
        result = await ac_system.ffe_engine.social_interface.join_group(
            user_id=user_id,
            group_id=group_id
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message", "Failed to join group"))

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Group join failed", group_id=group_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/social/groups/{group_id}/leave", tags=["Social"])
async def leave_social_group(
    group_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Leave a group (no pressure to stay)
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'social_interface'):
        raise HTTPException(status_code=503, detail="Social features not available")

    try:
        result = await ac_system.ffe_engine.social_interface.leave_group(
            user_id=user_id,
            group_id=group_id
        )

        return result

    except Exception as e:
        logger.error("Group leave failed", group_id=group_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/social/groups", tags=["Social"])
async def list_my_groups(
    user_id: str = Depends(get_current_user)
):
    """
    List all groups user is a member of
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'social_interface'):
        raise HTTPException(status_code=503, detail="Social features not available")

    try:
        groups = await ac_system.ffe_engine.social_interface.list_my_groups(user_id)
        return {"groups": groups}

    except Exception as e:
        logger.error("Group list failed", user_id=user_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/social/feed/{group_id}", tags=["Social"])
async def get_group_feed(
    group_id: str,
    limit: int = 20,
    user_id: str = Depends(get_current_user)
):
    """
    View wins shared in a group

    User must be a member of the group.
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'social_interface'):
        raise HTTPException(status_code=503, detail="Social features not available")

    try:
        feed = await ac_system.ffe_engine.social_interface.view_group_feed(
            user_id=user_id,
            group_id=group_id,
            limit=limit
        )

        if "error" in feed:
            raise HTTPException(status_code=404, detail=feed["error"])

        return feed

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Feed retrieval failed", group_id=group_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class WinShareRequest(BaseModel):
    """Request to share a win"""
    win_id: str
    win_description: str
    win_type: str
    celebration_text: str
    selected_groups: List[str]
    allow_encouragement: bool = True


@app.post("/api/social/share", tags=["Social"])
async def share_win(
    request: WinShareRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Share a win with selected groups

    USER-INITIATED: User explicitly chooses to share.
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'social_interface'):
        raise HTTPException(status_code=503, detail="Social features not available")

    try:
        result = await ac_system.ffe_engine.social_interface.share_win(
            user_id=user_id,
            win_id=request.win_id,
            win_description=request.win_description,
            win_type=request.win_type,
            celebration_text=request.celebration_text,
            selected_groups=request.selected_groups,
            allow_encouragement=request.allow_encouragement
        )

        return result

    except Exception as e:
        logger.error("Win sharing failed", user_id=user_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class EncouragementRequest(BaseModel):
    """Request to send encouragement"""
    message: str


@app.post("/api/social/encourage/{share_id}", tags=["Social"])
async def send_encouragement(
    share_id: str,
    request: EncouragementRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Send encouragement to someone's shared win
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'social_interface'):
        raise HTTPException(status_code=503, detail="Social features not available")

    try:
        result = await ac_system.ffe_engine.social_interface.send_encouragement(
            from_user_id=user_id,
            share_id=share_id,
            message=request.message
        )

        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Encouragement failed", share_id=share_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===== PERSONALITY DISCOVERY =====

@app.post("/api/personality/discover/start", tags=["Personality"])
async def start_personality_discovery(
    user_id: str = Depends(get_current_user)
):
    """
    Start a personality discovery session

    Returns first question to begin interactive assessment.
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'personality_discovery'):
        raise HTTPException(status_code=503, detail="Personality discovery not available")

    try:
        session = await ac_system.ffe_engine.personality_discovery.start_discovery_session(user_id)

        return {
            "session_id": session.session_id,
            "stage": session.stage,
            "message": "Let's discover your signature strengths! Answer a few questions."
        }

    except Exception as e:
        logger.error("Discovery session start failed", user_id=user_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/personality/discover/{session_id}/question", tags=["Personality"])
async def get_next_question(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Get next discovery question

    Adaptive questioning based on previous answers.
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'personality_discovery'):
        raise HTTPException(status_code=503, detail="Personality discovery not available")

    try:
        question = await ac_system.ffe_engine.personality_discovery.get_next_question(
            session_id=session_id,
            user_id=user_id
        )

        if not question:
            # Session complete
            return {
                "complete": True,
                "message": "Discovery session complete! View your results."
            }

        return {
            "question_id": question.question_id,
            "question_text": question.question_text,
            "question_type": question.question_type.value,
            "options": question.options if hasattr(question, 'options') else None,
            "complete": False
        }

    except Exception as e:
        logger.error("Question retrieval failed", session_id=session_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class AnswerRequest(BaseModel):
    """Answer to discovery question"""
    answer: Any


@app.post("/api/personality/discover/{session_id}/answer/{question_id}", tags=["Personality"])
async def record_answer(
    session_id: str,
    question_id: str,
    request: AnswerRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Record answer to discovery question
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'personality_discovery'):
        raise HTTPException(status_code=503, detail="Personality discovery not available")

    try:
        await ac_system.ffe_engine.personality_discovery.record_answer(
            session_id=session_id,
            user_id=user_id,
            question_id=question_id,
            answer=request.answer
        )

        return {
            "success": True,
            "message": "Answer recorded"
        }

    except Exception as e:
        logger.error("Answer recording failed", session_id=session_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/personality/discover/{session_id}/complete", tags=["Personality"])
async def complete_discovery(
    session_id: str,
    user_id: str = Depends(get_current_user)
):
    """
    Complete discovery session and get results

    Returns discovered signature strengths with confidence scores.
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'personality_discovery'):
        raise HTTPException(status_code=503, detail="Personality discovery not available")

    try:
        result = await ac_system.ffe_engine.personality_discovery.complete_session(
            session_id=session_id,
            user_id=user_id
        )

        return {
            "discovered_strengths": [
                {
                    "type": s.strength_type.value,
                    "label": s.identity_label,
                    "description": s.strength_description,
                    "confidence": s.confidence_score,
                    "examples": s.demonstrated_examples
                }
                for s in result.get("strengths", [])
            ],
            "discovery_confidence": result.get("discovery_confidence", 0.0),
            "summary": result.get("summary", "")
        }

    except Exception as e:
        logger.error("Discovery completion failed", session_id=session_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/personality/strengths", tags=["Personality"])
async def get_current_strengths(
    min_confidence: float = 0.3,
    user_id: str = Depends(get_current_user)
):
    """
    Get user's current signature strengths

    Includes dynamically updated confidence scores.
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'personality_connector'):
        raise HTTPException(status_code=503, detail="Personality features not available")

    try:
        strengths = await ac_system.ffe_engine.personality_connector.get_current_strengths(
            user_id=user_id,
            min_confidence=min_confidence
        )

        return {
            "strengths": [
                {
                    "type": s.strength_type.value,
                    "label": s.identity_label,
                    "description": s.strength_description,
                    "confidence": s.confidence_score,
                    "examples": s.demonstrated_examples[-5:]  # Last 5 examples
                }
                for s in strengths
            ]
        }

    except Exception as e:
        logger.error("Strengths retrieval failed", user_id=user_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/personality/insights", tags=["Personality"])
async def get_personality_insights(
    user_id: str = Depends(get_current_user)
):
    """
    Get insights about evolving personality

    Shows top strengths, emerging strengths, and trends.
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'personality_connector'):
        raise HTTPException(status_code=503, detail="Personality features not available")

    try:
        insights = await ac_system.ffe_engine.personality_connector.generate_insights(user_id)
        return insights

    except Exception as e:
        logger.error("Insights generation failed", user_id=user_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ===== TEACHING / PROTÉGÉ =====

@app.post("/api/teaching/start", tags=["Teaching"])
async def start_teaching_mode(
    user_id: str = Depends(get_current_user)
):
    """
    Start teaching mode

    User becomes a protégé, preparing to teach AI-PAL about their domain.
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'teaching_interface'):
        raise HTTPException(status_code=503, detail="Teaching features not available")

    try:
        result = await ac_system.ffe_engine.teaching_interface.start_teaching_mode(user_id)

        return {
            "message": "Teaching mode started! What would you like to teach me about?",
            "teaching_session_id": result.get("session_id"),
            "status": result.get("status")
        }

    except Exception as e:
        logger.error("Teaching mode start failed", user_id=user_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


class TeachingRequest(BaseModel):
    """Teaching content submission"""
    topic: str
    explanation: str
    examples: Optional[List[str]] = None


@app.post("/api/teaching/submit", tags=["Teaching"])
async def submit_teaching_content(
    request: TeachingRequest,
    user_id: str = Depends(get_current_user)
):
    """
    Submit teaching content

    User explains a concept or skill to AI-PAL.
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'teaching_interface'):
        raise HTTPException(status_code=503, detail="Teaching features not available")

    try:
        result = await ac_system.ffe_engine.teaching_interface.submit_teaching_content(
            user_id=user_id,
            topic=request.topic,
            explanation=request.explanation,
            examples=request.examples or []
        )

        return result

    except Exception as e:
        logger.error("Teaching submission failed", user_id=user_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/teaching/taught-topics", tags=["Teaching"])
async def get_taught_topics(
    user_id: str = Depends(get_current_user)
):
    """
    Get all topics user has taught

    Returns user's teaching history and mastery indicators.
    """
    ac_system = get_ac_system()

    if not ac_system.ffe_engine or not hasattr(ac_system.ffe_engine, 'teaching_interface'):
        raise HTTPException(status_code=503, detail="Teaching features not available")

    try:
        topics = await ac_system.ffe_engine.teaching_interface.get_taught_topics(user_id)
        return {"taught_topics": topics}

    except Exception as e:
        logger.error("Taught topics retrieval failed", user_id=user_id, exc_info=True)
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
