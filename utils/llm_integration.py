import requests
import logging
from typing import Dict, Any
from config import OLLAMA_URL, MODEL_CODING_ANALYZE, NUM_CTX
import json
from utils.json_treatment import extract_json, sanitize_analysis, get_issues_by_file
from core.analysis import filter_false_positives, convert_path_to_project

def analyze_with_ollama(prompt: str, file_path: str, project_path: str, analysis: list) -> Dict[str, Any]:
    """
    Envia análise para o Ollama com arquivo anexo e processa a resposta
    """
    try:
        # Lendo arquivo para adicionar no prompt
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # Adicionando o número de linhas a esquerda do texto para auxiliar o Modelo
        lines = file_content.split('\n')
        file_content_lines = '\n'.join(f'{idx + 1:>4} | {line}' for idx, line in enumerate(lines))

        # Convertendo o formato do diretorio do arquivo
        file_path_project = convert_path_to_project(project_path=project_path, file_path=file_path)

        # Adicionando LOG
        logging.info(f"Arquivo: {file_path_project} | Quantidade de linhas: {len(lines)}")

        # Obtendo todas as issues já encontradas antes nesse arquivo
        file_issues = get_issues_by_file(analysis=analysis['analysis'], file_path=file_path_project)

        # Adicionando conteudo do arquivo lido no prompt
        full_prompt = f"{prompt}\n"
        full_prompt += f"Além disso, revise se as issues listadas abaixo ainda estão presentes no código."
        full_prompt += f"{file_issues}\n"
        full_prompt += f"""
Caso alguma dessas issues ainda esteja presente no código, retorne essa mesma issue exatamente como ela está, sem alterar nada.
Se alguma dessas issues não for mais aplicável (porque o código foi alterado, corrigido ou não faz mais sentido), **não inclua essa issue no retorno**.
Se você identificar novas issues que não estão na lista, pode adicioná-las normalmente no mesmo padrão.
"""
        full_prompt += f"🟧 CÓDIGO PARA ANÁLISE COM NUMERAÇÃO DE LINHAS À ESQUERDA (NÃO ANALISE ESTA INSTRUÇÃO, APENAS O CÓDIGO):\n"
        full_prompt += f"--- Arquivo: {file_path} ---\n"
        full_prompt += f"==========Inicio do arquivo=========\n"
        full_prompt += f"{file_content_lines}\n==========Fim do arquivo=========\n"
        full_prompt += f"""
🚨 EXECUTE AGORA E RETORNE SOMENTE O JSON.
🟧 ROFORÇANDO O FORMATO OBRIGATÓRIO DA RESPOSTA — EXCLUSIVAMENTE ASSIM:
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
"""

        # LOG
        logging.info(f"=====prompt=====\n{full_prompt}\n=====fim do prompt=====\n\n")

        # Requisitando para o Modelo do Ollama avaliar o codigo
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL_CODING_ANALYZE,
                "prompt": full_prompt,
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "num_ctx": NUM_CTX
                }
            }
        )
        response.raise_for_status()

        # Extrai apenas o conteúdo da resposta do LLM
        response_data = response.json()
        
        # LOG
        # logging.info(f"===response_data===\n{response_data}\n===========")

        # Tratando a resposta
        if "response" in response_data:
            cleaned_response = response_data["response"].replace('```json', '').replace('```', '').strip()

            try:
                parsed = json.loads(cleaned_response)
            except Exception as e:
                # Caso de erro, ele irá gerar um LOG e retornar o parsed vazio
                logging.error(f"Erro no parsing do JSON: {e}")
                cleaned_response = cleaned_response.encode('utf-8').decode('unicode_escape')
                parsed = json.loads(cleaned_response)
        else:
            parsed = extract_json(str(response_data)) or []

        # Se vier como dict, tenta extrair listas
        if isinstance(parsed, dict):
            # Se for um dict, mas com a estrutura direta de uma issue, transforma em lista
            if all(key in parsed for key in ['id', 'severity', 'category', 'description', 'file', 'line', 'recommendation']):
                parsed = [parsed]
            else:
                # Pega a primeira lista encontrada
                for v in parsed.values():
                    if isinstance(v, list):
                        parsed = v
                        break
                else:
                    parsed = []
         # Confirma que o resultado final é lista
        if not isinstance(parsed, list):
            parsed = []

        # Removendo falsos positivos gerados
        parsed = filter_false_positives(parsed)

        # Caso o parsed não esteja vazio, ele irá cuidar que sejá um dicionario bem formado e contendo todos os campos obrigatorio
        if parsed:
            sanitized = sanitize_analysis(parsed)
            return {"analysis": sanitized}
        
        return {"analysis": []}

    except Exception as e:
        logging.error(f"Erro ao chamar Ollama: {str(e)}")
        return {"analysis": []}