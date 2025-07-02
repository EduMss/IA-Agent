import fitz
from PIL import Image
import pytesseract
import io
import base64
import requests
from config import OLLAMA_URL, MODEL_IMAGE_ANALYZE

# Obter uma descrição detalhada de uma imagem de acordo com o base64 da imagem usando o modelo LLM llava 
def describe_image_with_llava(image: Image.Image, description: str, ocr_text="") -> str:
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode()

    # Prompt

    prompt = (
        "Você é um assistente técnico que descreve imagens de manuais e documentos técnicos. "
        "Siga estas regras rigorosamente:\n"
        "1. Descreva APENAS o que pode ser claramente visto, sem suposições ou interpretações\n"
        "2. Foque em elementos técnicos: interfaces, botões, menus, textos visíveis\n"
        "3. Se houver texto legível (incluindo o fornecido por OCR), transcreva exatamente\n"
        "4. Mantenha a descrição objetiva e factual\n"
        "5. Não use frases como 'na imagem' ou 'podemos ver'\n"
        "6. Contexto do documento: " + description + "\n\n"
        "Elementos para descrever (se aplicável):\n"
        "- Janelas/diálogos (títulos, botões, campos)\n"
        "- Textos visíveis (transcrever exatamente)\n"
        "- Elementos de interface (menus, ícones, checkboxes)\n"
        "- Fluxo ou numeração de passos visíveis\n"
        "- Dados técnicos ou valores em campos\n\n"
        "Texto extraído por OCR (pode conter erros):\n" + ocr_text + "\n\n"
        "Descrição técnica objetiva:"
    )
    

    response = requests.post(f"{OLLAMA_URL}/api/generate", json={
        "model": MODEL_IMAGE_ANALYZE, # Modelo LLM desejado para processar
        "prompt": prompt, # prompt explicativo doque ele precisa fazer e entender
        "images": [img_base64], # Base64 da imagem que será descrita
        "stream": False 
    })
    response.raise_for_status()
    return response.json()["response"]

# Extrair textos e imagens do pdf para ser tratado
def extract_text_and_images(file, filename: str, description: str) -> str:
    doc = fitz.open(stream=file.read(), filetype="pdf")
    full_text = f"Documento: {filename}\n\n"
    full_text += f"Uma breve descrição do arquivo fornecido pelo usuário\n{filename}\n\n"
    full_text += f"Conteúdo extraído:\n\n"

    for page_num, page in enumerate(doc, start=1):
        full_text += f"\n--- Página {page_num} ---\n"
        
        # Extrair texto primeiro (em ordem natural)
        text = page.get_text("text")
        full_text += f"\n{text.strip()}\n"
        
        # Extrair imagens separadamente
        image_list = page.get_images(full=True)
            
        for img_index, img in enumerate(image_list, start=1):
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image = Image.open(io.BytesIO(image_bytes))
                
                image = image.convert('L')  # Converter para escala de cinza
                image = image.point(lambda x: 0 if x < 140 else 255)  # Aumentar contraste

                # OCR na imagem
                ocr_text = pytesseract.image_to_string(image)
                
                # Descrição da imagem
                try:
                    descriptionImagem = describe_image_with_llava(image, description, ocr_text)
                    full_text += (
                        f"\n[Descrição da imagem {img_index}]:\n"
                        f"{descriptionImagem.strip()}\n"
                        f"[Fim da descrição da imagem {img_index}]\n"
                    )
                except Exception as e:
                    full_text += f"\n[Erro ao descrever imagem {img_index}]\n"
                    
            except Exception as e:
                full_text += f"\n[Erro ao processar imagem {img_index}]\n"

    return full_text