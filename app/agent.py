'''
AI Agent for Tennis Courts Application
'''


from openai import OpenAI
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
from app.pydantic_models import AgentRequest

router = APIRouter()
client = OpenAI(api_key=os.environ["NYCPLACES_OPENAI_API_KEY"])


@router.get("/agent_health")
def health_check():
    return {"status": "ok"}


@router.post("/agent")
async def agent(request: AgentRequest):
    '''
    FastAPI endpoint that calls the Agent 
    '''

    api_key = os.getenv("NYCPLACES_OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing NYCPLACES_OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    try:
        response = client.responses.create(model="gpt-5-nano", 
                                           input=[
                                                    {
                                                        "role": "system",
                                                        "content": "You are a helpful assistant for a NYC handball courts app. Be concise."
                                                    },
                                                    {
                                                        "role": "user",
                                                        "content": request.query
                                                    }
                                                ],)
        return {"response": response.output_text}
    except Exception as e:
        return {"error": str(e)}
    

# if __name__ == "__main__":
#     import uvicorn  
#     uvicorn.run(app, host="



