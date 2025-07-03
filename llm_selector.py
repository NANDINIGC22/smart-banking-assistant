import os
import requests
import json
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def call_openai(prompt, model_name):
    try:
        response = openai.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"OpenAI request failed: {e}"

def call_ollama(prompt, model_name):
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }
    try:
        resp = requests.post(url, json=payload)

        # Try clean JSON parse first
        try:
            return resp.json().get("response", "No response from Ollama.")
        except json.JSONDecodeError:
            # Fallback: handle newline-separated JSON or noisy response
            lines = resp.text.splitlines()
            for line in lines:
                try:
                    data = json.loads(line)
                    return data.get("response", "No response from Ollama.")
                except json.JSONDecodeError:
                    continue
            return "Invalid response format from Ollama."
    except Exception as e:
        return f"Ollama request failed: {e}"

def get_llm(model_name):
    if model_name in ["gpt-4", "gpt-4o", "gpt-3.5-turbo"]:
        return lambda prompt: call_openai(prompt, model_name)
    elif model_name in ["llama3", "mistral"]:
        return lambda prompt: call_ollama(prompt, model_name)
    else:
        raise ValueError(f"Unsupported model: {model_name}")
