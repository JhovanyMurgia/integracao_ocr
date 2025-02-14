import re
import cv2
import os

from auxiliary_functions import calculate_base_angle, average_angles_boxes, rotate_image, group_words_by_lines
from config_run_model import run_ocr

# Funções utilizadas para extrair informações do texto de ambos os tipos de CNH
#############################################################################

# Pipeline para OCR
def pipeline_ocr(model, image_path, limiar_conf=0.5, show_image=False, debug=False):

    result = run_ocr(model, image_path, show_image)

    # Obter a inclinação dos retângulos com mais de 4 caracteres
    angle_list = []
    for block in result.pages[0].blocks:
        for line in block.lines:
            for word in line.words:
                vertices = word.geometry
                angle = calculate_base_angle(vertices)
                # Excluir valores discrepantes
                if -10 < angle < 10:
                    angle_list.append(angle)

    # Função que ordena e calcula a média dos quatro ângulos centrais da lista
    mean_angle = average_angles_boxes(angle_list)

    if mean_angle > 1 or mean_angle < -1:
        # Ajusta inclinação da imagem
        rotated_image = rotate_image(image_path, mean_angle)

        # Salvar a imagem rotacionada
        cv2.imwrite('rotated_image.jpg', rotated_image)

        image_path = "rotated_image.jpg"

        result = run_ocr(model, image_path, show_image)

        # Apagar o arquivo temporário
        os.remove("rotated_image.jpg")

    # Extrair o texto das linhas dentro do intervalo ajustado
    words_data = []

    # Extrair o texto e a geometria
    for block in result.pages[0].blocks:
        for line in block.lines:
            for word in line.words:
                if word.confidence > limiar_conf:
                    word_data = {
                        "text": word.value,  # O texto da palavra
                        "geometry": word.geometry  # Coordenadas normalizadas
                    }
                    words_data.append(word_data)

    # Agrupa as palavras em linhas
    lines = group_words_by_lines(words_data)

    if debug:
        # Exibe as linhas como texto (opcional)
        for i, line_text in enumerate(lines):
            print(f"Linha {i + 1}: {line_text}")

    return lines



# Funções utilizadas para extrair informações do texto do novo RG
################################################################


def extract_name(ocr_output):
    for i, line in enumerate(ocr_output):
        line = line.strip()
        if re.search(r'\bNOME\b', line, re.IGNORECASE):  # Procura a palavra "NOME"
            if i + 1 < len(ocr_output):  # Verifica se há uma próxima linha
                return ocr_output[i + 1].strip()  # Retorna a linha seguinte como nome

    return None  # Retorna None se não encontrar "NOME" ou se não houver próxima linha



def extract_filiation(ocr_output):
    filiation = []
    capture = False  # Flag para indicar quando começar a capturar os nomes
    
    for line in ocr_output:
        line = line.strip()
        
        if re.search(r'\bFILIA[ÇC]AO\b', line, re.IGNORECASE):  
            capture = True  # Começa a capturar a partir da linha seguinte
            continue  # Pula a linha atual
        
        if re.search(r'\bPERMISSAO\b', line, re.IGNORECASE):  
            break  # Para de capturar ao encontrar "PERMISSÃO"

        if capture:  
            filiation.append(line)  # Armazena as linhas de filiação
    
    return " ".join(filiation) if filiation else None  # Retorna uma string única ou None


def extract_num_rg(ocr_output):
    rg_pattern = re.compile(r'\b[A-Z]?(\d{6,9})\b', re.IGNORECASE)  
    # Captura um número de 6 a 9 dígitos, opcionalmente precedido por uma letra
    
    for line in ocr_output[:10]:  # Limita a busca às 10 primeiras linhas
        line = line.strip()
        match = rg_pattern.search(line)
        if match:
            return match.group(1)  # Retorna apenas os dígitos, ignorando a letra inicial

    return None  # Retorna None se nenhum RG for encontrado




def extract_cpf(ocr_output):
    cpf_patterns = [
        re.compile(r'CPF[\s:]*([0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2})'),
        re.compile(r'\b([0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2})\b')
    ]

    for pattern in cpf_patterns:
        for line in ocr_output:  
            line = line.strip()
            match = pattern.search(line)
            if match:
                return match.group(1)  # Retorna o primeiro RG encontrado

    return None

def extract_num_cnh(ocr_output):
    rg_pattern = re.compile(r'\b\d{11}\b')  # 

    for line in ocr_output[10:]:  # Limita a busca às 10 ultimas linhas
        line = line.strip()
        match = rg_pattern.search(line)
        if match:
            return match.group()  # Retorna o primeiro número encontrado

    return None  


def extract_cnh_dates(ocr_output):
    date_pattern = re.compile(r'\b(\d{2}/\d{2}/\d{4})\b')  # Captura datas no formato dd/mm/aaaa
    dates = []

    for line in ocr_output:
        line = line.strip()
        matches = date_pattern.findall(line)  # Encontra todas as datas na linha
        dates.extend(matches)  # Adiciona as datas encontradas à lista

    # Mapeia as três primeiras datas para as respectivas variáveis
    dt_nasc = dates[0] if len(dates) > 0 else None
    validade = dates[1] if len(dates) > 1 else None
    primeira_cnh = dates[2] if len(dates) > 2 else None

    return dt_nasc, validade, primeira_cnh


# Pipeline para extrair informações do RG novo


def extract_cnh(model, path, limiar_conf=0.5, show_image=False, debug=False):
    try:
        result = pipeline_ocr(model, path, limiar_conf,
                              show_image=show_image, debug=debug)
        nome = extract_name(result)
        filiacao = extract_filiation(result)
        dt_nasc, validade, primeira_cnh = extract_cnh_dates(result)
        cpf= extract_cpf(result)
        rg = extract_num_rg(result)
        cnh = extract_num_cnh(result)
        
    except FileNotFoundError as e:
        print(
            f"Imagem não fornecida ou não encontrada no caminho fornecido: {path}")
        nome = None
        filiacao = None
        dt_nasc = None
        validade = None
        primeira_cnh = None
        cpf = None
        rg = None
        cnh = None
        

    dados = {
        "RG": rg,
        "CPF": cpf,
        "CNH": cnh,
        "Nome": nome,        
        "Filiacao": filiacao,        
        "Data de Nascimento": dt_nasc,
        "Validade": validade,
        "Primeira CNH": primeira_cnh
    }
    return dados
