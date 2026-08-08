import logging
import requests
from typing import Dict, Any

from app.config import settings

logger = logging.getLogger("breeth_client")

class BreethClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("BREETH_API_KEY is not set or empty. A valid key is required to connect to the Breeth memory graph.")
        self.api_key = api_key
        self.base_url = "https://api.breeth.ai/v1"

    def write_episode(self, session_id: str, content: str, intent_extract: bool = True) -> dict:
        """
        Write a candidate response as an episode in a session-specific group.
        POST /episodes
        """
        group_id = f"session_{session_id}"
        url = f"{self.base_url}/episodes"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "content": content,
            "group_id": group_id,
            "extract_intent": intent_extract
        }
        
        logger.info("[BREETH_CLIENT] Writing episode to group '%s'...", group_id)
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        
        if response.status_code != 200:
            logger.error("[BREETH_CLIENT] POST /episodes failed with status %d: %s", response.status_code, response.text)
            response.raise_for_status()
            
        result = response.json()
        logger.info("[BREETH_CLIENT] SUCCESS: Logged episode ID: %s", result.get("id"))
        return result

    def search_session_context(self, session_id: str) -> dict:
        """
        Retrieve all episodes for this session and their extracted patterns.
        POST /search
        """
        group_id = f"session_{session_id}"
        url = f"{self.base_url}/search"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "query": "What patterns emerge from this candidate's responses?",
            "group_id": group_id
        }
        
        logger.info("[BREETH_CLIENT] Searching session context for group '%s'...", group_id)
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        
        if response.status_code != 200:
            logger.error("[BREETH_CLIENT] POST /search failed with status %d: %s", response.status_code, response.text)
            response.raise_for_status()
            
        result = response.json()
        logger.info("[BREETH_CLIENT] SUCCESS: Retrieved session context edges: %d", len(result.get("edges", [])))
        return result
