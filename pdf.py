import streamlit as st
import pdfplumber
import pandas as pd
import re
from datetime import datetime

st.set_page_config(
    page_title="Extrator de OSs e RHBTs",
    layout="wide"
)

st.subheader("🧾 Indenização de Transporte")


hoje = datetime.now()

meses = [
    "JANEIRO",
    "FEVEREIRO",
    "MARÇO",
    "ABRIL",
    "MAIO",
    "JUNHO",
    "JULHO",
    "AGOSTO",
    "SETEMBRO",
    "OUTUBRO",
    "NOVEMBRO",
    "DEZEMBRO"
]

incluir_relatorios = st.checkbox(
        "Incluir relatórios"
    )

col1, col2, col3 = st.columns([1, 1, 4])

with col1:
    ano = st.number_input(
        "Ano",
        min_value=2020,
        max_value=2100,
        value=hoje.year
    )

with col2:
    mes = st.selectbox(
        "Mês",
        meses,
        index=hoje.month - 1
    )
    
if "pares_extraidos" not in st.session_state:
    st.session_state.pares_extraidos = []

def obter_dia_semana(data_str):
    dias_semana = [
        "segunda-feira",
        "terça-feira",
        "quarta-feira",
        "quinta-feira",
        "sexta-feira",
        "sábado",
        "domingo"
    ]

    try:
        return dias_semana[
            datetime.strptime(
                data_str,
                "%d/%m/%Y"
            ).weekday()
        ]
    except ValueError:
        return ""
    
arquivo_pdf = st.file_uploader(
    "📂 Selecione o PDF",
    type=["pdf"]
)

if st.button("🚀 Processar PDF"):

    if arquivo_pdf is None:
        st.warning("⚠️ Selecione um PDF.")
        st.stop()

    dados = []

    try:

        with pdfplumber.open(arquivo_pdf) as pdf:

            for pagina in pdf.pages:

                tabelas = pagina.extract_tables(
                    table_settings={
                        "vertical_strategy": "lines",
                        "horizontal_strategy": "lines",
                        "snap_tolerance": 3,
                        "join_tolerance": 3,
                        "edge_min_length": 3,
                        "intersection_tolerance": 3
                    }
                )

                if not tabelas:
                    continue

                for tabela in tabelas:

                    for linha in tabela:

                        if not linha:
                            continue

                        linha_limpa = []

                        for celula in linha:

                            if celula is None:
                                linha_limpa.append("")
                            else:
                                linha_limpa.append(
                                    str(celula)
                                    .replace("\n", " ")
                                    .strip()
                                )

                        if any(campo != "" for campo in linha_limpa):
                            dados.append(linha_limpa)

        if not dados:
            st.error("Nenhum dado encontrado no PDF.")
            st.stop()

        # --------------------------------------------------
        # MONTA DATAFRAME
        # --------------------------------------------------

        max_colunas = max(len(linha) for linha in dados)

        dados_padronizados = []

        for linha in dados:
            linha += [""] * (max_colunas - len(linha))
            dados_padronizados.append(linha)

        df = pd.DataFrame(dados_padronizados)

        # Mantém apenas as 3 primeiras colunas
        df = df.iloc[:, :3]

        while df.shape[1] < 3:
            df[df.shape[1]] = ""

        df.columns = ["Data", "OS", "Descricao"]

        # --------------------------------------------------
        # PREENCHE DATAS
        # --------------------------------------------------

        padrao_data = re.compile(r"^\d{2}/\d{2}/\d{4}$")

        ultima_data = ""

        for i in df.index:

            valor = str(df.at[i, "Data"]).strip()

            if padrao_data.match(valor):
                ultima_data = valor

            elif valor == "":
                if ultima_data:
                    df.at[i, "Data"] = ultima_data

            else:
                df.at[i, "Data"] = ""

        # Remove linhas sem data
        df = df[df["Data"] != ""]

        # Remove linhas sem OS
        df = df[
            df["OS"]
            .fillna("")
            .astype(str)
            .str.strip()
            != ""
        ]
        df.reset_index(drop=True, inplace=True)
        df["DiaSemana"] = df["Data"].apply(
            obter_dia_semana
        )
        # --------------------------------------------------
        # EXTRAI RHBT DA DESCRIÇÃO
        # --------------------------------------------------

        df["Descricao"] = df["Descricao"].apply(
            lambda x: re.search(
                r"Ação fiscal:\s*([^,]+)",
                str(x)
            ).group(1)
            if re.search(
                r"Ação fiscal:\s*([^,]+)",
                str(x)
            )
            else ""
        )

        # Remove linhas sem RHBT
        df = df[df["Descricao"] != ""]

        df.reset_index(drop=True, inplace=True)

        # --------------------------------------------------
        # MONTA PARES
        # --------------------------------------------------

        pares_extraidos = []

        for _, linha in df.iterrows():

            os_formatada = (
                f"{linha['OS']} de {linha['Data']}"
            )

            rhbt = linha["Descricao"]

            pares_extraidos.append(
                (os_formatada, rhbt, linha["DiaSemana"])
            )

        st.session_state.pares_extraidos = pares_extraidos

        #st.success(
        #    f"{len(pares_extraidos)} registros encontrados."
        #)
        
        # Exibição da tabela extraída
        #st.dataframe(
        #    df,
        #    use_container_width=True
        #)

    except Exception as erro:
        st.error(f"Erro ao processar PDF: {erro}")

# --------------------------------------------------
# CHECKBOXES
# --------------------------------------------------

if st.session_state.pares_extraidos:

    st.write("**✅ Marque as OSs**")

    selecionadas = []
    itens_completos = []

    for i, (os_val, rhbt_val, dia_semana) in enumerate(
        st.session_state.pares_extraidos
    ):

        label = f"{os_val} - {rhbt_val} - {dia_semana}"

        if st.checkbox(label, key=f"chk_{i}"):
            selecionadas.append(os_val)

            # Condiciona a inclusão do relatório com base no checkbox do topo
            if incluir_relatorios:
                itens_completos.append(f"{os_val} (Ação Fiscal: {rhbt_val})")
            else:
                itens_completos.append(os_val)

    if selecionadas:

        # Mostra um contador nativo e destacado no topo
        st.metric(label="Quantidade de OSs selecionadas", value=len(selecionadas))

        resultado = "; ".join(selecionadas)
        
        resultado_completo = "; ".join(
            itens_completos
        )

        st.markdown("### OSs Selecionadas")

        st.text_area(
            "OSs:",
            value=resultado_completo,
            height=120
        )

        texto_sei = f"Declaro, ciente das penalidades previstas no art. 299 do Código Penal, que para fins de recebimento de Indenização de Transporte, nos termos do art. 106 da Lei Complementar nº 840, de 23 de dezembro de 2011 e o Decreto nº 43.138, de 24 de março de 2022, conforme autorização contida nas Ordem(ns) de Serviço(s) nº(s) {resultado_completo} que realizei os serviços externos no mês de {mes}, do ano de {ano}, em sua integralidade (10/10), no(s) local(is) constante(s) da(s) Ordem(ns) de Serviço supramencionada(s), utilizando meio próprio de locomoção, estando ciente das penalidades previstas no art. 299 do Código Penal e sanções constantes da Lei Complementar nº 840, de 23 de dezembro de 2011."

        st.markdown("### 📋 Texto para colar no processo SEI")

        st.text_area(
            "Texto para SEI:",
            value=texto_sei,
            height=200
        )
