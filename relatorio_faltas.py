# Arquivo: dashboard_faltas_final.py
# Autor: Jair Jales + Ajustes modernos e responsivos

import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os
import getpass
from datetime import datetime

st.set_page_config(layout="wide", page_title="Dashboard de Faltas")

# ===== FUNDO PERSONALIZADO COM CAMADA BRANCA TRANSPARENTE =====
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
        .main-overlay {{
            background: rgba(255,255,255,0.3);
            padding: 30px;
            border-radius: 15px;
        }}
        h1,h2,h3,h4,h5,h6, label, p, div {{
            color: white !important;
        }}
        .stButton>button {{
            background: linear-gradient(90deg,#235C9B,#012C4E)!important;
            color:white!important; font-weight:bold!important;
            border-radius:12px!important;
        }}
        </style>
    """, unsafe_allow_html=True)

set_background("fundo_interface.jpeg")

# ===== INTERFACE DO CABEÇALHO =====
with st.container():
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        st.image("logo.png", width=200)
    with col_title:
        st.markdown("""
            <div style='display: flex; align-items: center; height: 200px;'>
                <h1 style='color: white; margin: 0;'>📊 Dashboard de Faltas - Mercado Livre</h1>
            </div>
        """, unsafe_allow_html=True)

# ===== CAMINHO PLANILHA =====
st.markdown("📁 **Caminho da planilha sincronizada no OneDrive ou pasta do GitHub (planilhas/):**")
col_path, col_btn = st.columns([5, 1])
caminho = col_path.text_input("", value="planilhas/FALTAS MERCADO LIVRE 2025 - Copia.xlsx")
atualizar = col_btn.button("🔄 Atualizar")

if not os.path.exists(caminho):
    st.error("Caminho inválido. Verifique se o arquivo existe no repositório local.")
    st.stop()

# ===== LEITURA DE DADOS =====
try:
    df_raw = pd.read_excel(caminho, sheet_name="Geral", header=[4, 5], dtype=str)
    df_detalhado = pd.read_excel(caminho, sheet_name="Geral", header=5, dtype=str)
    df_base = pd.read_excel(caminho, sheet_name="Base Criados", header=2, dtype=str)

    contas = []
    faltas = []
    for col in df_raw.columns[4:]:
        valor, nome = col
        if isinstance(nome, str) and str(valor).isdigit():
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

# ===== HISTÓRICO AUTOMÁTICO =====
historico_path = "historico_faltas.csv"
hoje = datetime.today().strftime('%Y-%m-%d')
faltas_atuais = int(df_faltas["Faltas"].sum())

if os.path.exists(historico_path):
    df_historico = pd.read_csv(historico_path)
    if hoje not in df_historico["Data"].values:
        df_historico = pd.concat([df_historico, pd.DataFrame([{"Data": hoje, "Total Faltas": faltas_atuais}])], ignore_index=True)
        df_historico.to_csv(historico_path, index=False)
else:
    df_historico = pd.DataFrame([{"Data": hoje, "Total Faltas": faltas_atuais}])
    df_historico.to_csv(historico_path, index=False)

# ===== PERFIL DO USUÁRIO DETECTADO =====
usuario_local = getpass.getuser()

# ===== ABAS PRINCIPAIS (continua na próxima parte) =====
