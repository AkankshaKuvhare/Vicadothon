import threading
from typing import Dict, Any, Optional
from app import supabase_db

class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        
    def create_session(self, session_id: str, candidate: Dict[str, Any], plan: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Initializes the state of an interview session.
        Stores target days, pre-generated questions, history, and status trackers.
        """
        # Default fallback UUID if running without JWT user (e.g. testing)
        uid = user_id or "00000000-0000-0000-0000-000000000000"
        
        # 1. Store in Supabase DB if configured
        if supabase_db.is_db_configured():
            try:
                # Cache candidate in plan dictionary for easier retrieval on fetches
                plan_with_candidate = {**plan, "candidate_data": candidate}
                supabase_db.create_interview_session(
                    session_id=session_id,
                    user_id=uid,
                    candidate_id=candidate.get("member", {}).get("id", "UNKNOWN"),
                    plan=plan_with_candidate
                )
            except Exception as e:
                print(f"[SESSION_MANAGER] Supabase create_session failed: {e}. Using in-memory fallback.")

        # 2. Maintain local fallback copy
        with self._lock:
            session_state = {
                "sessionId": session_id,
                "user_id": uid,
                "candidate": candidate,
                "targetDays": plan["targetDays"],
                "questions": plan["questions"], # List of dicts: {"day": int, "question": str, "category": str}
                "history": [],                   # List of dicts: {"role": "interviewer" | "candidate", "content": str}
                "current_question_index": 0,
                "follow_up_count": 0,
                "done": False,
                "feedback": None
            }
            self._sessions[session_id] = session_state
            return session_state
            
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves session state from Supabase if configured, otherwise from in-memory cache."""
        if supabase_db.is_db_configured():
            try:
                db_session = supabase_db.get_interview_session(session_id)
                if db_session:
                    db_messages = supabase_db.get_session_messages(session_id)
                    history = [{"role": msg["role"], "content": msg["content"]} for msg in db_messages]
                    
                    plan = db_session.get("plan", {})
                    candidate = plan.get("candidate_data", {})
                    
                    # Fetch feedback details if complete
                    feedback = None
                    if db_session.get("done"):
                        db_feedback = supabase_db.get_feedback(session_id)
                        if db_feedback:
                            feedback = {
                                "summary": db_feedback.get("summary", ""),
                                "strengths": db_feedback.get("strengths", []),
                                "gaps": db_feedback.get("gaps", []),
                                "next": db_feedback.get("next_steps", [])
                            }
                    
                    return {
                        "sessionId": session_id,
                        "user_id": db_session["user_id"],
                        "candidate": candidate,
                        "targetDays": plan.get("targetDays", []),
                        "questions": plan.get("questions", []),
                        "history": history,
                        "current_question_index": db_session["current_question_index"],
                        "follow_up_count": db_session["follow_up_count"],
                        "done": db_session["done"],
                        "feedback": feedback
                    }
            except Exception as e:
                print(f"[SESSION_MANAGER] Supabase get_session failed: {e}. Using in-memory fallback.")

        with self._lock:
            return self._sessions.get(session_id)
            
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Updates the session state in Supabase database, falling back to local thread-safe dictionaries."""
        if supabase_db.is_db_configured():
            try:
                db_updates = {}
                if "current_question_index" in updates:
                    db_updates["current_question_index"] = updates["current_question_index"]
                if "follow_up_count" in updates:
                    db_updates["follow_up_count"] = updates["follow_up_count"]
                if "done" in updates:
                    db_updates["done"] = updates["done"]
                
                if db_updates:
                    supabase_db.update_interview_session(session_id, db_updates)
                
                # Check for history adjustments (new dialog bubbles)
                if "history" in updates:
                    new_history = updates["history"]
                    db_messages = supabase_db.get_session_messages(session_id)
                    db_count = len(db_messages)
                    
                    # Sync any unsaved messages to db messages table
                    if len(new_history) > db_count:
                        for i in range(db_count, len(new_history)):
                            msg = new_history[i]
                            supabase_db.add_message(session_id, msg["role"], msg["content"])
                
                # Sync feedback if available
                if "feedback" in updates and updates["feedback"]:
                    fb = updates["feedback"]
                    supabase_db.save_feedback(
                        session_id=session_id,
                        summary=fb.get("summary", ""),
                        strengths=fb.get("strengths", []),
                        gaps=fb.get("gaps", []),
                        next_steps=fb.get("next", [])
                    )
            except Exception as e:
                print(f"[SESSION_MANAGER] Supabase update_session failed: {e}. Falling back to local cache.")

        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].update(updates)
                return self._sessions[session_id]
            return None

session_manager = SessionManager()
