import os
from langchain_groq import ChatGroq

def get_llm(temperature=0):
    api_key = os.getenv("GROQ_API_KEY", "")
    # Defaulting to llama3-8b-8192 or similar if not specified
    model_name = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    
    return ChatGroq(
        api_key=api_key,
        model=model_name,
        temperature=temperature
    )
