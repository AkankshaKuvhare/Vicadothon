from typing import List, Dict, Any, Tuple
import json

from app.llm_client import generate

# Step a: Classification rules
# STRUGGLE: passed == true AND attempts >= 3
# FAILED: passed == false
# SKIPPED: skipped == true
# STRENGTH: passed == true AND attempts == 1
# NEUTRAL: passed == true AND attempts == 2 (or any other case)
def classify_mission(mission: Dict[str, Any]) -> str:
    if mission.get("skipped") is True:
        return "SKIPPED"
    
    passed = mission.get("passed")
    attempts = mission.get("attempts", 0)
    
    if passed is False:
        return "FAILED"
    elif passed is True:
        if attempts >= 3:
            return "STRUGGLE"
        elif attempts == 1:
            return "STRENGTH"
        elif attempts == 2:
            return "NEUTRAL"
    
    return "NEUTRAL"

def select_target_days(candidate_missions: List[Dict[str, Any]], curriculum_days: List[Dict[str, Any]]) -> List[int]:
    # Map curriculum days by day number for fast lookup
    curriculum_days_map = {d["day"]: d for d in curriculum_days}
    
    # helper to check if day is SHIP_IT or CAPSTONE
    def is_priority_day(day_num: int) -> bool:
        day_info = curriculum_days_map.get(day_num, {})
        day_type = day_info.get("type", "")
        return day_type in ("SHIP_IT", "CAPSTONE")
    
    # Classify candidate missions
    classified: Dict[str, List[Dict[str, Any]]] = {
        "STRUGGLE": [],
        "FAILED": [],
        "SKIPPED": [],
        "STRENGTH": [],
        "NEUTRAL": []
    }
    
    for mission in candidate_missions:
        cat = classify_mission(mission)
        classified[cat].append(mission)
        
    # Group STRUGGLE and FAILED together
    struggle_failed = classified["STRUGGLE"] + classified["FAILED"]
    skipped = classified["SKIPPED"]
    strength = classified["STRENGTH"]
    neutral = classified["NEUTRAL"]
    
    # b) Cross-reference and rank
    # struggle_failed ranked by attempts desc, then is_priority desc, then day number asc
    # (Since we sort descending, we use attempts, is_priority, and -day_num)
    struggle_failed.sort(
        key=lambda m: (
            m.get("attempts", 0) if m.get("passed") is True else 99,  # failed is prioritized or has attempts
            is_priority_day(m["day"]),
            -m["day"]
        ),
        reverse=True
    )
    
    # skipped ranked by is_priority desc, then day number asc
    skipped.sort(
        key=lambda m: (
            is_priority_day(m["day"]),
            -m["day"]
        ),
        reverse=True
    )
    
    # strength ranked by is_priority desc, then day number asc
    strength.sort(
        key=lambda m: (
            is_priority_day(m["day"]),
            -m["day"]
        ),
        reverse=True
    )
    
    # neutral ranked by is_priority desc, then day number asc
    neutral.sort(
        key=lambda m: (
            is_priority_day(m["day"]),
            -m["day"]
        ),
        reverse=True
    )
    
    # c) Select target days
    selected_days: List[int] = []
    
    # Target 2-3 from STRUGGLE/FAILED
    # Let's take up to 2 first
    for m in struggle_failed[:2]:
        if m["day"] not in selected_days:
            selected_days.append(m["day"])
            
    # Target 1-2 from SKIPPED
    # Let's take up to 1 first
    for m in skipped[:1]:
        if m["day"] not in selected_days:
            selected_days.append(m["day"])
            
    # Target 2-3 from STRENGTH
    # Let's take up to 2 first
    for m in strength[:2]:
        if m["day"] not in selected_days:
            selected_days.append(m["day"])
            
    # If any of the target categories was empty, or if we didn't hit 4 distinct days, backfill from NEUTRAL
    # The requirement is: "If any category is empty for this candidate, backfill from NEUTRAL to still hit >= 4 distinct days total"
    # Also "Hard requirement: final selection must span >= 4 distinct curriculum days"
    categories_checked = {
        "STRUGGLE_FAILED": len(struggle_failed) > 0,
        "SKIPPED": len(skipped) > 0,
        "STRENGTH": len(strength) > 0
    }
    
    any_empty = not all(categories_checked.values())
    
    if any_empty or len(selected_days) < 4:
        # Backfill from NEUTRAL
        for m in neutral:
            if m["day"] not in selected_days:
                selected_days.append(m["day"])
                if len(selected_days) >= 4:
                    break
                    
    # If we are STILL short of 4 days (e.g. neutral is empty or candidate has very few missions total),
    # let's collect from struggle_failed, skipped, and strength to fill up to 4 days
    if len(selected_days) < 4:
        for m in struggle_failed[2:]:
            if m["day"] not in selected_days:
                selected_days.append(m["day"])
                if len(selected_days) >= 4:
                    break
                    
    if len(selected_days) < 4:
        for m in strength[2:]:
            if m["day"] not in selected_days:
                selected_days.append(m["day"])
                if len(selected_days) >= 4:
                    break
                    
    if len(selected_days) < 4:
        for m in skipped[1:]:
            if m["day"] not in selected_days:
                selected_days.append(m["day"])
                if len(selected_days) >= 4:
                    break
                    
    return selected_days

QUESTIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "minItems": 8,
            "items": {
                "type": "object",
                "properties": {
                    "day": {"type": "integer"},
                    "question": {"type": "string"},
                    "category": {"type": "string", "enum": ["STRUGGLE", "FAILED", "SKIPPED", "STRENGTH", "NEUTRAL"]}
                },
                "required": ["day", "question", "category"]
            }
        }
    },
    "required": ["questions"]
}

def generate_interview_plan(candidate: Dict[str, Any], curriculum: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates an interview plan based on the candidate's learning history and the curriculum.
    Runs once on session start.
    """
    candidate_missions = candidate.get("missions", [])
    curriculum_days = curriculum.get("days", [])
    
    # 1. Select the target days (step a-c)
    selected_day_numbers = select_target_days(candidate_missions, curriculum_days)
    
    # Map selected days for easy details lookup
    curriculum_days_map = {d["day"]: d for d in curriculum_days}
    candidate_missions_map = {m["day"]: m for m in candidate_missions}
    
    # 2. Package context for each day to pass to the LLM
    day_contexts = []
    for day_num in selected_day_numbers:
        day_info = curriculum_days_map.get(day_num, {})
        mission_info = candidate_missions_map.get(day_num, {})
        
        # Calculate performance category
        category = classify_mission(mission_info) if mission_info else "NEUTRAL"
        
        day_contexts.append({
            "day": day_num,
            "title": day_info.get("title", ""),
            "type": day_info.get("type", ""),
            "tools": day_info.get("tools", []),
            "objectives": day_info.get("objectives", []),
            "candidate_performance": {
                "category": category,
                "passed": mission_info.get("passed") if mission_info else None,
                "attempts": mission_info.get("attempts", 0) if mission_info else 0,
                "skipped": mission_info.get("skipped", False) if mission_info else False
            }
        })
        
    member = candidate.get("member", {})
    
    # 3. Call LLM to generate >= 8 opening questions tailored to their background
    system_prompt = (
        "You are an expert technical interviewer conducting a personalized multi-turn coding and systems architecture interview. "
        "Your task is to generate a list of at least 8 tailored opening questions based on the candidate's learning history and background.\n\n"
        "Guidance on Question Phrasing:\n"
        "1. DO NOT ask generic textbook or dictionary-definition questions. "
        "2. Tailor questions to the candidate's experience level, job role, and target curriculum days.\n"
        f"   - Candidate Role: {member.get('jobRole', 'Software Engineer')}\n"
        f"   - Years of Experience: {member.get('yearsExperience', 0)} years\n"
        f"   - Education: {member.get('education', 'N/A')}\n"
        "3. Address different categories of performance differently:\n"
        "   - For 'STRUGGLE' or 'FAILED' days: Probe gently to see if they understand the concepts now. Reference their prior attempts indirectly (e.g. 'Implementing vector storage can sometimes require tuning indices or structure. What challenges did you face when...')\n"
        "   - For 'SKIPPED' days: Check if they possess prior knowledge of this area or if this constitutes a gap. Ask a conceptual, high-level evaluation question.\n"
        "   - For 'STRENGTH' days: Ask advanced, deep-dive scenario or trade-off questions to let them show off their strength at their experience level.\n"
        "4. Generate exactly 2 questions for each selected day to distribute them evenly and make sure all selected days are covered, totaling at least 8 questions."
    )
    
    prompt_payload = (
        f"Please generate the ordered list of interview questions. You must cover these selected days:\n"
        f"{json.dumps(day_contexts, indent=2)}\n"
    )
    
    messages = [
        {"role": "user", "content": prompt_payload}
    ]
    
    llm_result = generate(system_prompt, messages, json_schema=QUESTIONS_SCHEMA)
    
    # Schema check ensures 'questions' is a list of questions
    questions = llm_result.get("questions", [])
    
    return {
        "targetDays": selected_day_numbers,
        "questions": questions
    }
