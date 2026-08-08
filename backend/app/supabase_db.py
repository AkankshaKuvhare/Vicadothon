import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional

logger = logging.getLogger("supabase_db")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

def _get_headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

def is_db_configured() -> bool:
    """Returns True if database endpoint variables are configured."""
    return bool(SUPABASE_URL and SUPABASE_KEY)

# --- PROFILES ---
def upsert_profile(user_id: str, email: str, name: Optional[str] = None) -> Dict[str, Any]:
    if not is_db_configured():
        return {}
    url = f"{SUPABASE_URL}/rest/v1/profiles"
    payload = {
        "id": user_id,
        "name": name or email.split("@")[0],
        "job_role": "Candidate",
        "status": "ACTIVE"
    }
    # Upsert using Postgrest resolution header
    headers = _get_headers()
    headers["Prefer"] = "resolution=merge-duplicates,return=representation"
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    res_list = response.json()
    return res_list[0] if res_list else {}

# --- INTERVIEW SESSIONS ---
def create_interview_session(
    session_id: str, 
    user_id: str, 
    candidate_id: str, 
    plan: Dict[str, Any]
) -> Dict[str, Any]:
    if not is_db_configured():
        return {}
    # Ensure profile exists in profile table before referencing
    try:
        upsert_profile(user_id, "user@example.com")
    except Exception as e:
        logger.warning("Profile auto-upsert failed: %s. Continuing...", e)

    url = f"{SUPABASE_URL}/rest/v1/interview_sessions"
    payload = {
        "id": session_id,
        "user_id": user_id,
        "candidate_id": candidate_id,
        "done": False,
        "current_question_index": 0,
        "follow_up_count": 0,
        "plan": plan
    }
    response = requests.post(url, json=payload, headers=_get_headers(), timeout=15)
    if response.status_code != 201 and response.status_code != 200:
        logger.error("Failed to create session in Supabase: %s", response.text)
        response.raise_for_status()
    res_list = response.json()
    return res_list[0] if res_list else {}

def get_interview_session(session_id: str) -> Optional[Dict[str, Any]]:
    if not is_db_configured():
        return None
    url = f"{SUPABASE_URL}/rest/v1/interview_sessions?id=eq.{session_id}"
    response = requests.get(url, headers=_get_headers(), timeout=15)
    response.raise_for_status()
    res_list = response.json()
    return res_list[0] if res_list else None

def update_interview_session(session_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    if not is_db_configured():
        return {}
    url = f"{SUPABASE_URL}/rest/v1/interview_sessions?id=eq.{session_id}"
    response = requests.patch(url, json=updates, headers=_get_headers(), timeout=15)
    response.raise_for_status()
    res_list = response.json()
    return res_list[0] if res_list else {}

# --- MESSAGES ---
def add_message(session_id: str, role: str, content: str) -> Dict[str, Any]:
    if not is_db_configured():
        return {}
    url = f"{SUPABASE_URL}/rest/v1/messages"
    payload = {
        "session_id": session_id,
        "role": role,
        "content": content
    }
    response = requests.post(url, json=payload, headers=_get_headers(), timeout=15)
    response.raise_for_status()
    res_list = response.json()
    return res_list[0] if res_list else {}

def get_session_messages(session_id: str) -> List[Dict[str, Any]]:
    if not is_db_configured():
        return []
    # Fetch messages ordered by created_at ascending
    url = f"{SUPABASE_URL}/rest/v1/messages?session_id=eq.{session_id}&order=created_at.asc"
    response = requests.get(url, headers=_get_headers(), timeout=15)
    response.raise_for_status()
    return response.json()

# --- FEEDBACK ---
def save_feedback(session_id: str, summary: str, strengths: List[str], gaps: List[str], next_steps: List[str]) -> Dict[str, Any]:
    if not is_db_configured():
        return {}
    url = f"{SUPABASE_URL}/rest/v1/feedback"
    payload = {
        "session_id": session_id,
        "summary": summary,
        "strengths": strengths,
        "gaps": gaps,
        "next_steps": next_steps
    }
    # Allow overwriting existing feedback if retried
    headers = _get_headers()
    headers["Prefer"] = "resolution=merge-duplicates,return=representation"
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    res_list = response.json()
    return res_list[0] if res_list else {}

def get_feedback(session_id: str) -> Optional[Dict[str, Any]]:
    if not is_db_configured():
        return None
    url = f"{SUPABASE_URL}/rest/v1/feedback?session_id=eq.{session_id}"
    response = requests.get(url, headers=_get_headers(), timeout=15)
    response.raise_for_status()
    res_list = response.json()
    return res_list[0] if res_list else None

# --- PLAGIARISM FLAGS ---
def add_plagiarism_flag(session_id: str, flag_type: str, message_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not is_db_configured():
        return {}
    url = f"{SUPABASE_URL}/rest/v1/plagiarism_flags"
    payload = {
        "session_id": session_id,
        "message_id": message_id,
        "flag_type": flag_type,
        "metadata": metadata or {}
    }
    response = requests.post(url, json=payload, headers=_get_headers(), timeout=15)
    response.raise_for_status()
    res_list = response.json()
    return res_list[0] if res_list else {}
