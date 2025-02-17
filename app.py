import os
import streamlit as st
import pandas as pd
import numpy as np
import cv2
from config_run_model import load_ocr_model
from extract_information_card import ocr_card
from extract_information_rg import extract_rg_novo, extract_rg_antigo
from extract_information_cnh import extract_cnh
from PIL import Image


def desenhar_bounding_boxes(uploaded_file, result):
    # Abrir a imagem
    image = Image.open(uploaded_file)

    # Converte para numpy array (caso seja uma imagem PIL)
    image_np = np.array(image)

    annotated_image = image_np.copy()
    h, w, _ = image_np.shape

    for page in result.pages:
        for block in page.blocks:
            for line in block.lines:
                for word in line.words:
                    # Converte as coordenadas do quadrilátero
                    points = np.array(word.geometry)  # Transforma em array NumPy
                    x_coords = points[:, 0]  # Lista de coordenadas X
                    y_coords = points[:, 1]  # Lista de coordenadas Y

                    # Define a bounding box mínima
                    x_min, x_max = int(min(x_coords) * w), int(max(x_coords) * w)
                    y_min, y_max = int(min(y_coords) * h), int(max(y_coords) * h)

                    # Obtém a confiança da palavra detectada
                    confidence = word.confidence  # Confiança do OCR (entre 0 e 1)
                    confidence_text = f"{confidence * 100:.0f}"  # Converte para percentual

                    # Desenha a bounding box (Azul)
                    cv2.rectangle(annotated_image, (x_min, y_min), (x_max, y_max), (255, 0, 0), 1)

                    # Exibe a confiança acima do texto (Fonte menor)
                    cv2.putText(annotated_image, confidence_text, (x_min, y_min - 2),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)  
                    

    annotated_image = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB)

    return annotated_image


def process_images(directory, model, process_function, **kwargs):
    if any(os.scandir(directory)):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)

            st.write(f"**Processando arquivo:** {filename} ...")
            data, meta_data = process_function(model, file_path, **kwargs)

            img_bbox = desenhar_bounding_boxes(file_path, meta_data)

            # Criar colunas para exibir lado a lado
            col1, col2 = st.columns(2)

            with col1:
                st.image(Image.open(file_path), caption="Imagem Original", use_column_width=True)

            with col2:
                st.image(img_bbox, caption="Imagem com campos reconhecidos pela IA", use_column_width=True)

            # Exibir os dados extraídos
            if isinstance(data, dict):
                df = pd.DataFrame(list(data.items()), columns=["Campos no documento", "Resultado identificado"])
                st.table(df)
            else:
                st.write("Erro: Dados não encontrados.")
    else: 
        st.write("Nenhum documento desse tipo encontrado.")

def main():

    #Logo SESA
    col1, col2, col3 = st.columns([2, 1, 2])  
    with col2:
        st.image(Image.open("brasao_vertical_sesa_cor.jpg"), use_column_width=True)
    
    #Titulo da pagina
    st.title("Ordens de Serviço: 46, 47, 48 e 49")
    st.write("Clique no botão abaixo para iniciar o processamento das imagens.")

    #Botão para processar imagens
    if st.button("Executar Modelos de Detecção e Reconhecimento de Texto"):
        with st.spinner("Carregando modelo..."):
            model = load_ocr_model()

        # Diretórios com os arquivos de imagem
        cartao = "./cartao"
        cnh = "./cnh"
        rg_t1 = "./rg_t1"
        rg_t2 = "./rg_t2"

        st.subheader("Processando Cartão SUS")
        process_images(cartao, model, ocr_card)

        st.subheader("Processando CNH")
        process_images(cnh, model, extract_cnh, limiar_conf=0)

        st.subheader("Processando RG")
        if any(os.scandir(rg_t1)):
            files = os.listdir(rg_t1)
            for i in range(0, len(files), 2):
                file1 = os.path.join(rg_t1, files[i])
                file2 = os.path.join(rg_t1, files[i+1]) if i+1 < len(files) else None

                st.write(f"**Processando arquivos:** {files[i]} {' e ' + files[i+1] if file2 else ''} ...")

                data, meta_data_f, meta_data_v = extract_rg_novo(model, file1, file2, limiar_conf=0)

                col1, col2 = st.columns(2)

                with col1:
                    st.image(Image.open(file1), caption=f"Imagem: {files[i]}", use_column_width=True)

                with col2:
                    img_bbox = desenhar_bounding_boxes(file1, meta_data_f)
                    st.image(img_bbox, caption="Imagem com campos reconhecidos pela IA", use_column_width=True)

                if file2:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.image(Image.open(file2), caption=f"Imagem: {files[i+1]}", use_column_width=True)
                    with col2:
                        img_bbox = desenhar_bounding_boxes(file2, meta_data_v)
                        st.image(img_bbox, caption="Imagem com campos reconhecidos pela IA", use_column_width=True)

                if isinstance(data, dict):
                    df = pd.DataFrame(list(data.items()), columns=["Campos no documento", "Resultado identificado"])
                    st.table(df)
                else:
                    st.write("Erro: Dados não encontrados.")

        
        process_images(rg_t2, model, extract_rg_antigo, limiar_conf=0)

        st.success("Processamento concluído!")


if __name__ == "__main__":
    main()
