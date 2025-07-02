import chromadb
from config import CHROMADB_HOST, CHROMADB_PORT, VECTOR_SEARCH_N_RESULTS
import logging
from chromadb.errors import ChromaError

# Configura log
logging.basicConfig(level=logging.INFO)

# 🟢 Conectar com o ChromaDB
try:
    client = chromadb.HttpClient(
        host=CHROMADB_HOST,
        port=CHROMADB_PORT
    )
    # Testa conexão
    client.heartbeat()
    logging.info("✅ Conectado ao ChromaDB com sucesso.")
except Exception as e:
    logging.error(f"❌ Erro ao conectar com ChromaDB: {e}")
    raise



# Selecionando/Criando a collections "pdf_documents" dentro do chromadb
try:
    collection = client.get_or_create_collection("pdf_documents")
except Exception as e:
    logging.error(f"❌ Erro ao acessar/criar collection no ChromaDB: {e}")
    raise


# Deletando o conteudo no chromadb do arquivo pdf com o mesmo nome que está sendo passado pelo argunto do metodo
def delete_from_chroma(file_name: str):
    try:
        """Remove documentos da coleção com base no nome do arquivo"""
        results = collection.get(where={"file": file_name})
        if results and results.get("ids"):
            collection.delete(ids=results["ids"])
            logging.info(f"🗑️ Dados do arquivo '{file_name}' deletados do ChromaDB.")
        else:
            logging.info(f"ℹ️ Nenhum dado encontrado para deletar com o arquivo '{file_name}'.")
    except ChromaError as e:
        logging.error(f"❌ Erro no ChromaDB ao deletar '{file_name}': {e}")
    except Exception as e:
        logging.error(f"❌ Erro inesperado ao deletar '{file_name}': {e}")


# Adicionando conteudo em embeddings do pdf, gerado pela IA, na base de dados do chromadb 
def add_to_chroma(id: str, text: str, embedding: list, file_name: str):
    try:
        collection.add(
            ids=[id],
            documents=[text],
            embeddings=[embedding],
            metadatas={"file": file_name} # Nome do arquivo para conseguir excluir quando for atualizar os dados do pdf
        )
        logging.info(f"✅ Documento '{id}' do arquivo '{file_name}' adicionado ao ChromaDB.")
    except ChromaError as e:
        logging.error(f"❌ Erro no ChromaDB ao adicionar '{id}': {e}")
    except Exception as e:
        logging.error(f"❌ Erro inesperado ao adicionar '{id}': {e}")


# Buscando informação na base de dados do chromadb de acordo com o embedding fornecido
def query_chroma(embedding: list, n_results=VECTOR_SEARCH_N_RESULTS):
    try:
        results = collection.query(
            query_embeddings=[embedding],
            n_results=n_results
        )
        logging.info(f"🔎 Query no ChromaDB retornou {len(results.get('ids', []))} resultados.")
        return results
    except ChromaError as e:
        logging.error(f"❌ Erro no ChromaDB durante a busca: {e}")
    except Exception as e:
        logging.error(f"❌ Erro inesperado durante a busca: {e}")
    
    # Retorno seguro em caso de erro
    return {"ids": [], "documents": [], "embeddings": [], "metadatas": []}  