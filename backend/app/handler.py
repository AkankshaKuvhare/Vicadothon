from typing import Dict, Any, List
import json

from app.session import session_manager
from app.config import settings
from app.llm_client import generate
from app.feedback import synthesize_feedback
from app.breeth_client import BreethClient

# Instantiate the real BreethClient
breeth = BreethClient(api_key=settings.BREETH_API_KEY)

# Load curriculum static data to cross-reference tools in the follow-up heuristic fallback
try:
    with open(settings.CURRICULUM_PATH, "r", encoding="utf-8") as f:
        curriculum_data = json.load(f)
    curriculum_days_map = {d["day"]: d for d in curriculum_data.get("days", [])}
except Exception:
    curriculum_days_map = {}

def should_follow_up(candidate_response: str, question_context: dict) -> bool:
    """
    Simple heuristic: follow up if response is:
    - Too short (< 30 words)
    - Vague (uses hedging language: "I think", "maybe", "basically")
    - Incomplete (doesn't mention specific tools/concepts from the day's curriculum)
    """
    word_count = len(candidate_response.split())
    vague_words = ["think", "maybe", "basically", "probably", "sort of"]
    has_vague = any(word in candidate_response.lower() for word in vague_words)
    
    tools = question_context.get("tools", [])
    has_tool_mention = False
    if tools:
        for tool in tools:
            if tool.lower() in candidate_response.lower():
                has_tool_mention = True
                break
        is_incomplete = not has_tool_mention
    else:
        is_incomplete = False
        
    return word_count < 30 or (has_vague and word_count < 50) or (is_incomplete and word_count < 60)

def handle_interview_turn(session_id: str, user_message: str) -> Dict[str, Any]:
    """
    Stage 2: Turn Handler
    Logs candidate response to Breeth, parses extracted reasoning style patterns,
    steers interview routing, and manages safety constraints.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found.")
        
    if session["done"]:
        return {
            "reply": "Interview completed.",
            "done": True,
            "feedback": session["feedback"]
        }
        
    # 1. Log response to real Breeth API
    try:
        episode = breeth.write_episode(session_id, user_message, intent_extract=True)
        cognitive_pattern = episode.get("intent_meta", {}).get("cognitive_pattern", "")
        if not cognitive_pattern:
            cognitive_pattern = ""
    except Exception as e:
        print(f"[TURN_HANDLER] WARNING: Breeth log failed: {e}. Defaulting to empty pattern.")
        cognitive_pattern = ""
        
    # Append candidate's response to history
    session["history"].append({"role": "candidate", "content": user_message})
    
    current_idx = session["current_question_index"]
    planned_questions = session["questions"]
    
    # Resolve curriculum context for active day
    current_q_info = planned_questions[current_idx]
    day_num = current_q_info["day"]
    day_info = curriculum_days_map.get(day_num, {})
    
    question_context = {
        "day": day_num,
        "title": day_info.get("title", ""),
        "tools": day_info.get("tools", []),
        "objectives": day_info.get("objectives", []),
        "category": current_q_info["category"]
    }
    
    # Check safety cap: max 1 consecutive follow-up per topic
    if session["follow_up_count"] >= 1:
        print(f"[TURN_HANDLER] Max follow-up count reached for topic index {current_idx}. Forcing ADVANCE.")
        decision = "ADVANCE"
        reason = "Maximum follow-up limit of 1 reached."
    else:
        # Check cognitive pattern steering from Breeth first
        if "grasps quickly" in cognitive_pattern.lower() or "first-try" in cognitive_pattern.lower():
            decision = "ADVANCE"
            reason = f"Breeth cognitive pattern '{cognitive_pattern}' indicates quick grasp, advancing."
        elif "iterates" in cognitive_pattern.lower() or "struggles initially" in cognitive_pattern.lower():
            decision = "FOLLOW_UP"
            reason = f"Breeth cognitive pattern '{cognitive_pattern}' indicates iteration/struggle, follow up once."
        else:
            # Fallback to local heuristics
            is_follow_up = should_follow_up(user_message, question_context)
            if is_follow_up:
                decision = "FOLLOW_UP"
                reason = "Fallback heuristic trigger (too short, vague, or incomplete response)."
            else:
                decision = "ADVANCE"
                reason = "Fallback heuristic satisfies depth criteria."
                
        print(f"[TURN_HANDLER] Decision: {decision}. Source Reason: {reason}")
            
    # 2. Execute Decision
    if decision == "FOLLOW_UP":
        # Increment follow-up count
        session["follow_up_count"] += 1
        
        # Generate follow-up question
        follow_up_system = (
            "You are an expert technical interviewer. Ask a brief, direct, single follow-up question "
            "based on the candidate's last response to explore their depth of knowledge. "
            "Do not ask multiple questions. Keep it to one clean question."
        )
        
        try:
            follow_up_q = generate(follow_up_system, session["history"])
        except Exception as e:
            print(f"[TURN_HANDLER] Follow-up generation failed: {e}. Defaulting to planned question advance.")
            decision = "ADVANCE"
            
    if decision == "ADVANCE":
        # Move to next question index
        session["current_question_index"] += 1
        session["follow_up_count"] = 0
        new_idx = session["current_question_index"]
        
        if new_idx >= len(planned_questions):
            # 3. FINAL TURN: planned questions are exhausted
            print("[TURN_HANDLER] All planned questions exhausted. Fetching Breeth session history context...")
            
            # Fetch Breeth memory graph context to feed the Synthesizer
            try:
                breeth_context = breeth.search_session_context(session_id)
            except Exception as e:
                print(f"[TURN_HANDLER] Breeth search context failed: {e}. Proceeding without it.")
                breeth_context = None
                
            print("[TURN_HANDLER] Initiating Feedback Synthesizer...")
            try:
                feedback_data = synthesize_feedback(session["candidate"], session["history"], breeth_context)
            except Exception as e:
                print(f"[TURN_HANDLER] Feedback synthesis failed: {e}. Using fallback static feedback.")
                feedback_data = {
                    "summary": "Technical interview completed successfully covering multiple curriculum modules.",
                    "strengths": ["Demonstrated competency in key concepts discussed during the interview"],
                    "gaps": ["Further practice and conceptual reinforcement in some skipped or struggle day modules"],
                    "next": ["Review curriculum logs and code solutions for targeted improvement"]
                }
                
            session["done"] = True
            session["feedback"] = feedback_data
            session_manager.update_session(session_id, session)
            
            return {
                "reply": "Interview completed.",
                "done": True,
                "feedback": feedback_data
            }
        else:
            # Generate next question with a smooth transition
            next_q_info = planned_questions[new_idx]
            transition_system = (
                "You are an expert technical interviewer.\n"
                "Your task is to transition smoothly from the previous discussion to the next planned question.\n\n"
                f"Next Planned Question (Target Day {next_q_info['day']}): {next_q_info['question']}\n\n"
                "Acknowledge the candidate's last response briefly (conversational validation), "
                "build a transition bridge, and ask the next question. "
                "You MUST preserve the core focus of the planned question."
            )
            
            try:
                reply_text = generate(transition_system, session["history"])
            except Exception as e:
                print(f"[TURN_HANDLER] Transition generation failed: {e}. Using raw planned question.")
                reply_text = next_q_info["question"]
    else:
        # decision is FOLLOW_UP and LLM call succeeded
        reply_text = follow_up_q
        
    # Append the generated question to history
    session["history"].append({"role": "interviewer", "content": reply_text})
    
    # Save the updated session state
    session_manager.update_session(session_id, session)
    
    return {
        "reply": reply_text,
        "done": False
    }
