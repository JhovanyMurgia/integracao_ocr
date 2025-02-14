import os


from config_run_model import load_ocr_model
from extract_information_card import ocr_card
from extract_information_rg import extract_rg_novo, extract_rg_antigo
from extract_information_cnh import extract_cnh

if __name__ == "__main__":
    # Carregar o modelo
    model = load_ocr_model()
    

    # Diretórios com os arquivos de imagem
    cartao = "./cartao"
    cnh = "./cnh"
    rg_t1 = "./rg_t1"
    rg_t2 = "./rg_t2"
                  
    if any(os.scandir(cartao)):
        # Iterar sobre todos os arquivos no diretório
        for filename in os.listdir(cartao):
            file_path = os.path.join(cartao, filename)

            print(f"Processando arquivo: {filename} ...")

            # Processar cada arquivo e obter o dicionário de dados
            data = ocr_card(model, file_path, show_image=True) 

            print(data)
    
    if any(os.scandir(cnh)):
        # Iterar sobre todos os arquivos no diretório
        for filename in os.listdir(cnh):
            file_path = os.path.join(cnh, filename)

            print(f"Processando arquivo: {filename} ...")

            # Processar cada arquivo e obter o dicionário de dados
            data = extract_cnh(model, file_path, limiar_conf=0,show_image=True)

            print(data)

    if any(os.scandir(rg_t1)):
         # Obter a lista de arquivos no diretório
        files = os.listdir(rg_t1)

        # Iterar sobre os arquivos de dois em dois
        for i in range(0, len(files), 2):
            file1 = os.path.join(rg_t1, files[i])
            file2 = os.path.join(rg_t1, files[i+1]) if i+1 < len(files) else None

            print(f"Processando arquivos: {files[i]} e {files[i+1] if file2 else 'N/A'} ...")

            # Processar cada arquivo e obter o dicionário de dados
            data = extract_rg_novo(model, file1, file2, limiar_conf=0,show_image=True)

            print(data)

    if any(os.scandir(rg_t2)):
        # Iterar sobre todos os arquivos no diretório
        for filename in os.listdir(rg_t2):
            file_path = os.path.join(rg_t2, filename)

            print(f"Processando arquivo: {filename} ...")

            # Processar cada arquivo e obter o dicionário de dados
            data = data = extract_rg_antigo(model, file_path, limiar_conf=0,show_image=True)

            print(data)
 