# ✅ Final Clean llm_selector.py Compatible with openai ≥ 1.0.0

import os
import openai
import requests

client = openai.Client(api_key=os.getenv("OPENAI_API_KEY"))

def get_llm(model_name):
    ollama_server = "http://localhost:11434"

    def call_openai(prompt, model):
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful banking assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()

    def call_ollama(prompt, model):
        payload = {"model": model, "prompt": prompt}
        resp = requests.post(f"{ollama_server}/api/generate", json=payload)
        return resp.json().get("response", "No response from Ollama.")

    if model_name in ["gpt-4", "gpt-4o", "gpt-3.5"]:
        return lambda prompt: call_openai(prompt, model_name)
    elif model_name in ["llama3", "mistral", "deepseek"]:
        return lambda prompt: call_ollama(prompt, model_name)
    else:
        raise ValueError("Unsupported model selected")
