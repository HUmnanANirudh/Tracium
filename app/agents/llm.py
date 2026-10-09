import os
from langchain_groq import ChatGroq

def get_llm(temperature=0):
    api_key = os.getenv("GROQ_API_KEY", "")
    # Must be a model listed by https://api.groq.com/openai/v1/models for your key
    model_name = os.getenv("GROQ_MODEL") or "openai/gpt-oss-120b"
    
    return ChatGroq(
        api_key=api_key,
        model=model_name,
        temperature=temperature
    )
