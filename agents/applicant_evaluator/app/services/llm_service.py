import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3" 

def query_llm(prompt: str) -> str:
    """
    Send a prompt to the Ollama model and return the generated text.
    """
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except Exception as e:
        return f"LLM unavailable: {e}"
