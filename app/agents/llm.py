import os
from langchain_google_genai import ChatGoogleGenerativeAI

def get_llm(temperature=0):
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    if not gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not set. Please set the environment variable.")
        
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=gemini_api_key,
        temperature=temperature
    )
