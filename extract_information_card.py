import re
import cv2
import os

from auxiliary_functions import calculate_base_angle, average_angles_boxes, rotate_image, group_words_by_lines
from config_run_model import run_ocr

def pipeline_ocr_card(model, image_path, show_image=False):
    result = run_ocr(model, image_path, show_image)

    meta_data = result

    # Obter a inclinação dos retângulos com mais de 4 caracteres
    angle_list = []
    for block in result.pages[0].blocks:
        for line in block.lines:
            for word in line.words:
                vertices = word.geometry
                angle = calculate_base_angle(vertices)
                # Excluir valores discrepantes
                if -5 < angle < 5:
                    angle_list.append(angle)

    if len(angle_list) > 0:
        # Função que ordena e calcula a média dos quatro ângulos centrais da lista
        mean_angle = average_angles_boxes(angle_list)
    else:
        mean_angle = 0

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
                word_data = {
                    "text": word.value,  # O texto da palavra
                    "geometry": word.geometry  # Coordenadas normalizadas
                }
                words_data.append(word_data)

    # Agrupa as palavras em linhas
    lines = group_words_by_lines(words_data)

    return lines, meta_data


# Funções para separar as entidades no OCR
# Tipo 1 - cartão mais comum
def regex_card_type_1(lines):
    extracted_data = {
        "Nome": None,
        "Data de Nascimento": None,
        "Sexo": None,
        "Numero do Cartao": None
    }

    for i, line in enumerate(lines):
        # Remover caracteres especiais e limpar espaços extras
        clean_line = re.sub(r'[.,;:_-]', '', line)
        clean_line = re.sub(r'\s+', ' ', clean_line).strip()

        # Tenta encontrar a matrícula (XXX XXXX XXXX XXXX)
        if re.match(r"^\d{3}(?: \d{4}){3}$", clean_line):
            registration = clean_line.strip()
            birth_date, gender, name = None, None, None

            # Subir até encontrar a data de nascimento e sexo
            j = i - 1
            while j >= 0:
                prev_line = re.sub(r'[.,;:_-]', '', lines[j]).strip()
                birth_date_match = re.search(r"\d{2}/\d{2}/\d{4}", prev_line)

                if birth_date_match:
                    birth_date = birth_date_match.group(0)
                    gender = prev_line.strip()[-1] if prev_line.strip()[-1] in "MF" else None
                    break  # Para de subir ao encontrar uma data válida
                j -= 1  # Continua subindo

            # Subir até encontrar um nome válido (pelo menos duas palavras)
            j -= 1
            while j >= 0:
                candidate_name = re.sub(r'[.,;:_-]', '', lines[j]).strip()
                if len(candidate_name.split()) >= 2:
                    name = candidate_name
                    break  # Para de subir ao encontrar um nome válido
                j -= 1  # Continua subindo

            # Adiciona os dados extraídos à lista
            extracted_data = {
                "Nome": name,
                "Data de Nascimento": birth_date,
                "Sexo": gender,
                "Numero do Cartao": registration
            }

    return extracted_data

# Cartão tipo 2 - sem data de nascimento e sexo
def regex_card_type_2(lines):
    extracted_data = {
        "Nome": None,
        "Data de Nascimento": None,
        "Sexo": None,
        "Numero do Cartao": None
    }

    for i, line in enumerate(lines):
        # Tenta encontrar o número de matrícula
        result = re.search(r"\d{15}", line)
        if result:
            registration = result.group().strip()
            birth_date = None
            gender = None
            if i > 0:
                name = ""
                for j in range(i):
                    if j < (i - 1):
                        name = name + lines[j] + " "
                    else:
                        name = name + lines[j]
            else:
                name = None

            # Adiciona as informações extraídas
            extracted_data = {
                "Nome": name,
                "Data de Nascimento": birth_date,
                "Sexo": gender,
                "Numero do Cartao": registration
            }

    return extracted_data

def ocr_card(model, image_path, show_image=False):
#
    lines, meta_data = pipeline_ocr_card(model, image_path, show_image=show_image)
    # Separação das entidades
    result = regex_card_type_1(lines) 
    if result["Numero do Cartao"] is None:
        result = regex_card_type_2(lines)
    
    return result, meta_data
