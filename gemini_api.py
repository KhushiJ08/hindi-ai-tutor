import requests

# 🏠 Locally hosted Gemma 4 via Ollama
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma4:e4b"

def get_response(user_input):
    prompt = f"""
    Tum ek friendly Hindi tutor ho.

    Student ka question:
    {user_input}

    Simple Hindi mein samjhao.
    Gaon example use karo.
    End mein ek chhota sa question pucho.
    """

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=120)
        response.raise_for_status()
        return response.json()["response"]
    except requests.exceptions.ConnectionError:
        return "⚠️ Ollama server se connect nahi ho paa raha. Kya Ollama chal raha hai? (`ollama serve`)"
    except requests.exceptions.Timeout:
        return "⚠️ Model ka response bahut time le raha hai. Thoda wait karke phir try karo."
    except Exception as e:
        return f"⚠️ Kuch gadbad ho gayi: {e}"