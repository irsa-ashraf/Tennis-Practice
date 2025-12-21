from openai import OpenAI
from fastapi import APIRouter, HTTPException
import os

from app.pydantic_models import AgentRequest

router = APIRouter()

def _get_client() -> OpenAI:
    api_key = os.getenv("NYCPLACES_OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing NYCPLACES_OPENAI_API_KEY")
    return OpenAI(api_key=api_key)

@router.get("/agent_health")
def agent_health():
    return {"status": "ok"}

@router.post("/agent")
async def agent(request: AgentRequest):
    query = (request.query or "").strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    client = _get_client()

    try:
        resp = client.responses.create(
            model="gpt-5-nano",
            input=[
                {"role": "system", "content": "You are a helpful assistant for a NYC handball courts app. Be concise."},
                {"role": "user", "content": query},
            ],
        )
        return {"text": resp.output_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")
