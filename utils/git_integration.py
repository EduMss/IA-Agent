import os
import shutil
from git import Repo, GitCommandError
from urllib.parse import urlparse, urlunparse
from config import GIT_USER, GIT_TOKEN, GIT_PROJECT_TEMP
import logging

# Baixar um repositorio em uma pasta temporaria
def clone_repo(repo_url: str, dest_dir: str = GIT_PROJECT_TEMP, branch: str = "master") -> str:
    """
    Clona o repositório git na pasta destino com autenticação via token.

    :param repo_url: URL HTTPS do repositório (ex: https://github.com/usuario/projeto.git)
    :param dest_dir: pasta local para clonar (pode ser temporária)
    :return: caminho da pasta clonada
    """
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    # Insere usuário e token na URL para autenticação
    parsed_url = urlparse(repo_url)
    netloc = f"{GIT_USER}:{GIT_TOKEN}@{parsed_url.netloc}"
    auth_repo_url = urlunparse((
        parsed_url.scheme,
        netloc,
        parsed_url.path,
        parsed_url.params,
        parsed_url.query,
        parsed_url.fragment
    ))

    # Obtendo o nome do projeto, para criar o sub-diretorio com o nome do projeto
    repo_name = os.path.basename(parsed_url.path).replace(".git", "")
    # Obtendo o caminho completo de onde vai ficar o repositorio clonado
    clone_path = os.path.join(dest_dir, repo_name)

    # caso o projeto exister, atualizar o respositorio 
    if os.path.exists(clone_path):
        try:
            logging.info(f"Repositório encontrado em {clone_path}, atualizando...")
            repo = Repo(clone_path)
            origin = repo.remotes.origin
            origin.pull()
            logging.info("Repositório atualizado com sucesso.")
        # Se de erro, ele vai apagar o diretorio e clonar o diretorio
        except GitCommandError as e:
            logging.warning(f"Erro ao atualizar o repositório: {e}")
            logging.warning("Tentando clonar novamente...")
            import shutil
            shutil.rmtree(clone_path)
            Repo.clone_from(auth_repo_url, clone_path, branch=branch)
            logging.info("Repositório clonado novamente.")
    # Se não existir, clona o repositorio
    else:
        logging.info(f"Clonando repositório em {clone_path}")
        Repo.clone_from(auth_repo_url, clone_path, branch=branch)
        logging.info("Clonagem concluída.")

    return clone_path

def remove_clone_repo(dir_repo: str) -> str:
    if os.path.exists(dir_repo):
        shutil.rmtree(dir_repo)