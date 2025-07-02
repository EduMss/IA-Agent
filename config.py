from dotenv import load_dotenv
import os

# Carregar variáveis do arquivo .env
load_dotenv()

# Função auxiliar para transformar string em lista
def parse_env_list(value: str) -> list:
    return [item.strip() for item in value.split(",") if item.strip()]

# Url do servidor Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "") 

# LLM Models
MODEL_CHAT = os.getenv("MODEL_CHAT", "mistral")
MODEL_IMAGE_ANALYZE = os.getenv("MODEL_IMAGE_ANALYZE", "llava")
# MODEL_CODING_ANALYZE = os.getenv("MODEL_CODING_ANALYZE", "llama2:13b")
# MODEL_CODING_ANALYZE = os.getenv("MODEL_CODING_ANALYZE", "deepseek-coder-v2:16b") # Minha 2ª Opção de modelo para codigo, ele não é tão bom quanto o codestral:22b, mas é mais rapido
# MODEL_CODING_ANALYZE = os.getenv("MODEL_CODING_ANALYZE", "codestral:22b") # Melhor modelo até o momento, mas tem uma demora maior
MODEL_CODING_ANALYZE = os.getenv("MODEL_CODING_ANALYZE", "qwen2.5-coder:32b")
# MODEL_CODING_ANALYZE = os.getenv("MODEL_CODING_ANALYZE", "deepcoder:14b")


#Tokens aceito pelo modelo LLM (Padrão do Ollama é 4096)
NUM_CTX = int(os.getenv("NUM_CTX", 32000))

# ChromaDB
CHROMADB_HOST = os.getenv("CHROMADB_HOST", "") # Ip do servidor do chromadb
CHROMADB_PORT = int(os.getenv("CHROMADB_PORT", 8000)) # porta que está sendo utilizada a aplicação do chromadb

# Configurações de chunking (divisão do texto)
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1500)) # Quantidade de caracteres por chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200)) # Sobreposição entre chunks para manter contexto

# Configurações de busca vetorial
VECTOR_SEARCH_N_RESULTS = int(os.getenv("VECTOR_SEARCH_N_RESULTS", 10)) # Quantidade de documentos mais próximos a serem retornados na busca

# Configurações do SonarQube
SONAR_URL = os.getenv("SONAR_URL", "")
SONAR_TOKEN = os.getenv("SONAR_TOKEN", "")
SONAR_RULES_ID = os.getenv("SONAR_RULES_ID", "agenteia")
SONAR_ENGINE_ID = os.getenv("SONAR_ENGINE_ID", "AgenteIAEngine")
SONAR_NOME = os.getenv("SONAR_NOME", "Agente IA")

# Git
GIT_USER = os.getenv("GIT_USER", "")
GIT_TOKEN = os.getenv("GIT_TOKEN", "")
GIT_PROJECT_TEMP = os.getenv("GIT_PROJECT_TEMP", "project_temp")

# Logs
LOGS_DIR = os.getenv("LOGS", "logs")

# Carregar diretórios ignorados
IGNORED_FOLDERS = set(parse_env_list(os.getenv("IGNORED_FOLDERS", "")))

# Carregar arquivos ignorados
IGNORED_FILES = set(parse_env_list(os.getenv("IGNORED_FILES", "")))

# Carregar extensões aceitas
ACCEPTED_EXTENSIONS = tuple(parse_env_list(os.getenv("ACCEPTED_EXTENSIONS", "")))

# Frases para serem ignoradas nas issues dos codigos
BAD_PATTERNS = [
    "está bem estruturado",
    "fácil de entender",
    "bem organizado",
    "não há problemas",
    "nenhum problema encontrado",
    "ótima organização",
    "estrutura limpa",
    "parabéns pelo código",
    "nenhum problema"
]