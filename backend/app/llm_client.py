import json
import logging
import requests
from typing import Any, Dict, List, Optional
import jsonschema

from app.config import settings

logger = logging.getLogger("llm_client")

class LLMGenerationError(Exception):
    """Raised when both primary and fallback LLMs fail to generate or validate."""
    pass

class JSONValidationError(Exception):
    """Raised when JSON parsing or schema validation fails."""
    pass

def _clean_json_string(raw_str: str) -> str:
    """Heuristic helper to extract clean JSON string if wrapped in markdown formatting."""
    if not raw_str:
        return ""
    cleaned = raw_str.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()

def _validate_response(content: str, json_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Tries to parse response content as JSON and validate against schema."""
    if not content:
        raise JSONValidationError("Response content is empty or None.")
        
    cleaned = _clean_json_string(content)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise JSONValidationError(f"Response content is not valid JSON: {str(e)}. Raw content: {content}")
        
    try:
        jsonschema.validate(instance=data, schema=json_schema)
    except jsonschema.ValidationError as e:
        raise JSONValidationError(f"Response fails JSON schema validation: {str(e)}. Parsed data: {data}")
        
    return data

def _call_sarvam(messages: List[Dict[str, str]], has_schema: bool) -> str:
    """Call Sarvam AI API using requests REST client."""
    if not settings.SARVAM_API_KEY:
        raise ValueError("SARVAM_API_KEY is not set.")
        
    url = "https://api.sarvam.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.SARVAM_API_KEY}"
    }
    payload = {
        "model": "sarvam-105b",
        "messages": messages,
        "temperature": 0.1 if has_schema else 0.7,
        "top_p": 0.95,
        "max_tokens": 1024
    }
    
    logger.info("[LLM_CLIENT] Calling Sarvam AI completing REST endpoint...")
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    
    if response.status_code != 200:
        logger.error("[LLM_CLIENT] Sarvam AI endpoint returned status code %d: %s", response.status_code, response.text)
        response.raise_for_status()
        
    data = response.json()
    choices = data.get("choices")
    if not choices:
        raise ValueError(f"Sarvam AI returned empty choices structure. Full response: {json.dumps(data)}")
    message = choices[0].get("message")
    if not message:
        raise ValueError(f"Sarvam AI returned choice with no message body. Full response: {json.dumps(data)}")
    content = message.get("content")
    if content is None:
        raise ValueError(f"Sarvam AI returned message with content=None (moderated or failed). Full response: {json.dumps(data)}")
        
    return content

def _call_groq(messages: List[Dict[str, str]], has_schema: bool) -> str:
    """Call Groq API using requests REST client."""
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not set.")
        
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.GROQ_API_KEY}"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.1 if has_schema else 0.7,
        "max_tokens": 1024
    }
    
    logger.info("[LLM_CLIENT] Calling Groq completing REST endpoint...")
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    
    if response.status_code != 200:
        logger.error("[LLM_CLIENT] Groq endpoint returned status code %d: %s", response.status_code, response.text)
        response.raise_for_status()
        
    data = response.json()
    choices = data.get("choices")
    if not choices:
        raise ValueError(f"Groq returned empty choices structure. Full response: {json.dumps(data)}")
    message = choices[0].get("message")
    if not message:
        raise ValueError(f"Groq returned choice with no message body. Full response: {json.dumps(data)}")
    content = message.get("content")
    if content is None:
        raise ValueError(f"Groq returned message with content=None. Full response: {json.dumps(data)}")
        
    return content

def _build_payload_messages(system_prompt: str, messages: List[Dict[str, str]], json_schema: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
    """Merges system prompts and user dialogues into OpenAI format."""
    payload_messages = []
    
    local_system = system_prompt or ""
    if json_schema:
        schema_instruction = (
            f"\n\nYou MUST return a JSON object matching this schema. "
            f"Do not include any normal conversation, explanation or markdown blocks outside the JSON object.\n"
            f"JSON Schema:\n{json.dumps(json_schema, indent=2)}"
        )
        local_system += schema_instruction
        
    if local_system:
        payload_messages.append({"role": "system", "content": local_system})
        
    for msg in messages:
        role = msg.get("role", "user")
        if role not in ("system", "user", "assistant"):
            role = "user"
        payload_messages.append({"role": role, "content": msg.get("content", "")})
        
    return payload_messages

def generate(system_prompt: str, messages: List[Dict[str, str]], json_schema: Optional[Dict[str, Any]] = None) -> Any:
    """
    Generate completion using real API endpoints only (no mocks).
    Primary provider: Sarvam AI (model: sarvam-105b)
    Fallback provider: Groq (model: llama-3.3-70b-versatile)
    Logs which provider actually served each call.
    """
    payload_messages = _build_payload_messages(system_prompt, messages, json_schema)
    
    # --- Try Primary Provider: Sarvam AI ---
    try:
        print("[LLM_CLIENT] Routing request to Sarvam AI (Primary)...")
        content = _call_sarvam(payload_messages, json_schema is not None)
        
        if json_schema:
            try:
                parsed = _validate_response(content, json_schema)
                print("[LLM_CLIENT] SUCCESS: Sarvam AI (Primary) served request with valid JSON.")
                return parsed
            except JSONValidationError as val_err:
                print(f"[LLM_CLIENT] Sarvam JSON validation failed: {val_err}. Retrying once with stricter prompt...")
                stricter_messages = payload_messages + [
                    {"role": "assistant", "content": content if content else ""},
                    {"role": "user", "content": f"CRITICAL ERROR: Your previous response was invalid. Return ONLY a valid JSON object matching the schema. Do not output explanations, do not wrap in markdown: {json.dumps(json_schema)}"}
                ]
                content = _call_sarvam(stricter_messages, True)
                parsed = _validate_response(content, json_schema)
                print("[LLM_CLIENT] SUCCESS: Sarvam AI (Primary) served request on retry.")
                return parsed
        else:
            print("[LLM_CLIENT] SUCCESS: Sarvam AI (Primary) served request.")
            return content
            
    except Exception as sarvam_err:
        print(f"[LLM_CLIENT] WARNING: Sarvam AI failed or returned invalid JSON. Error: {sarvam_err}")
        print("[LLM_CLIENT] Routing request to Groq (Fallback)...")
        
        # --- Try Fallback Provider: Groq ---
        try:
            content = _call_groq(payload_messages, json_schema is not None)
            
            if json_schema:
                try:
                    parsed = _validate_response(content, json_schema)
                    print("[LLM_CLIENT] SUCCESS: Groq (Fallback) served request with valid JSON.")
                    return parsed
                except JSONValidationError as val_err:
                    print(f"[LLM_CLIENT] Groq JSON validation failed: {val_err}. Retrying once with stricter prompt...")
                    stricter_messages = payload_messages + [
                        {"role": "assistant", "content": content if content else ""},
                        {"role": "user", "content": f"CRITICAL ERROR: Your previous response was invalid. Return ONLY a valid JSON object matching the schema. Do not output explanations, do not wrap in markdown: {json.dumps(json_schema)}"}
                    ]
                    content = _call_groq(stricter_messages, True)
                    parsed = _validate_response(content, json_schema)
                    print("[LLM_CLIENT] SUCCESS: Groq (Fallback) served request on retry.")
                    return parsed
            else:
                print("[LLM_CLIENT] SUCCESS: Groq (Fallback) served request.")
                return content
                
        except Exception as groq_err:
            error_msg = f"Both primary (Sarvam) and fallback (Groq) providers failed. Groq Error: {groq_err}"
            print(f"[LLM_CLIENT] CRITICAL ERROR: {error_msg}")
            raise LLMGenerationError(error_msg) from groq_err
