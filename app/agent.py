'''
AI Agent for Tennis Courts Application
'''


from openai import OpenAI
from app.main import app
from fastapi import APIRouter
from pydantic import BaseModel
import os

router = APIRouter()
client = OpenAI(api_key=os.environ["NYCPLACES_OPENAI_API_KEY"])

