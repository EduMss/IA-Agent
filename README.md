# 🧠 LLM-Driven Code Analyzer API

Um backend inteligente que utiliza modelos de linguagem (LLMs) para análise automática de código-fonte, geração de insights e integração com plataformas como SonarQube, ChromaDB e Telegram.

## 🚀 Funcionalidades

- 📁 Clonagem automática de projetos Git
- 🤖 Análise de código com modelos LLM (via Ollama)
- 🧠 Classificação de problemas: qualidade, bugs, lógica, segurança, etc.
- 📝 Geração de relatório JSON padronizado
- ☁️ Integração com **SonarQube** (via external-issues.json)
- 📚 Indexação de PDFs em base vetorial (**ChromaDB**) com extração de imagens e textos
- 💬 Chat RAG com Telegram (responde com base nos PDFs enviados)

---

## 🧠 Modelos LLM Utilizados

| Finalidade         | Modelo                   |
|--------------------|--------------------------|
| Análise de código  | `qwen2.5-coder:32b`      |
| Chat geral (RAG)   | `mistral`                |
| Imagem + PDF       | `llava:7b`               |

Todos gerenciados via [Ollama](https://ollama.com).

---

## 📦 Tecnologias e Bibliotecas

- Python 3.12+
- [FastAPI](https://fastapi.tiangolo.com/)
- [Ollama](https://ollama.com/) (GPU)
- [ChromaDB](https://docs.trychroma.com/)
- [SonarQube](https://www.sonarsource.com/)
- PyMuPDF, PIL (PDF + imagem)
- Telegram Bot API

---

## ⚙️ Variáveis de Ambiente

Crie um arquivo `.env` com (altere as informações):

```env
OLLAMA_URL=http://localhost:11434

MODEL_CHAT=mistral
MODEL_IMAGE_ANALYZE=llava
MODEL_CODING_ANALYZE=qwen2.5-coder:32b

CHROMADB_HOST=IP-ChromaDB
CHROMADB_PORT=Porta-ChromaDB

CHUNK_SIZE=2000
CHUNK_OVERLAP=300
VECTOR_SEARCH_N_RESULTS=10
NUM_CTX=32000

SONAR_URL=http://URL-SONARQUBE
SONAR_TOKEN=TOKEN-LOGIN-SONARQUBE
SONAR_RULES_ID=agenteia
SONAR_ENGINE_ID=AgenteIAEngine
SONAR_NOME=Agente IA

GIT_USER=USUARIO-GITHUB
GIT_TOKEN=TOKEN-GITHUB
GIT_PROJECT_TEMP=project_temp

LOGS_DIR=logs

IGNORED_FOLDERS=.git,__pycache__,.idea,.vs,node_modules,venv,.mypy_cache,.vscode
IGNORED_FILES=.gitignore,README.md,LICENSE
ACCEPTED_EXTENSIONS=.py,.js,.ts,.java,.c,.cpp,.cs,.go,.html,.jsx,.tsx
```

---

## 📦 Como Executar

**1.** Clone este repositório:
```bash
git clone https://github.com/seu-usuario/seu-projeto.git
cd seu-projeto
```

**2.** Instale as dependências:
```
pip install -r requirements.txt
```

**3.** Configure seu .env com as credenciais e URLs necessárias

**4.** Instale o Tesseract ORC e adicione no PATH do Windows 

**5.** Descompacte o arquivo 'dependecias/Windows/sonar-scanner.rar' em 'dependecias/Windows/'

**6.** Faça o Download dos modelos no ollama:
```
ollama pull qwen2.5-coder:32b
ollama pull mistral
ollama pull llava:7b
```

**7.** Inicie o servidor Ollama:
```
ollama serve
```

**8.** Inicie o backend:
```
uvicorn main:app --reload
```


---

## 🔗 Requisições
## 🧠 Chat (/ask)
Permite realizar perguntas ao sistema.

- Método: **POST**
- Content-Type: **application/x-www-form-urlencoded**
- Parâmetros:
    - question: (string) – Pergunta para o modelo
```
POST /ask
Content-Type: application/x-www-form-urlencoded

question=Qual a função da classe FileManager?
```

## 📄 Enviar PDF (/upload-pdf)
Faz upload de um arquivo PDF para análise e indexação.

- Método: **POST**
- Content-Type: **multipart/form-data**
- Parâmetros:
  - file: (arquivo) – PDF a ser enviado
  - description: (string) – Breve descrição do conteúdo

```
POST /upload-pdf
Content-Type: multipart/form-data

file=[arquivo.pdf]
description=Manual de uso do sistema
```

## 🔍 Análise de Projeto Git (/analyze)
Analisa um projeto de código hospedado em um repositório Git, clona, analisa com LLM e envia para o SonarQube.

- Método: **POST**
- Content-Type: **application/json**
- Body:
```
{
  "sonar_project_key": "PROJET-KEY-SONARQUBE",
  "project_git_url": "URL-GITHUB-PROJETO",
  "project_git_branch": "master"
}
```


## 📄 Licença
MIT © [Eduardo Matheus]