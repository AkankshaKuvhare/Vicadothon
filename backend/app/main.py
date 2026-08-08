import json
import logging
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import InterviewRequest, InterviewResponse, Feedback
from app.session import session_manager
from app.planner import generate_interview_plan
from app.handler import handle_interview_turn
from app.auth import get_current_user_id


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(title="PrepPal API")

# Add CORS Middleware for React frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load curriculum.json as static reference data at startup
try:
    with open(settings.CURRICULUM_PATH, "r", encoding="utf-8") as f:
        curriculum_data = json.load(f)
    logger.info("Successfully loaded curriculum.json from %s", settings.CURRICULUM_PATH)
except Exception as e:
    logger.error("Failed to load curriculum.json at startup: %s", e)
    curriculum_data = {"days": []}

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "PrepPal Backend"}

@app.get("/api/candidates")
def get_candidates():
    try:
        with open(settings.CANDIDATES_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error("Failed to load candidates.json: %s", e)
        raise HTTPException(status_code=500, detail="Failed to load candidates file")


@app.post("/api/interview", response_model=InterviewResponse)
def interview_endpoint(request: InterviewRequest, user_id: str = Depends(get_current_user_id)):
    """
    Unified endpoint for conducting the multi-turn technical interview.
    Graded Contract Specifications:
    
    1. Turn 1 (start):
       Request:  { "sessionId": "abc-123", "candidate": {...} }
       Response: { "reply": "...", "done": false }
       
    2. Turns 2..N:
       Request:  { "sessionId": "abc-123", "message": "..." }
       Response: { "reply": "...", "done": false }
       
    3. Final Turn:
       Response: {
         "reply": "Interview completed.",
         "done": true,
         "feedback": { "summary": "", "strengths": [], "gaps": [], "next": [] }
       }
    """
    session_id = request.sessionId
    
    # Check if this is Turn 1 (initialization)
    if request.candidate is not None:
        logger.info("Initializing session: %s for user: %s", session_id, user_id)
        
        # 1. Start the Interview Planner (Stage 1)
        # Classify performance, select target days, generate >= 8 questions via LLM
        try:
            plan = generate_interview_plan(request.candidate.dict(), curriculum_data)
        except Exception as e:
            logger.error("Planner generation failed for session %s: %s", session_id, e)
            raise HTTPException(status_code=500, detail=f"Interview planning failed: {str(e)}")
            
        # 2. Save plan to session state with user_id context
        session_state = session_manager.create_session(
            session_id=session_id,
            candidate=request.candidate.dict(),
            plan=plan,
            user_id=user_id
        )
        
        # Retrieve the first pre-planned opening question
        first_q_info = plan["questions"][0]
        first_question = first_q_info["question"]
        
        # Record the initial interviewer query in history
        session_state["history"].append({"role": "interviewer", "content": first_question})
        session_manager.update_session(session_id, session_state)
        
        return InterviewResponse(reply=first_question, done=False)
        
    # Standard Turns 2..N
    else:
        logger.info("Processing subsequent turn for session: %s by user: %s", session_id, user_id)
        
        # Verify session exists
        session = session_manager.get_session(session_id)
        if not session:
            logger.warning("Session not found: %s", session_id)
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found. Start a session by sending the candidate profile.")
            
        # Security validation: Ensure session user matches authenticated user
        if session.get("user_id") != user_id:
            logger.warning("Unauthorized access attempt on session %s by user %s", session_id, user_id)
            raise HTTPException(status_code=403, detail="Access denied: this session belongs to another user.")
            
        user_message = request.message
        if user_message is None:
            raise HTTPException(status_code=400, detail="Missing 'message' field for subsequent turn.")
            
        # Call Turn Handler (Stage 2 & 3)
        try:
            response_data = handle_interview_turn(session_id, user_message)
        except Exception as e:
            logger.error("Turn handling failed for session %s: %s", session_id, e)
            raise HTTPException(status_code=500, detail=f"Turn processing error: {str(e)}")
            
        return InterviewResponse(
            reply=response_data["reply"],
            done=response_data["done"],
            feedback=response_data.get("feedback")
        )


@app.get("/api/interview/session/{session_id}")
def get_session_details(session_id: str, user_id: str = Depends(get_current_user_id)):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Security validation: Ensure session user matches authenticated user
    if session.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Access denied: this session belongs to another user.")
    
    # Return plan details and current progress tracking metadata for the frontend
    plan = session.get("plan", {})

    return {
        "targetDays": plan.get("targetDays", []),
        "questions": [
            {"day": q["day"], "category": q["category"]} for q in plan.get("questions", [])
        ],
        "currentQuestionIndex": session["current_question_index"],
        "followUpCount": session["follow_up_count"],
        "done": session["done"]
    }

