# Arquivo: dashboard_faltas_final.py
# Autor: Jair Jales

import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os
import getpass
from datetime import datetime

st.set_page_config(layout="wide", page_title="Dashboard de Faltas")

# ===== FUNDO PERSONALIZADO =====
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
        h1,h2,h3,h4,h5,h6, label, p, div {{
            color: white !important;
        }}
        .stButton>button {{
            background: linear-gradient(90deg,#235C9B,#012C4E)!important;
            color:white!important; font-weight:bold!important;
            border-radius:12px!important;
            transition: all 0.3s ease-in-out;
        }}
        .stButton>button:hover {{
            transform: scale(1.05);
        }}
        .glass-card {{
            background: rgba(255, 255, 255, 0.07);
            border-radius: 20px;
            padding: 25px;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            animation: fadeIn 1s ease-in-out;
            margin-bottom: 20px;
        }}
        @keyframes fadeIn {{
            0% {{ opacity: 0; transform: translateY(20px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}
        </style>
    """, unsafe_allow_html=True)

set_background("fundo_interface.jpeg")

# ===== LOGO + TITULO =====
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("logo.png", width=200)
with col_title:
    st.markdown("""
        <div style='display: flex; align-items: center; height: 200px;'>
            <h1 style='color: white; margin: 0;'>📊 Dashboard de Faltas - Mercado Livre</h1>
        </div>
    """, unsafe_allow_html=True)

# ===== CAMINHO DO ARQUIVO (GitHub ou Local) =====
st.markdown("📁 **Caminho da planilha sincronizada no OneDrive ou GitHub (pasta planilhas/):**")
col_path, col_btn = st.columns([5, 1])
caminho = col_path.text_input("", value="planilhas/FALTAS MERCADO LIVRE 2025.xlsx")
atualizar = col_btn.button("🔄 Atualizar")

if not os.path.exists(caminho):
    st.warning("Este é um link online ou o caminho não existe localmente. O botão de edição pode estar disponível, mas a leitura da planilha será ignorada.")
    st.stop()

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
    df_long = df_detalhado.melt(id_vars=["SKU", "Estoque", "Marca", "Titulo"], value_vars=colunas_validas,
                                var_name="Conta", value_name="Check")
    df_long["Conta_Exibicao"] = df_long["Conta"].str.split(".").str[0].str.upper().str.strip()
    df_long["Faltas"] = df_long["Check"].fillna("0").apply(lambda x: 1 if str(x).strip() == "0" else 0)
except Exception as e:
    st.error(f"Erro ao processar a planilha: {e}")
    st.stop()

usuario_local = getpass.getuser()
st.markdown("""
<div class="glass-card">
    <h2>📌 Total de Faltas: {}</h2>
    <h2>📁 Contas Ativas: {}</h2>
</div>
""".format(df_faltas['Faltas'].sum(), df_faltas['Conta_Exibicao'].nunique()), unsafe_allow_html=True)

st.markdown("## 📊 Gráfico de Faltas por Conta")
graf = px.bar(df_faltas.sort_values("Faltas", ascending=True), 
              x="Faltas", y="Conta_Exibicao", orientation="h",
              title="Contas com maior número de faltas",
              color_discrete_sequence=["#4287f5"])
graf.update_layout(
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(color='white'),
    hoverlabel=dict(bgcolor="white", font_size=14, font_family="Arial")
)
st.plotly_chart(graf, use_container_width=True)

st.markdown("""
---
👤 Usuário atual: **{}**
""".format(usuario_local))
