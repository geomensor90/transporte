import streamlit as st
import re

def extrair_os(texto):
    padrao_data = r"\d{2}/\d{2}/\d{4}"
    padrao_os = r"OS-\d{3}\.\d{3}/\d{4}"

    datas = re.findall(padrao_data, texto)
    dados = {}
    partes = re.split(padrao_data, texto)[1:]

    for i, data in enumerate(datas):
        oss = re.findall(padrao_os, partes[i]) if i < len(partes) else []
        if oss:
            dados[data] = oss

    return dados

st.title("Extração de OSs")
texto_input = st.text_area("Cole o texto aqui:", height=200)

if st.button("Processar Texto"):
    if texto_input:
        dados_os = extrair_os(texto_input)
        if dados_os:
            resultado = ""
            for data, oss in dados_os.items():
                os_str = " e ".join(oss)
                resultado += f"{os_str} de **{data}**; "
            st.markdown(resultado)
        else:
            st.write("Nenhuma OS encontrada no texto.")
    else:
        st.write("Por favor, cole o texto no campo acima.")
