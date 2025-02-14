import os
import streamlit as st
from config_run_model import load_ocr_model
from extract_information_card import ocr_card
from extract_information_rg import extract_rg_novo, extract_rg_antigo
from extract_information_cnh import extract_cnh
from PIL import Image

def process_images(directory, model, process_function, **kwargs):
    if any(os.scandir(directory)):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            st.image(Image.open(file_path), caption=f"Imagem: {filename}", use_column_width=True)
            
            st.write(f"**Processando arquivo:** {filename} ...")
            data = process_function(model, file_path, **kwargs)
            st.json(data)

def main():
    st.title("Ordens de Serviço: 46, 47, 48 e 49")
    st.write("Clique no botão abaixo para iniciar o processamento das imagens.")
    
    if st.button("Executar Modelos de Detecção e Reconhecimento de Texto"):
        with st.spinner("Carregando modelo..."):
            model = load_ocr_model()

        # Diretórios com os arquivos de imagem
        cartao = "./cartao"
        cnh = "./cnh"
        rg_t1 = "./rg_t1"
        rg_t2 = "./rg_t2"
        
        st.subheader("Processando Cartões")
        process_images(cartao, model, ocr_card, show_image=False)

        st.subheader("Processando CNHs")
        process_images(cnh, model, extract_cnh, limiar_conf=0, show_image=False)
        
        st.subheader("Processando RG Tipo 1")
        if any(os.scandir(rg_t1)):
            files = os.listdir(rg_t1)
            for i in range(0, len(files), 2):
                file1 = os.path.join(rg_t1, files[i])
                file2 = os.path.join(rg_t1, files[i+1]) if i+1 < len(files) else None
                
                st.image(Image.open(file1), caption=f"Imagem: {files[i]}", use_column_width=True)
                if file2:
                    st.image(Image.open(file2), caption=f"Imagem: {files[i+1]}", use_column_width=True)
                    st.write(f"**Processando arquivos:** {files[i]} e {files[i+1]} ...")
                else:
                    st.write(f"**Processando arquivo:** {files[i]} ...")
                
                data = extract_rg_novo(model, file1, file2, limiar_conf=0, show_image=False)
                st.json(data)
        
        st.subheader("Processando RG Tipo 2")
        process_images(rg_t2, model, extract_rg_antigo, limiar_conf=0, show_image=False)
        
        st.success("Processamento concluído!")

if __name__ == "__main__":
    main()
