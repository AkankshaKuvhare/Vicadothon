from typing import Dict, Any, List, Optional
from app.llm_client import generate

FEEDBACK_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "strengths": {
            "type": "array",
            "items": {"type": "string"}
        },
        "gaps": {
            "type": "array",
            "items": {"type": "string"}
        },
        "next": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["summary", "strengths", "gaps", "next"]
}

def synthesize_feedback(
    candidate: Dict[str, Any], 
    history: List[Dict[str, str]], 
    breeth_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Stage 3: Feedback Synthesizer
    Summarizes the entire conversation transcript and incorporates Breeth cognitive patterns 
    into a structured candidate assessment feedback.
    """
    member = candidate.get("member", {})
    
    system_prompt = (
        "You are an elite technical interviewer and assessor evaluating a candidate's technical interview transcript.\n"
        "Your task is to analyze the conversation and provide constructive, structured feedback.\n\n"
        "Evaluation Guidelines:\n"
        "1. Be objective, realistic, and specific to the topics covered. Do not use generic filler text.\n"
        "2. Formulate:\n"
        "   - summary: A cohesive paragraph summarizing the candidate's general performance, technical communication style, and readiness.\n"
        "   - strengths: A list of 2-3 specific technical strengths demonstrated by the candidate in their answers.\n"
        "   - gaps: A list of 2-3 areas where the candidate showed hesitation, misunderstandings, or incomplete knowledge.\n"
        "   - next: Actionable learning path recommendation items (e.g. 'Study topic X', 'Read documentation for Y') to help the candidate progress.\n"
    )
    
    # Extract Breeth cognitive patterns and add to prompt if available
    if breeth_context:
        edges = breeth_context.get("edges", [])
        patterns = []
        for edge in edges:
            meta = edge.get("intent_meta", {})
            pattern = meta.get("cognitive_pattern")
            if pattern:
                patterns.append(pattern)
        
        if patterns:
            # Deduplicate
            unique_patterns = list(set(patterns))
            system_prompt += (
                "\nCRITICAL: The candidate's response history has been analyzed. "
                "Incorporate the following extracted Breeth cognitive and reasoning style patterns "
                "directly into your evaluation narrative (summary and recommendations):\n"
            )
            for pat in unique_patterns:
                system_prompt += f"  - Cognitive Pattern: {pat}\n"
            system_prompt += "\n"

    system_prompt += "3. Format your response strictly in the JSON format matching the schema."
    
    formatted_transcript = []
    for msg in history:
        role_label = "Interviewer" if msg["role"] == "interviewer" else "Candidate"
        formatted_transcript.append(f"{role_label}: {msg['content']}")
        
    transcript_str = "\n".join(formatted_transcript)
    
    prompt_payload = (
        f"Candidate Name: {member.get('name', 'N/A')}\n"
        f"Target Role: {member.get('jobRole', 'N/A')}\n"
        f"Years of Experience: {member.get('yearsExperience', 0)}\n\n"
        f"Interview Transcript:\n"
        f"\"\"\"\n{transcript_str}\n\"\"\"\n"
    )
    
    messages = [
        {"role": "user", "content": prompt_payload}
    ]
    
    result = generate(system_prompt, messages, json_schema=FEEDBACK_SCHEMA)
    return result
