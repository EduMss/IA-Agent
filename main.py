from utils.git_integration import clone_repo
from utils.json_treatment import convert_analysis_to_sonarqube
from utils.pdf_reader import extract_text_and_images
from utils.embedding import get_embedding
from utils.chroma_client import add_to_chroma, query_chroma, delete_from_chroma
from utils import llm_integration
from utils.check import check_environment_variables
from models.schemas import AnalyzeRequest, AnalysisResponse
from core.analysis import get_project_files, consolidate_analysis, generate_project_tree, convert_path_to_project
from core.sonar_integration import get_sonar_issues, run_sonar_scanner
from config import OLLAMA_URL, CHUNK_SIZE, CHUNK_OVERLAP, MODEL_CHAT, LOGS_DIR, SONAR_TOKEN, SONAR_URL
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from contextlib import asynccontextmanager
import requests
import logging
import json
import time

# Verificar se as variaveis importante estão configuradas!
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🚀 Checagem no startup
    check_environment_variables()
    print("✔️ Variáveis de ambiente validadas. API iniciando.")
    yield
    # 🧹 Aqui seria o shutdown se quisesse
    print("🛑 API sendo desligada.")


# Passando o lifespan para ele executar antes de iniciar a aplicação
app = FastAPI(lifespan=lifespan)

# Criando diretorio log
Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)

# Configuração básica de logging
logging.basicConfig(
    filename='logs/analysis.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True  # <- sobrescreve qualquer configuração anterior de logging
)

#Enviar arquivo para a base de dados
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...), description: str = Form(...)):
    try:
        file_name = file.filename

        # Remove dados antigos do arquivo, se existirem
        delete_from_chroma(file_name)

        # extrair conteudo do pdf e transformar em texto para a base de dados
        content = extract_text_and_images(file.file, file_name, description)
        
        if not content.strip():
            return {"error": "Não foi possível extrair texto do PDF."}

        print(f"Conteudo gerado apartir do pdf: {file_name}\nDescrição forncida pelo usuário: {description}\n\n{content}")

        # dividindo o conteudo do pdf em pedaços menores para ser armazenado na base de dados
        chunks = [content[i:i+CHUNK_SIZE] for i in range(0, len(content), CHUNK_SIZE - CHUNK_OVERLAP)]
        
        # Convertendo o conteudo do chunk para embedding e armazenando na base de dados
        for idx, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            add_to_chroma(f"{file_name}_chunk_{idx}", chunk, embedding, file_name)
        
        return {"status": f"PDF '{file_name}' processado e salvo no ChromaDB"}
    except:
        return {"status": f"Erro ao enviar o arquivo '{file_name}' para a base de dados."}

# Perguntar para obter respostar de acordo com as informações da base de dados
@app.post("/ask")
async def ask_question(question: str = Form(...)):
    question_embedding = get_embedding(question)
    results = query_chroma(question_embedding)
    
    context = "\n\n".join(results["documents"][0])
    
    prompt = f"""
    Você é um assistente inteligente. Utilize apenas o contexto fornecido abaixo para responder de forma precisa, clara e objetiva.

    Se o contexto contiver descrições de imagens ou informações provenientes de OCR, **utilize-as apenas se forem úteis e relevantes para responder à pergunta**. Ignore qualquer dado irrelevante, como carimbos, assinaturas, marcas visuais ou elementos que não acrescentem informação direta à resposta.

    Ao utilizar informações de descrições de imagens, **evite expressões como "a imagem acima", "como visto na imagem", "A descrição da imagem apresentada" ou qualquer referência posicional**, pois o usuário não tem acesso às imagens — apenas ao texto extraído da base de dados. Portanto, apresente a informação de forma direta, clara e independente da posição ou da existência da imagem.

    Quando houver um texto na imagem, ela estará delimitada da seguinte forma:
    - 🟩 **Início do texto:** `[Texto encontrado na imagem (OCR) — use apenas se for relevante]`
    - 🟥 **Fim do texto:** `[Fim do Texto encontrado na imagem]`

    Quando houver uma descrição de imagem, ela estará delimitada da seguinte forma:
    - 🟩 **Início da descrição:** `[Descrição da imagem, descrição gerada pela IA — use apenas se for relevante]`
    - 🟥 **Fim da descrição:** `[Fim da descrição da imagem]`

    → Esse conteúdo pode ou não ser relevante para responder à pergunta. **Tenha cuidado ao utilizá-lo, considerando se realmente contribui para uma resposta útil e correta.**  
    **Atenção:** Certifique-se de não descartar informações além das descrições de imagem. Avalie cuidadosamente o que é relevante e o que não é.

    Nunca invente informações. Responda apenas com base no contexto fornecido.  
    Se não encontrar uma resposta no contexto, informe claramente que a informação não está disponível.

    Lembre-se: se a resposta não estiver presente no contexto fornecido, não tente adivinhar, inventar ou gerar informações externas.
    
    ------------------------------

    O contexto a seguir foi extraído de manuais técnicos, onde podem estar presentes etapas, comandos, caminhos de arquivos e procedimentos. Leia com atenção, mesmo que a formatação ou estrutura não esteja perfeita.

    📄 Contexto:
    {context}
    ------------------------------

    ❓ Pergunta:
    {question}

    💡 Responda de forma completa e clara em português:
    """
    response = requests.post(f"{OLLAMA_URL}/api/generate", json={
        "model": MODEL_CHAT,
        "prompt": prompt,
        "stream": False
    })
    response.raise_for_status()
    answer = response.json()["response"]
    return {"answer": answer}


@app.get("/health")
async def health():
    return {"status": "API rodando"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_code(request: AnalyzeRequest):
    try:
        logging.info("=== INICIANDO ANALISE ===")

        # Inicio Timer
        start_time = time.time() 

        # Clonando repositorio Git
        project_path = clone_repo(repo_url=request.project_git_url, branch=request.project_git_branch)

        # Obtendo a estrutura do projeto
        project_struct = generate_project_tree(project_path)

        # Prompt para o modelo LLM entender oque é para fazer com o codigo fornecido
        prompt = f"""
🚨 SUA TAREFA:
Você é um analista de código sênior altamente especializado. Sua missão é analisar criticamente o código fornecido e IDENTIFICAR problemas de forma clara, objetiva e direta.

⚠️ O QUE VOCÊ **NÃO DEVE FAZER**:
- 🚫 NÃO gere documentação.
- 🚫 NÃO descreva funcionalidades.
- 🚫 NÃO explique como a função ou o componente funciona.
- 🚫 NÃO gere steps, passos ou fluxogramas.
- 🚫 NÃO gere tabelas.
- 🚫 NÃO explique parâmetros, tipos, props ou métodos.
- 🚫 NÃO descreva comportamentos esperados do código.
- 🚫 NÃO elogie o código.
- 🚫 NÃO sugira melhorias que envolvam estética, padrões, boas práticas ou comentários.
- 🚫 NÃO gere nenhum texto fora do JSON.

⚠️ O QUE VOCÊ DEVE FAZER:
- ✔️ Identificar problemas de:
  - Qualidade de código
  - Bugs
  - Erros de lógica
  - Vulnerabilidades de segurança
  - Problemas de performance
  - Problemas de manutenibilidade
  - Problemas de confiabilidade
- ✔️ Indicar o arquivo e a linha exata ou intervalo onde o problema ocorre.
- ✔️ Sugerir uma solução prática e direta no campo `"recommendation"`.

Respostas em português!!

🟧 FORMATO OBRIGATÓRIO DA RESPOSTA — EXCLUSIVAMENTE ASSIM:
- Um **array JSON** contendo objetos com os seguintes campos obrigatórios:

[
  {{
    "id": "string",
    "severity": "MINOR|MAJOR|HIGH|CRITICAL|BLOCKER|INFO",
    "category": "CODE_QUALITY|BUG|LOGIC|SECURITY|PERFORMANCE|MAINTAINABILITY|RELIABILITY",
    "description": "string",
    "file": "string",
    "line": "string",
    "recommendation": "string"
  }}
]

🟧 EXEMPLO DE COMO INFORMAR LINHAS:
- Para uma única linha: "line": "10"
- Para um intervalo: "line": "10-15"

🛑 NÃO inclua nenhuma chave externa como "issues", "problems", "data" ou qualquer outro wrapper.
🛑 NÃO inclua comentários, descrições adicionais, texto fora do JSON.
🛑 SE NÃO HOUVER PROBLEMAS NO CÓDIGO, retorne um array vazio: []. Nada além disso.

====== Estrutura do projeto ======
{project_struct}
====== Fim da estrutura do projeto ======

"""
        # Obtendo todos os arquivos do projeto
        project_files = get_project_files(project_path)

        # Criando lista vazia onde será armazenada todos os resultados do LLM
        all_analysis = []

        files_count = 0
        project_total_files = len(project_files)
        files_name = ""

        # Obtendo todos os arquivos que serão processados
        for file_path in project_files:
            file_path = convert_path_to_project(project_path=project_path, file_path=file_path)
            files_name += f"{file_path}\n"

        # Remover o ultimo "\n"
        files_name = files_name.rstrip('\n')

        # Adicionando o número de linhas a esquerda do texto para auxiliar a quantidade de arquivos
        files_name_lines = files_name.split('\n')
        files_name = '\n'.join(f'{idx + 1:>4} | {line}' for idx, line in enumerate(files_name_lines))

        # Adicionando log 
        logging.info(f"====Arquivos que serão analisados====\n{files_name}\n=====================================")
        logging.info("=== RESPOSTA BRUTA ===")

        # Ignorar a etapa de buscar issues do SonarQube caso não estejam configuradas as variáveis de ambiente do SonarQube
        issues_list = []
        if SONAR_URL == "":
            print("Ignorando etapa de integração com o SonarQube. Defina a URL do SonarQube na variável de ambiente SONAR_URL")
            logging.warning("Ignorando etapa de integração com o SonarQube. Defina a URL do SonarQube na variável de ambiente SONAR_URL")
        elif SONAR_TOKEN == "":
            print("Ignorando etapa de integração com o SonarQube. Defina o Token do SonarQube na variável de ambiente SONAR_TOKEN")
            logging.warning("Ignorando etapa de integração com o SonarQube. Defina o Token do SonarQube na variável de ambiente SONAR_TOKEN")
        else:
            # Obtendo issues que foiram enocntradas pelo modelo salvo no sonar
            issues_list = get_sonar_issues(project_key=request.sonar_project_key)

        # Processar cada arquivo individualmente
        # for file_path in project_files[:1]:  # Limita a 3 arquivos para teste
        for file_path in project_files:  # Analisar todos os arquivos do projeto

            # Inicio Timer
            start_time_current_file = time.time() 

            # Contador do arquivos atual
            files_count += 1            
            try:
                logging.info(f"=== Iniciando Validação do arquivo {file_path} ===\n=== Arquivos {files_count}/{project_total_files} ===")
                
                # Analisar com Ollama
                analysis = llm_integration.analyze_with_ollama(prompt=prompt, file_path=file_path, project_path=project_path, analysis=issues_list)

                # Adicionando json gerado pelo LLM na lista
                all_analysis.append(analysis)

                #Adicionando LOG
                logging.info(json.dumps(analysis, indent=2))

                # Obtendo o tempo atual para calcular o tempo levado para processar o arquivo
                end_time = time.time()  # Fim do timer
                duration = end_time - start_time_current_file  # Tempo decorrido em segundos

                # Convertendo o diretorio do arquivo para ficar mais legivel
                file_path = convert_path_to_project(project_path=project_path, file_path=file_path)

                # Adicionando LOG do tempo da analise
                logging.info(f"✅ Análise do arquivo '{file_path}' concluída em {duration:.2f} segundos")
                
            except Exception as e:
                logging.error(f"Erro ao analisar {file_path}: {str(e)}")
        
        # Juntando todas as respostas do LLM que está na lista para um unico json
        response = consolidate_analysis(analysis_list=all_analysis, start_time=start_time, project_path=project_path)

        # Verificar se as variaveis de ambiente do SonarQube estão configuradas, se não, nem tenta executar a parte de integração com SonarQube
        if SONAR_URL == "":
            print("Ignorando etapa de integração com o SonarQube. Defina a URL do SonarQube na variável de ambiente SONAR_URL")
            logging.warning("Ignorando etapa de integração com o SonarQube. Defina a URL do SonarQube na variável de ambiente SONAR_URL")
        elif SONAR_TOKEN == "":
            print("Ignorando etapa de integração com o SonarQube. Defina o Token do SonarQube na variável de ambiente SONAR_TOKEN")
            logging.warning("Ignorando etapa de integração com o SonarQube. Defina o Token do SonarQube na variável de ambiente SONAR_TOKEN")
        else:
            # Converter o json padrão para o json que o SonarQube aceita
            json_sonarqube = convert_analysis_to_sonarqube(response['analysis'])   

            # Adicionar o arquivo json no projeto
            # Salvar o arquivo das issues no diretorio do projeto
            json_issues_path = Path(project_path) / "external-issues.json"
            with open(json_issues_path, 'w', encoding='utf-8') as f:
                json.dump(json_sonarqube, f, ensure_ascii=False)

            # Integração com o sonarqube para enviar as issues
            run_sonar_scanner(project_key=request.sonar_project_key, project_dir=Path(project_path))

        # Adicionando LOG
        logging.info("=== RESPOSTA VALIDADA ===")
        logging.info(response)

        return response
        
    except Exception as e:
        logging.error(f"Erro durante análise: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)