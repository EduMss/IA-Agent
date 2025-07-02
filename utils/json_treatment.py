import json
import re
import logging
from typing import List
from config import SONAR_ENGINE_ID, SONAR_RULES_ID, SONAR_NOME

def map_category_to_type(category: str) -> str:
    category = category.upper()
    if category in ["SECURITY"]:
        return "VULNERABILITY"
    if category in ["BUG", "LOGIC"]:
        return "BUG"
    return "CODE_SMELL"

def map_category_to_quality(category: str) -> str:
    category_map = {
        "SECURITY": "SECURITY",
        "PERFORMANCE": "RELIABILITY",
        "BUG": "RELIABILITY",
        "LOGIC": "RELIABILITY",
        "CODE_QUALITY": "MAINTAINABILITY",
        "MAINTAINABILITY": "MAINTAINABILITY",
        "RELIABILITY": "RELIABILITY"
    }
    return category_map.get(category.upper(), "MAINTAINABILITY")

def map_severity(severity: str) -> str:
    """
    Mapeia severidades genéricas para as aceitas pelo SonarQube.
    """
    severity = severity.upper()
    mapping = {
        "LOW": "MINOR",
        "MEDIUM": "MAJOR",
        "HIGH": "CRITICAL",   # Pode ser MAJOR se quiser
        "CRITICAL": "CRITICAL",
        "BLOCKER": "BLOCKER",
        "INFO": "INFO"
    }
    return mapping.get(severity.upper(), "INFO")  # Default para INFO se não encontrar

# Converter o json padrão para o json do sonarqube
def convert_analysis_to_sonarqube(analysis: List[dict]) -> dict:
    rules = [
        {
            "id": SONAR_RULES_ID,
            "name": f"Issue Detector - {SONAR_NOME}",
            "description": f"Regra para detectar problemas encontrados pelo {SONAR_NOME}.",
            "engineId": SONAR_ENGINE_ID,
            "cleanCodeAttribute": "CONVENTIONAL",
            "type": "CODE_SMELL",
            "severity": "INFO",
            "impacts": [
                {
                    "softwareQuality": "MAINTAINABILITY",
                    "severity": "HIGH"
                }
            ]
        }
    ]
        
    issues = []

    for item in analysis:
        line = item.get("line", "1")
        start_line = int(line.split('-')[0]) if '-' in line else int(line)
        end_line = int(line.split('-')[1]) if '-' in line else start_line

        # === Construindo a issue ===
        issue = {
            "ruleId": SONAR_RULES_ID,
            "effortMinutes": 5,  # Você pode ajustar conforme necessário
            "primaryLocation": {
                "message": item.get("description", "No description provided."),
                "filePath": item.get("file", ""),
                "textRange": {
                    "startLine": start_line,
                    "endLine": end_line,
                    "startColumn": 1
                }
            }
        }
        issues.append(issue)

    return {
        "rules": rules,
        "issues": issues
    }


# Retorna todas as Issues que tenham um "file" especifico
def get_issues_by_file(analysis: List[dict], file_path: str) -> List[dict]:
    """
    Retorna todas as issues que pertencem ao arquivo informado.

    :param analysis: Lista de issues.
    :param file_path: Caminho do arquivo (ex.: 'public/index.html').
    :return: Lista de issues filtradas.
    """
    return [issue for issue in analysis if issue.get('file') == file_path]

def extract_analysis_json(response_text: str):
    try:
        # Remove delimitadores de código se tiver
        cleaned = response_text.strip().replace("```json", "").replace("```", "")

        # Faz parsing mesmo se for string com \n escapado
        if isinstance(cleaned, str):
            try:
                parsed = json.loads(cleaned)
            except json.JSONDecodeError:
                # Tenta novamente removendo barras extras
                cleaned = cleaned.encode('utf-8').decode('unicode_escape')
                parsed = json.loads(cleaned)
        else:
            parsed = cleaned

        # Se vier encapsulado como {'issues': [...]}
        if isinstance(parsed, dict):
            if 'issues' in parsed:
                return parsed['issues']
            if 'problems' in parsed:
                return parsed['problems']
            # Se vier chave desconhecida, pega o primeiro array que encontrar
            for v in parsed.values():
                if isinstance(v, list):
                    return v
            return []

        # Se já for lista direta
        if isinstance(parsed, list):
            return parsed

        return []

    except Exception as e:
        logging.error(f"Erro ao extrair JSON: {e}")
        return []

def extract_json(text):
    try:
        # Primeiro, tenta carregar diretamente
        return json.loads(text)
    except json.JSONDecodeError:
        # Se falhar, tenta extrair o conteúdo entre os primeiros colchetes
        matches = re.findall(r"\{.*\}|\[.*\]", text, re.DOTALL)
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
    return None


def get_default_value(field):
    # Configurações padrões do json das issues
    defaults = {
        "id": "unknown",
        "severity": "LOW",
        "category": "CODE_QUALITY",
        "description": "Descrição não fornecida",
        "file": "desconhecido",
        "line": "0",
        "recommendation": "Revisar manualmente"
    }
    return defaults.get(field, None)

def sanitize_analysis(analysis_list):
    # Lista onde será adicionados os itens tratados
    sanitized = []
    # Lista de campos obrigatorio
    required_fields = ["id", "severity", "category", "description", "file", "line", "recommendation"]

    # percorrer pela lista para tratar cada item
    for item in analysis_list:
        # Verifica se o item não é uma string ou outro tipo, se for, ele ignora e não processa
        if not isinstance(item, dict):
            continue  # Ignorar itens não-dicionário

        # Criando um dicionário vazio que irá receber os campos obrigatórios
        sanitized_item = {}

        item['line'] = str(item.get('line', '')) if item.get('line') is not None else ''

        # Ele tenta obter o valor de cada campo, se não conseguir, ele irá adicionar o valor padrão informados no metodo get_default_value
        for field in required_fields:
            sanitized_item[field] = item.get(field, get_default_value(field))

        # Adiciona o item tratado na lista
        sanitized.append(sanitized_item)

    return sanitized