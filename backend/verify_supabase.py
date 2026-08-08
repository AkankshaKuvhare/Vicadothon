import os
from pathlib import Path
from dotenv import load_dotenv

# Load env variables from .env
backend_dir = Path(__file__).resolve().parent
load_dotenv(backend_dir / ".env")

from app import supabase_db

def test_supabase_crud():
    print("[INFO] Checking Supabase DB configurations...")
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
    
    print(f"  SUPABASE_URL configured:              {bool(url)}")
    print(f"  SUPABASE_SERVICE_ROLE_KEY configured:  {bool(key)}")
    print(f"  SUPABASE_JWT_SECRET configured:        {bool(jwt_secret)}")
    
    if not supabase_db.is_db_configured():
        print("\n[CRITICAL] Supabase connection is NOT active. Variables are missing or placeholders.")
        print("Please configure valid credentials in backend/.env before running database tests.")
        return
        
    print("\n[INFO] Starting Supabase CRUD verification tests...")
    
    test_user_id = "00000000-0000-0000-0000-000000000001"
    test_session_id = "00000000-0000-0000-0000-000000000002"
    
    # 1. Profile Upsert
    print("\n1. Testing Profile Upsert...")
    profile = supabase_db.upsert_profile(test_user_id, "test_cohort@example.com", "Test Candidate")
    print("SUCCESS: Profile synced:", profile)
    
    # 2. Session Creation
    print("\n2. Testing Session Creation...")
    mock_plan = {
        "targetDays": [7, 10, 23, 31],
        "questions": [
            {"day": 7, "question": "Explain text embeddings?", "category": "STRENGTH"}
        ]
    }
    session = supabase_db.create_interview_session(test_session_id, test_user_id, "CAND-999", mock_plan)
    print("SUCCESS: Session created:", session)
    
    # 3. Message Log
    print("\n3. Testing Message Log...")
    msg = supabase_db.add_message(test_session_id, "interviewer", "Explain text embeddings?")
    print("SUCCESS: Message added:", msg)
    
    # 4. Message Retrieve
    print("\n4. Testing Message Retrieval...")
    history = supabase_db.get_session_messages(test_session_id)
    print(f"SUCCESS: Retrieved {len(history)} messages in dialogue.")
    
    # 5. Plagiarism Flag
    print("\n5. Testing Plagiarism Logging...")
    flag = supabase_db.add_plagiarism_flag(
        session_id=test_session_id,
        flag_type="tab_switch",
        message_id=msg.get("id"),
        metadata={"switched_count": 3}
    )
    print("SUCCESS: Plagiarism flagged:", flag)
    
    # 6. Save Feedback
    print("\n6. Testing Feedback Synthesis Persistence...")
    feedback = supabase_db.save_feedback(
        session_id=test_session_id,
        summary="Candidate showed excellent embeddings mastery.",
        strengths=["Robust vector search knowledge"],
        gaps=["None"],
        next_steps=["Advance to deployment modules"]
    )
    print("SUCCESS: Feedback saved:", feedback)

if __name__ == "__main__":
    test_supabase_crud()
