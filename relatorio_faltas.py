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

# ===== FUNDO TRANSPARENTE GLOBAL =====
def apply_global_overlay():
    st.markdown("""
        <style>
        .stApp::before {
            content: "";
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.05);
            z-index: -1;
        }
        </style>
    """, unsafe_allow_html=True)

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
        }}
        </style>
    """, unsafe_allow_html=True)

# Aplicar fundos
apply_global_overlay()
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

# ===== LEITURA DAS PLANILHAS =====
caminho = "planilhas/FALTAS MERCADO LIVRE 2025 - Copia.xlsx"

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

# ===== ABAS PRINCIPAIS COM FILTROS E GRÁFICOS ADICIONAIS =====
tabs = st.tabs(["📊 Dashboard Geral", "📈 Histórico", "🚨 Alertas", "📥 Exportações", "📂 Base Criados", "⚙️ Configurações", "👤 Perfil"])

with tabs[0]:
    col1, col2 = st.columns(2)
    with col1:
        conta_filtro = st.selectbox("📁 Conta", ["Todas"] + sorted(df_long["Conta_Exibicao"].unique()))
    with col2:
        marca_filtro = st.selectbox("🏷️ Marca", ["Todas"] + sorted(df_long["Marca"].unique()))

    dados_filtrados = df_long.copy()
    if conta_filtro != "Todas":
        dados_filtrados = dados_filtrados[dados_filtrados["Conta_Exibicao"] == conta_filtro]
    if marca_filtro != "Todas":
        dados_filtrados = dados_filtrados[dados_filtrados["Marca"] == marca_filtro]

    st.markdown("""
        <style>
        .custom-cards {{ display: flex; gap: 30px; margin-top: 10px; margin-bottom: 30px; }}
        .custom-card {{ background-color: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.2);
            border-radius: 16px; padding: 25px; min-width: 200px; text-align: center; }}
        .custom-card h2 {{ font-size: 18px; margin-bottom: 8px; color: white; }}
        .custom-card p {{ font-size: 24px; font-weight: bold; color: white; }}
        </style>
        <div class="custom-cards">
            <div class="custom-card"><h2>📦 Total de Faltas</h2><p>{df_faltas['Faltas'].sum()}</p></div>
            <div class="custom-card"><h2>📁 Contas Ativas</h2><p>{df_faltas['Conta_Exibicao'].nunique()}</p></div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 📊 Gráfico de Faltas por Conta")
    graf_contas = px.bar(df_faltas.sort_values("Faltas", ascending=False), x="Faltas", y="Conta_Exibicao", orientation="h",
                         hover_data={"Faltas": True, "Conta_Exibicao": True}, labels={"Faltas": "🔴 Faltas", "Conta_Exibicao": "📁 Conta"})
    graf_contas.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
    st.plotly_chart(graf_contas, use_container_width=True)

    st.markdown("### 🏆 Marcas com mais Faltas")
    top_marcas = dados_filtrados.groupby("Marca")["Faltas"].sum().reset_index().sort_values("Faltas", ascending=False).head(10)
    graf_marcas = px.bar(top_marcas, x="Faltas", y="Marca", orientation="h")
    graf_marcas.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white")
    st.plotly_chart(graf_marcas, use_container_width=True)

    st.markdown("### 📋 Tabela Geral Detalhada")
    tabela = dados_filtrados[["SKU", "Titulo", "Marca", "Estoque", "Conta_Exibicao", "Faltas"]]
    st.dataframe(tabela.sort_values("Faltas", ascending=False), use_container_width=True, height=400)

# Créditos
st.markdown("""
---
📌 Desenvolvido por **Jair Jales** com base na ideia de Ronald Costa
""")
