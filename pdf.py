import streamlit as st
import re
from collections import defaultdict

def extrair_os_agrupadas_por_data(texto):
    padrao_os = r"OS-\d{3}\.\d{3}/\d{4}"
    padrao_data = r"\d{2}/\d{2}/\d{4}"

    oss = list(re.finditer(padrao_os, texto))
    datas = list(re.finditer(padrao_data, texto))

    agrupadas = defaultdict(list)

    for os_match in oss:
        os_texto = os_match.group()
        os_pos = os_match.start()

        data_anterior = ""
        for data_match in reversed(datas):
            if data_match.start() < os_pos:
                data_anterior = data_match.group()
                break

        if data_anterior:
            agrupadas[data_anterior].append(os_texto)

    resultado = []
    for data, os_list in agrupadas.items():
        os_str = " e ".join(os_list)
        resultado.append(f"{os_str} de {data}")

    return resultado

def extrair_pares_os_rhbt_com_data(texto):
    padrao_os = r"OS-\d{3}\.\d{3}/\d{4}"
    padrao_rhbt = r"RHBT-\d{3}\.\d{3}\.\d/\d{4}"
    padrao_data = r"\d{2}/\d{2}/\d{4}"

    oss = list(re.finditer(padrao_os, texto))
    rhbts = list(re.finditer(padrao_rhbt, texto))
    datas = list(re.finditer(padrao_data, texto))

    pares = []

    for i, os_match in enumerate(oss):
        os_texto = os_match.group()
        os_pos = os_match.start()

        # Pega a data anterior
        data_anterior = ""
        for data_match in reversed(datas):
            if data_match.start() < os_pos:
                data_anterior = data_match.group()
                break

        os_formatado = f"{os_texto} de {data_anterior}" if data_anterior else os_texto

        limite_final = len(texto)
        if i + 1 < len(oss):
            limite_final = oss[i + 1].start()

        rhbt_proximo = ""
        for rhbt_match in rhbts:
            if os_match.end() < rhbt_match.start() < limite_final:
                rhbt_proximo = rhbt_match.group()
                break

        if rhbt_proximo:
            pares.append((os_formatado, rhbt_proximo))

    return pares

# --- Interface Streamlit ---
st.title("🧾 Extrator de OSs, Datas e RHBTs")

texto = st.text_area("📄 Cole aqui o texto completo:", height=200)

if "pares_extraidos" not in st.session_state:
    st.session_state.pares_extraidos = []
if "oss_datas_agrupadas" not in st.session_state:
    st.session_state.oss_datas_agrupadas = []

if st.button("🚀 Processar Texto"):
    if texto.strip():
        st.session_state.oss_datas_agrupadas = extrair_os_agrupadas_por_data(texto)
        st.session_state.pares_extraidos = extrair_pares_os_rhbt_com_data(texto)
    else:
        st.warning("⚠️ Cole algum texto antes de processar.")

# --- OSs agrupadas por data ---
if st.session_state.oss_datas_agrupadas:
    os_datas_str = "; ".join(st.session_state.oss_datas_agrupadas)
    st.text_area("📌 OSs com datas:", value=os_datas_str, height=150)

# --- Pares de OS + RHBT com checkbox ---
if st.session_state.pares_extraidos:
    st.markdown("### ✅ Marque os pares desejados:")
    selecionadas = []

    for i, (os_val, rhbt_val) in enumerate(st.session_state.pares_extraidos):
        label = f"{os_val} - {rhbt_val}"
        if st.checkbox(label, key=f"chk_{i}"):
            selecionadas.append(os_val)

    if selecionadas:
        st.markdown(f"<h1 style='text-align: center;'>Total de OSs selecionadas: {len(selecionadas)}</h1>", unsafe_allow_html=True)
        resultado = "; ".join(selecionadas)
        st.markdown("### OSs Selecionadas:")
        st.text_area("OSs:", value=resultado, height=100)
        # Texto para colar no processo SEi com a frase personalizada
        texto_sei = f"Declaro, ciente das penalidades previstas no art. 299 do Código Penal, que para fins de recebimento de Indenização de Transporte, nos termos do art. 106 da Lei Complementar nº 840, de 23 de dezembro de 2011 e o Decreto nº 43.138, de 24 de março de 2022, conforme autorização contida nas Ordem(ns) de Serviço(s) nº(s)  {resultado} que realizei os serviços externos no mês de ABRIL, do ano de 2024, em sua integralidade (10/10) ,no(s) local(is) constante(s) da(s) Ordem(ns) de Serviço supramencionada(s), utilizando meio próprio de locomoção, estando ciente das penalidades previstas no art. 299 do Código Penal e sanções constantes da Lei Complementar nº 840, de 23 de dezembro de 2011."
        st.markdown("### 📋 Texto para colar no processo SEi")
        st.text_area("Texto para SEI:", value=texto_sei, height=100)
