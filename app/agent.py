'''
AI Agent for Tennis Courts Application
'''


from openai import OpenAI
from app.main import app
from fastapi import APIRouter
from pydantic import BaseModel
import os
from app.pydantic_models import AgentRequest
from fastapi import FastAPI


app = FastAPI()
client = OpenAI(api_key=os.environ["NYCPLACES_OPENAI_API_KEY"])


@app.post("/agent")
async def agent(request: AgentRequest):
    '''
    FastAPI endpoint that calls the Agent 
    '''

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



