import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma4:e4b"

def get_response(user_input):
    prompt = f"""Tum ek friendly Hindi tutor ho. 
Student ka question: {user_input}

1. Simple Hindi mein samjhao. Gaon example use karo. End mein ek chhota sa question pucho.
2. Identify the main topic being discussed (1 or 2 words only).

IMPORTANT: You must respond ONLY with a valid JSON object. Do not include markdown formatting like ```json.
{{
    "tutor_response": "Your Hindi response here",
    "topic": "The core concept (e.g., Photosynthesis, Fractions, Newton's Law)",
    "status": "Struggling"
}}"""

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "format": "json" # This Ollama flag forces JSON output
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        
        # Parse the JSON string returned by Ollama into a Python dictionary
        raw_output = response.json()["response"]
        parsed_data = json.loads(raw_output)
        
        return parsed_data
        
    except requests.exceptions.ConnectionError:
        return {"tutor_response": "⚠️ Ollama server se connect nahi ho paa raha.", "topic": "Error", "status": "Error"}
    except json.JSONDecodeError:
        return {"tutor_response": "⚠️ Model ne galat format diya. Phir se try karo.", "topic": "Error", "status": "Error"}
    except Exception as e:
        return {"tutor_response": f"⚠️ Kuch gadbad ho gayi: {e}", "topic": "Error", "status": "Error"}