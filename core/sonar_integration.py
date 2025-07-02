from config import SONAR_URL, SONAR_TOKEN, SONAR_ENGINE_ID, SONAR_RULES_ID
from typing import List, Dict
from pathlib import Path
import requests
import subprocess
import platform
import os
import logging

def get_sonar_issues(project_key: str) -> List[Dict]:
    """
    Obtém issues do SonarQube filtrados por severidade
    
    Args:
        project_key: Chave do projeto no SonarQube
        scope: Nível de severidade (critical, major, etc.)
    
    Returns:
        Lista de issues no formato simplificado
    """
    try:
        response = requests.get(
            f"{SONAR_URL}/api/issues/search",
            params={
                "componentKeys": project_key,
                "rules": f"external_{SONAR_ENGINE_ID}:{SONAR_RULES_ID}"
            },
            auth=(SONAR_TOKEN, "")
        )
        
        response.raise_for_status()
        
        # Simplifica a resposta do Sonar
        return {
            "analysis": [
                {
                    "id": issue["key"],
                    "severity": issue["severity"],
                    "category": issue["rule"],
                    "description": issue["message"],
                    "file": issue["component"].split(":")[-1],
                    "line": (
                        str(start_line) if (start_line := issue.get("textRange", {}).get("startLine", issue.get("line")))
                        == (end_line := issue.get("textRange", {}).get("endLine", issue.get("line")))
                        else f"{start_line}-{end_line}"
                    ),
                    "recommendation": "**sem recommendation, gere uma de acordo com as informações da issues**"
                }
                for issue in response.json().get("issues", [])
            ]
        }
    
    except Exception as e:
        logging.error(f"Erro ao buscar issues do SonarQube: {str(e)}")
        return []
    

def run_sonar_scanner(project_key: str, project_dir: Path):
    # Detecta o sistema operacional
    sistema = platform.system()

    # Verificando qual é sistema operacional, para selecionar o sonar-scanner
    if sistema == 'Windows':
        scanner_path = Path('dependencias/Windows/sonar-scanner/bin/sonar-scanner.bat')
    elif sistema == 'Linux':
        scanner_path = Path('dependencias/Linux/sonar-scanner/bin/sonar-scanner')
    else:
        logging.error(f"❌ Sistema operacional não suportado: {sistema}")
        raise Exception(f"❌ Sistema operacional não suportado: {sistema}")

    # Obtendo o path correto
    scanner_path = scanner_path.resolve()
    project_dir = project_dir.resolve()

    # Verificando se o diretorio existe
    if not os.path.isdir(project_dir):
        logging.error(f"❌ Diretório do projeto não encontrado: {project_dir}")
        raise FileNotFoundError(f"❌ Diretório do projeto não encontrado: {project_dir}")

    # Verifica se o arquivo existe
    if not os.path.isfile(scanner_path):
        logging.error(f"❌ SonarScanner não encontrado em {scanner_path}")
        raise FileNotFoundError(f"❌ SonarScanner não encontrado em {scanner_path}")

    try:
        # Executando o sonar-scanner para enviar as issues para o SonarQube
        result = subprocess.run(
            [
                scanner_path,
                f"-Dsonar.projectKey={project_key}",
                f"-Dsonar.sources=.",
                f"-Dsonar.host.url={SONAR_URL}",
                f"-Dsonar.token={SONAR_TOKEN}",
                f"-Dsonar.externalIssuesReportPaths=external-issues.json",
            ],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(project_dir) # Informando em qual diretorio que será executado o comando
        )

        # Adicionando LOG se tudo correr bem
        logging.info(f"✅ Saída: {result.stdout}")
    except subprocess.CalledProcessError as e:
        # Adicionando LOG de erro
        logging.error(f"❌ Erro: {e.stderr}")