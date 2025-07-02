import requests
from config import OLLAMA_URL, MODEL_CHAT

# Obtendo o embedding do texto para procurar ou armazenar a informação na base de dados (chroma)
def get_embedding(text: str):
    response = requests.post(f"{OLLAMA_URL}/api/embeddings", json={
        "model": MODEL_CHAT,  # ou qualquer modelo
        "prompt": text
    })
    response.raise_for_status()
    return response.json()["embedding"]
