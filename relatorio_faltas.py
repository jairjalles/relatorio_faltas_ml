import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os
from datetime import datetime

st.set_page_config(layout="wide", page_title="Dashboard de Faltas")

# ===== FUNDO PERSONALIZADO COM CAMADA EXTRA =====
def set_background(image_file):
    with open(image_file, "rb") as f:
        img64 = base64.b64encode(f.read()).decode()
    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{img64}");
            background-size: cover;
            background-attachment: fixed;
        }}

        .container-bg {{
            background-color: rgba(0, 0, 0, 0.45);
            padding: 25px;
            border-radius: 20px;
            margin-bottom: 20px;
        }}

        h1, h2, h3, h4, h5, h6, label, p, div {{
            color: white !important;
        }}

        .stButton>button {{
            background: linear-gradient(90deg,#235C9B,#012C4E)!important;
            color:white!important;
            font-weight:bold!important;
            border-radius:12px!important;
        }}

        .block-container {{
            padding-top: 2rem;
        }}
        </style>
    """, unsafe_allow_html=True)

set_background("fundo_interface.jpeg")

# ===== LOGO + TITULO COM CAMADA =====
with st.container():
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        st.image("logo.png", width=200)
    with col_title:
        st.markdown("""
        <div class='container-bg'>
            <h1 style='margin: 0;'>📊 Dashboard de Faltas - Mercado Livre</h1>
        </div>
        """, unsafe_allow_html=True)

# ===== CAMINHO DO ARQUIVO COM CAMADA =====
st.markdown("""
    <div class='container-bg'>
        <p>📁 <strong>Caminho da planilha sincronizada no OneDrive ou GitHub (pasta planilhas/)</strong>:</p>
    </div>
""", unsafe_allow_html=True)

col_path, col_btn = st.columns([5, 1])
caminho = col_path.text_input("", value="planilhas/FALTAS MERCADO LIVRE 2025.xlsx")
atualizar = col_btn.button("🔄 Atualizar")

if not os.path.exists(caminho):
    st.error("Caminho inválido. Verifique se a planilha está sincronizada no OneDrive.")
    st.stop()

# Carregamento e processamento da planilha
try:
    df_raw = pd.read_excel(caminho, sheet_name="Geral", header=[4, 5], dtype=str)
    df_detalhado = pd.read_excel(caminho, sheet_name="Geral", header=5, dtype=str)
    df_base = pd.read_excel(caminho, sheet_name="Base Criados", header=2, dtype=str)

    contas = []
    faltas = []
    for col in df_raw.columns[4:]:
        valor, nome = col
        if isinstance(nome, str) and isinstance(valor, (int, float, str)) and str(valor).isdigit():
            nome_limpo = str(nome).split('.')[0].strip().upper()
            contas.append(nome_limpo)
            faltas.append(int(valor))
    df_faltas = pd.DataFrame({"Conta_Exibicao": contas, "Faltas": faltas})
    df_faltas = df_faltas.drop_duplicates(subset="Conta_Exibicao", keep="first")

    colunas_validas = df_detalhado.columns[4:]
    df_long = df_detalhado.melt(id_vars=["SKU", "Estoque", "Marca", "Titulo"],
                                 value_vars=colunas_validas,
                                 var_name="Conta", value_name="Check")
    df_long["Conta_Exibicao"] = df_long["Conta"].str.split(".").str[0].str.upper().str.strip()
    df_long["Faltas"] = df_long["Check"].fillna("0").apply(lambda x: 1 if str(x).strip() == "0" else 0)
except Exception as e:
    st.error(f"Erro ao processar a planilha: {e}")
    st.stop()

# A partir daqui, seguirá com as abas, gráficos, filtros, e animações visuais como na versão anterior
# Basta colar o restante do código (das abas e gráficos) abaixo deste bloco
