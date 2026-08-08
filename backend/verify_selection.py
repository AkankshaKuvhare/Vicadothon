import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load env
backend_dir = Path(__file__).resolve().parent
load_dotenv(backend_dir / ".env")

import app.planner as planner

def mock_llm_generate(system_prompt, messages, json_schema=None):
    """Fallback mock LLM generator to make the script runnable without keys."""
    # Find user message with payload
    payload = messages[0]["content"]
    try:
        # Extract selected days JSON from prompt
        import re
        json_match = re.search(r"(\[.*\])", payload, re.DOTALL)
        if json_match:
            day_contexts = json.loads(json_match.group(1))
        else:
            day_contexts = []
    except Exception:
        day_contexts = []
        
    # Generate mock questions matching the schema
    questions = []
    for ctx in day_contexts:
        day = ctx["day"]
        title = ctx["title"]
        category = ctx["candidate_performance"]["category"]
        
        # Make questions look personalized based on category
        if category == "STRUGGLE":
            q1 = f"Regarding {title} (Day {day}): Given your experience, what are the primary engineering hurdles you faced during this build, and how did you resolve them?"
            q2 = f"On Day {day}, you explored {title} and encountered some challenges. How would you design a testing harness to catch these integration failures earlier?"
        elif category == "FAILED":
            q1 = f"We noticed {title} (Day {day}) was incomplete. Can you walk me through your architectural plan for this day's project, and where the core blocker occurred?"
            q2 = f"If you were to refactor {title} (Day {day}) today with your current knowledge, what changes would you make in the setup?"
        elif category == "SKIPPED":
            q1 = f"Since you skipped Day {day} ({title}), how familiar are you with the tools used there, such as {', '.join(ctx.get('tools', [])[:2])}?"
            q2 = f"For Day {day} ({title}), what is your conceptual understanding of its objectives, and have you implemented similar architectures in your career?"
        else: # STRENGTH or NEUTRAL
            q1 = f"For {title} (Day {day}), where you excelled: How would you scale the tools ({', '.join(ctx.get('tools', []))}) to handle 10x throughput?"
            q2 = f"What design patterns did you apply in {title} (Day {day}) to ensure modularity and high reliability?"
            
        questions.append({"day": day, "question": q1, "category": category})
        questions.append({"day": day, "question": q2, "category": category})
        
    return {"questions": questions}

def test_planner():
    # Load candidate and curriculum files
    with open(backend_dir / "candidates.json", "r", encoding="utf-8") as f:
        candidates_data = json.load(f)
        
    with open(backend_dir / "curriculum.json", "r", encoding="utf-8") as f:
        curriculum_data = json.load(f)
        
    candidates = candidates_data["candidates"]
    curriculum = curriculum_data
    
    test_ids = ["CAND-001", "CAND-002", "CAND-003"]
    
    for candidate in candidates:
        member = candidate["member"]
        if member["id"] not in test_ids:
            continue
            
        print("=" * 70)
        print(f"CANDIDATE: {member['name']} ({member['id']})")
        print(f"ROLE: {member['jobRole']} | EXP: {member['yearsExperience']} years")
        print("-" * 70)
        
        # Generate the plan with try-except to handle key failures gracefully
        try:
            plan = planner.generate_interview_plan(candidate, curriculum)
        except Exception as e:
            print(f"[NOTICE] Actual LLM call failed (Error: {e}). Falling back to mock generator...")
            # Temporarily mock the planner's imported generate reference
            orig_generate = planner.generate
            planner.generate = mock_llm_generate
            plan = planner.generate_interview_plan(candidate, curriculum)
            # Restore
            planner.generate = orig_generate
            
        print(f"Selected Days (Span >= 4): {plan['targetDays']}\n")
        print("Generated Questions:")
        for idx, q in enumerate(plan["questions"]):
            print(f"  {idx+1}. [Day {q['day']}] ({q['category']}): {q['question']}")
        print("=" * 70 + "\n")

if __name__ == "__main__":
    test_planner()
