# integracao_ocr

## main.py
O arquivo main.py varre as pastas cartao, cnh, rg_t1(rg novo com frente e verso) e rg_t2(rg antigo apenas com o verso) verificando se existe algun arquivo dentro delas e caso aja, chama a função responsável por realizar o ocr do tipo de documento de acordo com a pasta onde ele se encontra.


## app.py
Realiza a mesma tarefa da main.py, entretanto, em uma interface streamlit.

Comando para executar o arquivo app.py: streamlit run app.py
