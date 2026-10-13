from typing import Optional, Dict, Any
import httpx
from backend.app.core.config import settings


class LocalAssistantAdapter:
    def __init__(self):
        self.enabled = settings.LOCAL_ASSISTANT_ENABLED
        self.provider = settings.LOCAL_ASSISTANT_PROVIDER
        self.base_url = settings.LOCAL_ASSISTANT_BASE_URL.rstrip("/")
        self.model = settings.LOCAL_ASSISTANT_MODEL

    async def generate_coordination_note(self, incident_data: Dict[str, Any], hospitals_summary: list) -> Optional[str]:
        if not self.enabled:
            return None

        prompt = (
            "You are a local, non-clinical emergency coordination operations assistant. "
            "You MUST NOT diagnose, predict patient survival, provide treatment advice, or alter hospital rankings. "
            "Hospital ranking is strictly deterministic and computed by the software engine. "
            "Provide at most 3 concise operational checklist points regarding missing logistical data or resource verification. "
            f"Case: {incident_data}. Candidate Facilities: {hospitals_summary}."
        )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                if self.provider == "ollama":
                    resp = await client.post(
                        f"{self.base_url}/api/chat",
                        json={
                            "model": self.model or "llama3",
                            "stream": False,
                            "messages": [{"role": "user", "content": prompt}]
                        }
                    )
                    if resp.status_code == 200:
                        return resp.json().get("message", {}).get("content", "")
                else:
                    # OpenAI-compatible / LM Studio
                    resp = await client.post(
                        f"{self.base_url}/v1/chat/completions",
                        json={
                            "model": self.model or "default",
                            "messages": [{"role": "user", "content": prompt}]
                        }
                    )
                    if resp.status_code == 200:
                        choices = resp.json().get("choices", [])
                        if choices:
                            return choices[0].get("message", {}).get("content", "")
        except Exception as e:
            # Fall back gracefully; assistant is strictly non-essential
            return f"Local assistant unavailable ({type(e).__name__}); deterministic ranking remains authoritative."

        return None


local_assistant = LocalAssistantAdapter()
