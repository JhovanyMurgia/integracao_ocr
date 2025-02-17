import re
import cv2
import os

from auxiliary_functions import calculate_base_angle, average_angles_boxes, rotate_image, group_words_by_lines
from config_run_model import run_ocr



# Funções utilizadas para extrair informações do texto de ambos os tipos de RG
#############################################################################

# Pipeline para OCR
def pipeline_ocr(model, image_path, limiar_conf=0.5, show_image=False, debug=False):

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
                if -10 < angle < 10:
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

    return lines, meta_data


# Função para extrair informações do text do RG antigo
######################################################

def extract_num_rg_antigo(ocr_output):

    rg_patterns = [
        # Após "REGISTRO GERAL"
        re.compile(r'REGISTRO GERAL[\s:]*([0-9]{1,2}\.?[0-9]{3}\.?[0-9]{3})'),
        # (22.875.151-94 ou 22.875.151-9)
        re.compile(r'\b([0-9]{2,3}\.[0-9]{3}\.[0-9]{3}-[0-9]{1,2})\b'),
        # Formato com pontos (1.234.567 ou 12.345.678)
        re.compile(r'\b([0-9]{1,2}\.[0-9]{3}\.[0-9]{3})\b'),
        # Formato com espaços (1 234 567 ou 12 345 678)
        re.compile(r'\b([0-9]{1,2}\s[0-9]{3}\s[0-9]{3})\b'),
        re.compile(r'\b([0-9]{3}\.[0-9]{3})\b')  # (123.456)

    ]

    for pattern in rg_patterns:
        for line in ocr_output[:4]:  # Limita a iteração às 4 primeiras linhas
            line = line.strip()
            match = pattern.search(line)
            if match:
                return match.group(1)  # Retorna o primeiro RG encontrado

    return None  # Retorna None se nenhum RG for encontrado


def extract_dt_expedicao_nome_filiacao(ocr_output):
    dt_expedicao_patterns = [
        # Formato com barras (12/34/5678)
        re.compile(r'\b([0-9]{2}/[0-9]{2}/[0-9]{4})\b'),
        # Formato com hífens (12-34-5678)
        re.compile(r'\b([0-9]{2}-[0-9]{2}-[0-9]{4})\b'),
        # Formato com pontos (12.34.5678)
        re.compile(r'\b([0-9]{2}\.[0-9]{2}\.[0-9]{4})\b')
    ]

    for pattern in dt_expedicao_patterns:
        for i, line in enumerate(ocr_output):  # Percorre todas as linhas
            line = line.strip()
            match = pattern.search(line)
            if match:
                dt_expedicao = match.group(1)

                # Verifica o nome
                nome = None
                if i + 1 < len(ocr_output):
                    next_line = ocr_output[i + 1].strip()
                    if len(next_line.split()) > 1:  # Verifica se a linha tem mais de uma palavra
                        nome = next_line
                        next_line = ocr_output[i + 2].strip()
                        # Verifica se a linha tem mais de uma palavra
                        if len(next_line.split()) > 1:
                            filiacao = ocr_output[i + 2].strip() + " " + ocr_output[i + 3].strip(
                            ) if i + 3 < len(ocr_output) else None
                            # Limpa o valor do nome e da filiação
                            if nome != None:
                                nome = re.sub(r'\bNOME\b', '', nome).strip()
                            if filiacao != None:
                                filiacao = re.sub(
                                    r'\bFILIAÇAO\b', '', filiacao).strip()
                            return dt_expedicao, nome, filiacao
                        else:
                            filiacao = ocr_output[i + 3].strip() + " " + ocr_output[i + 4].strip(
                            ) if i + 4 < len(ocr_output) else None
                            # Limpa o valor do nome e da filiação
                            if nome != None:
                                nome = re.sub(r'\bNOME\b', '', nome).strip()
                            if filiacao != None:
                                filiacao = re.sub(
                                    r'\bFILIAÇAO\b', '', filiacao).strip()
                            return dt_expedicao, nome, filiacao

                    else:   # Pula para a próxima linha se tiver apenas uma palavra
                        nome = ocr_output[i + 2].strip()
                        next_line = ocr_output[i + 3].strip()
                        # Verifica se a linha tem mais de uma palavra
                        if len(next_line.split()) > 1:
                            filiacao = ocr_output[i + 3].strip() + " " + ocr_output[i + 4].strip(
                            ) if i + 3 < len(ocr_output) else None
                            # Limpa o valor do nome e da filiação
                            if nome != None:
                                nome = re.sub(r'\bNOME\b', '', nome).strip()
                            if filiacao != None:
                                filiacao = re.sub(
                                    r'\bFILIAÇAO\b', '', filiacao).strip()
                            return dt_expedicao, nome, filiacao
                        else:
                            filiacao = ocr_output[i + 4].strip() + " " + ocr_output[i + 5].strip(
                            ) if i + 5 < len(ocr_output) else None
                            # Limpa o valor do nome e da filiação
                            if nome != None:
                                nome = re.sub(r'\bNOME\b', '', nome).strip()
                            if filiacao != None:
                                filiacao = re.sub(
                                    r'\bFILIAÇAO\b', '', filiacao).strip()
                            return dt_expedicao, nome, filiacao

    return None, None, None  # Retorna None se nenhum padrão for encontrado


def extract_cpf_antigo(ocr_output):
    pattern = re.compile(r'\b([0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2})\b')

    for line in ocr_output[4:]:  # Começa a partir da quinta linha
        line = line.strip()
        match = pattern.search(line)
        if match:
            return match.group(1)  # Retorna o primeiro CPF encontrado

    return None  # Retorna None se nenhum CPF for encontrado


def extract_dt_nasc_antigo(ocr_output):

    dt_nasc_patterns = [
        # Formato com barras (12/34/5678)
        re.compile(r'\b([0-9]{2}/[0-9]{2}/[0-9]{4})\b'),
        # Formato com hífens (12-34-5678)
        re.compile(r'\b([0-9]{2}-[0-9]{2}-[0-9]{4})\b'),
        # Formato com pontos (12.34.5678)
        re.compile(r'\b([0-9]{2}\.[0-9]{2}\.[0-9]{4})\b')
    ]

    for pattern in dt_nasc_patterns:
        for line in ocr_output[4:]:  # Limita a iteração às 4 primeiras linhas
            line = line.strip()
            match = pattern.search(line)
            if match:
                return match.group(1)  # Retorna o primeiro RG encontrado

    return None  # Retorna None se nenhum RG for encontrado


# Pipeline para extrair informações do RG antigo


def extract_rg_antigo(model, path_verso, limiar_conf=0.5, show_image=False, debug=False):
    try:
        # Chama a função e obtém o resultado
        lines, meta_data = pipeline_ocr(
            model, path_verso, limiar_conf=limiar_conf, show_image=show_image, debug=debug)
        # Extrai as informações
        rg = extract_num_rg_antigo(lines)
        dt_expedicao, nome, filiacao = extract_dt_expedicao_nome_filiacao(
            lines)
        cpf = extract_cpf_antigo(lines)
        dt_nasc = extract_dt_nasc_antigo(lines)

    except FileNotFoundError as e:
        print(
            f"Imagem não fornecida ou não encontrada no caminho fornecido: {path_verso}")
        nome = None
        filiacao = None
        dt_nasc = None
        rg = None
        cpf = None
        dt_expedicao = None

    dados = {
        "RG": rg,
        "Data de Expedicao": dt_expedicao,
        "Nome": nome,
        "Filiacao": filiacao,
        "CPF": cpf,
        "Data de Nascimento": dt_nasc
    }
    return dados, meta_data


# Funções utilizadas para extrair informações do texto do novo RG
################################################################

def extract_name(ocr_output):
    for line in ocr_output:  # Começa a partir da quinta linha
        line = line.strip()
        # Usa regex para encontrar o nome após a palavra "NOME"
        match = re.search(r'NOME\s+(.+)', line)
        if match:
            return match.group(1)

    return None  # Retorna None se nenhum CPF for encontrado


def extract_filiation(ocr_output):
    for i, line in enumerate(ocr_output):
        line = line.strip()
        match = re.search(r'FILIA[ÇC]AO\s*(.*)', line)
        if match:
            filiation_current = match.group(1).strip()
            if not filiation_current and i + 1 < len(ocr_output):
                filiation_current = ocr_output[i+1].strip()
                filiation_next = ocr_output[i+2].strip() if i + \
                    2 < len(ocr_output) else ""
            else:
                filiation_next = ocr_output[i+1].strip() if i + \
                    1 < len(ocr_output) else ""

            if " E " in filiation_current or " E " in filiation_next or \
               " E" in filiation_current or " E" in filiation_next:
                return f"{filiation_current} {filiation_next}".strip()
            else:
                return filiation_current

    return None


def extract_dt_nasc(ocr_output):

    dt_nasc_patterns = [
        # Formato com barras (12/34/5678)
        re.compile(r'\b([0-9]{2}/[0-9]{2}/[0-9]{4})\b'),
        # Formato com hífens (12-34-5678)
        re.compile(r'\b([0-9]{2}-[0-9]{2}-[0-9]{4})\b'),
        # Formato com pontos (12.34.5678)
        re.compile(r'\b([0-9]{2}\.[0-9]{2}\.[0-9]{4})\b')
    ]

    for pattern in dt_nasc_patterns:
        for line in ocr_output[4:]:  # Limita a iteração às 4 primeiras linhas
            line = line.strip()
            match = pattern.search(line)
            if match:
                return match.group(1)  # Retorna o primeiro RG encontrado

    return None  # Retorna None se nenhum RG for encontrado


def extract_num_rg_novo(ocr_output):
    rg_patterns = [
        re.compile(r'REGISTRO GERAL[\s:]*([0-9]{1,2}\.?[0-9]{3}\.?[0-9]{3})'),
        re.compile(r'\b([0-9]{2,3}\.[0-9]{3}\.[0-9]{3}-[0-9]{1,2})\b'),
        re.compile(r'\b([0-9]{1,2}\.[0-9]{3}\.[0-9]{3})\b'),
        re.compile(r'\b([0-9]{1,2}\s[0-9]{3}\s[0-9]{3})\b'),
        re.compile(r'\b([0-9]{3}\.[0-9]{3})\b')
    ]

    for pattern in rg_patterns:
        for line in ocr_output:
            line = line.strip()
            match = pattern.search(line)
            if match:
                return match.group(1)

    return None


def extract_cpf(ocr_output):
    cpf_patterns = [
        re.compile(r'CPF[\s:]*([0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2})'),
        re.compile(r'\b([0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2})\b')
    ]

    for i, line in enumerate(ocr_output):
        line = line.strip()
        for pattern in cpf_patterns:
            match = pattern.search(line)
            if match:
                cpf = match.group(1)
                # Busca o RG nas linhas abaixo do CPF
                rg = extract_num_rg_novo(ocr_output[i+1:])
                if rg:
                    return cpf, rg
                else:
                    return cpf, None

    return None, None


def extract_dt_expedicao(ocr_output):

    dt_expedicao_patterns = [
        # Formato com barras (12/34/5678)
        re.compile(r'\b([0-9]{2}/[0-9]{2}/[0-9]{4})\b'),
        # Formato com hífens (12-34-5678)
        re.compile(r'\b([0-9]{2}-[0-9]{2}-[0-9]{4})\b'),
        # Formato com pontos (12.34.5678)
        re.compile(r'\b([0-9]{2}\.[0-9]{2}\.[0-9]{4})\b')
    ]

    for pattern in dt_expedicao_patterns:
        for line in ocr_output:  
            line = line.strip()
            match = pattern.search(line)
            if match:
                return match.group(1)  # Retorna o primeiro RG encontrado

    return None  # Retorna None se nenhum RG for encontrado


# Pipeline para extrair informações do RG novo
def extract_rg_novo(model, path_frente, path_verso, limiar_conf=0.5, show_image=False, debug=False):
    try:
        result, meta_data_f = pipeline_ocr(model, path_frente, limiar_conf,
                              show_image=show_image, debug=debug)
        nome = extract_name(result)
        filiacao = extract_filiation(result)
        dt_nasc = extract_dt_nasc(result)
    except FileNotFoundError as e:
        print(
            f"Imagem não fornecida ou não encontrada no caminho fornecido: {path_frente}")
        nome = None
        filiacao = None
        dt_nasc = None

    try:
        result_v, meta_data_v = pipeline_ocr(
            model, path_verso, limiar_conf, show_image=show_image, debug=debug)
        cpf, rg = extract_cpf(result_v)
        if rg is None:
            rg = extract_num_rg_novo(result_v)
        dt_expedicao = extract_dt_expedicao(result_v)
    except FileNotFoundError as e:
        print(
            f"Imagem não fornecida ou não encontrada no caminho fornecido: {path_verso}")
        cpf = None
        rg = None
        dt_expedicao = None

    dados = {
        "RG": rg,
        "Data de Expedicao": dt_expedicao,
        "Nome": nome,
        "Filiacao": filiacao,
        "CPF": cpf,
        "Data de Nascimento": dt_nasc
    }
    return dados, meta_data_f, meta_data_v
