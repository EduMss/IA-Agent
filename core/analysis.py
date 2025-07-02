import os
from typing import Dict, List
from pathlib import Path
import logging
from config import IGNORED_FOLDERS, IGNORED_FILES, ACCEPTED_EXTENSIONS, BAD_PATTERNS
import time

# Esse metodo irá converter o diretorio "src/components/arquivos.js" para "C:\\Diretorio\\Projeto\\src\\components\\arquivos.js"
def convert_project_to_path(project_path: str, file_path: str) -> str:
    # Irá juntar os diretorio (podendo ficar tanto como "\\" e "/")
    full_path = Path(project_path) / Path(file_path)
    # Forçando a saida como "//"
    return str(full_path).replace('/', '\\')


# Esse metodo irá converter o diretorio "C:\\Diretorio\\Projeto\\src\\components\\arquivos.js" para "src/components/arquivos.js"
def convert_path_to_project(project_path: str, file_path: str) -> str:
    # Adicionando "\\" no final do caminho do projeto
    path_project = str(Path(project_path)) + "\\"
    # Removendo o caminho do projeto
    path = file_path.replace(path_project, '')
    # Alterando o "\\" para "/"
    path = path.replace("\\", '/')
    return path

def generate_project_tree(project_path: str) -> Dict:
    """Gera estrutura do projeto em formato de dicionário"""

    # Usa a biblioteca pathlib para manipular o caminho de forma mais robusta, multiplataforma e elegante.
    project_root = Path(project_path)

    # Cria a estrutura inicial do dicionário
    structure = {
        "name": project_root.name,
        "type": "directory",
        "children": []
    }

    # Percorre todos os arquivos e subpastas diretamente dentro do diretório (*)
    for item in project_root.glob("*"):
        # Chama recursivamente a função generate_project_tree() passando o caminho da subpasta
        # Adiciona a árvore dessa subpasta na lista "children".
        if item.is_dir():
            # Ignorando diretorios desnecessários
            if item.name in IGNORED_FOLDERS:
                continue  

            structure["children"].append(generate_project_tree(str(item)))

        # Se for um arquivo, cria um dicionário com as informações do arquivo
        else:
            # Ignorando arquivos desnecessários
            if item.name in IGNORED_FILES:
                continue  

            structure["children"].append({
                "name": item.name,
                "type": "file",
                "size": item.stat().st_size
            })
    
    return structure


def get_project_files(project_path: str) -> List[str]:
    """Retorna lista todos arquivos no projeto"""
    # Criando uma lista vazia onde será guardado todos os diretorios dos arquivos encontrados
    project_files = []

    # Percorrendo por todos os arquivos, sub-diretorio e arquivos dentro dos sub-diretorio
    for root, dirs, files in os.walk(project_path):
        # Filtra diretórios ignorados (remove da lista antes de entrar)
        dirs[:] = [d for d in dirs if d not in IGNORED_FOLDERS]

        for file in files:
            # Ignorar arquivos ocultos (que começam com ponto '.')
            if file.startswith('.'):
                continue

             # Ignorar arquivos específicos
            if file in IGNORED_FILES:
                continue

            # Formatos que será aceito para avaliar
            if file.endswith(ACCEPTED_EXTENSIONS):
                # Adicionando o arquivo encontrado na lista
                project_files.append(os.path.join(root, file))
    return project_files


def filter_false_positives(analysis: list) -> list:
    filtered = []
    for item in analysis:
        description = item.get("description", "").lower()

        if any(bad in description for bad in BAD_PATTERNS):
            continue  # Ignora esse item

        filtered.append(item)

    return filtered


def consolidate_analysis(analysis_list: List[dict], start_time: time, project_path: str) -> dict:
    """Combina análises de múltiplos arquivos"""

    # LOG
    logging.info(f"=== Todas as issues ===")

    # Criando o json default do analysis
    consolidated = {"analysis": []}
    # Percorrentando a Lisca recebida com os json's
    for analysis in analysis_list:
        # Melhorando o diretorio de saida para ficar visualmente melhor
        # Ao inves de mostrar o diretorio completo, ira mostrar somente o caminho do arquivo dentro do projeto
        for issue in analysis["analysis"]:
            if "file" in issue and issue["file"]:
                issue["file"] = convert_path_to_project(project_path=project_path, file_path=issue["file"])

        # LOG
        logging.info(f"{analysis}")

        # Obtendo o conteudo do json, ele vai receber algo assim: {"analysis": [{... meu json ....}]}
        if "analysis" in analysis and isinstance(analysis["analysis"], list):
            # Obtendo json e adicionando no json default criado anteriormente
            consolidated["analysis"].extend(analysis["analysis"])
        else:
            # Caso não for do jeito que o projeto estava esperando, ele irá gerar um aviso
            logging.warning(f"Formato inesperado em {analysis}, adicionando como issue individual")
            consolidated["analysis"].append(analysis)

    #LOG
    logging.info(f"=======================")

    
    end_time = time.time()  # 🕒 Fim do timer
    duration = end_time - start_time  # ⏱️ Tempo decorrido em segundos

    # Adicionando LOG do tempo da analise
    logging.info(f"✅ Análise concluída em {duration:.2f} segundos")

    # Adicionando o conteudo do 'statistics' no json
    consolidated["statistics"] = {
        "total_files_analyzed": len(analysis_list),
        "total_issues_found": len(consolidated["analysis"]),
        "total_time": f"{duration:.2f} segundos"
    }

    return consolidated

