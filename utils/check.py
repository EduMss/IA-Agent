from config import OLLAMA_URL, CHROMADB_HOST, SONAR_URL, SONAR_TOKEN, GIT_USER, GIT_TOKEN
from fastapi import HTTPException, status
import os

def check_environment_variables():
    if OLLAMA_URL == "":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Defina a URL do Ollama serve na variável de ambiente OLLAMA_URL"
        )
    
    if CHROMADB_HOST == "":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Defina a URL do ChromaDB na variável de ambiente CHROMADB_HOST, caso necessário defina a porta na variável CHROMADB_PORT"
        )
    
    if SONAR_URL == "":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Defina a URL do SonarQube na variável de ambiente SONAR_URL"
        )
    
    if SONAR_TOKEN == "":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Defina o Token do SonarQube na variável de ambiente SONAR_TOKEN"
        )
    
    if GIT_USER == "":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Defina o Usuário do Git na variável de ambiente GIT_USER"
        )
    
    if GIT_TOKEN == "":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Defina o Token do Git na variável de ambiente GIT_TOKEN"
        )
    
# 🚩 Função para checar as variáveis de ambiente
def check_environment_variables():
    required_vars = {
        "OLLAMA_URL": "Defina a URL do ChromaDB na variável de ambiente CHROMADB_HOST, caso necessário defina a porta na variável CHROMADB_PORT",
        "CHROMADB_HOST": "Defina a URL do ChromaDB na variável de ambiente CHROMADB_HOST", 
        "GIT_USER": "Defina o Usuário do Git na variável de ambiente GIT_USER",
        "GIT_TOKEN": "Defina o Token do Git na variável de ambiente GIT_TOKEN",
    }

    missing = []

    for var, error_message in required_vars.items():
        if not os.getenv(var):
            missing.append(error_message)

    if missing:
        errors = "\n".join(missing)
        raise Exception(f"Erro nas variáveis de ambiente:\n{errors}")