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

# ===== CAMINHO DO ARQUIVO =====
st.markdown("📁 **Caminho da planilha sincronizada no OneDrive ou GitHub (pasta planilhas/):**")
col_path, col_btn = st.columns([5, 1])
caminho = col_path.text_input("", value="planilhas/FALTAS MERCADO LIVRE 2025.xlsx")
atualizar = col_btn.button("🔄 Atualizar")

if not os.path.exists(caminho):
    st.error("Caminho inválido. Verifique se a planilha está sincronizada corretamente.")
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
    df_faltas = pd.DataFrame({"Conta_Exibicao": contas, "Faltas": faltas}).drop_duplicates("Conta_Exibicao")

    colunas_validas = df_detalhado.columns[4:]
    df_long = df_detalhado.melt(id_vars=["SKU", "Estoque", "Marca", "Titulo"], value_vars=colunas_validas,
                                var_name="Conta", value_name="Check")
    df_long["Conta_Exibicao"] = df_long["Conta"].str.split(".").str[0].str.upper().str.strip()
    df_long["Faltas"] = df_long["Check"].fillna("0").apply(lambda x: 1 if str(x).strip() == "0" else 0)
except Exception as e:
    st.error(f"Erro ao processar a planilha: {e}")
    st.stop()

usuario_local = getpass.getuser()
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

st.markdown("""<style>
.card-container {{display: flex; gap: 30px; margin-top: 10px; margin-bottom: 30px;}}
.card {{background-color: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 16px; padding: 25px; min-width: 200px; text-align: center;}}
.card h2 {{font-size: 18px; margin-bottom: 8px; color: white;}}
.card p {{font-size: 24px; font-weight: bold; color: white;}}
</style>""", unsafe_allow_html=True)

tabs = st.tabs(["📊 Dashboard Geral", "📈 Histórico", "🚨 Alertas", "📥 Exportações", "📂 Base Criados", "⚙️ Configurações", "👤 Perfil"])

with tabs[0]:
    st.markdown(f"""
        <div class="card-container">
            <div class="card">
                <h2>📦 Total de Faltas</h2>
                <p>{df_faltas['Faltas'].sum()}</p>
            </div>
            <div class="card">
                <h2>📁 Contas Ativas</h2>
                <p>{df_faltas['Conta_Exibicao'].nunique()}</p>
            </div>
        </div>""", unsafe_allow_html=True)

    st.markdown("### 📊 Gráfico de Faltas por Conta")
    graf_contas = px.bar(df_faltas.sort_values("Faltas", ascending=False), x="Faltas", y="Conta_Exibicao",
                         orientation="h", title="Contas com maior número de faltas",
                         color_discrete_sequence=["#1f77b4"])
    graf_contas.update_traces(hovertemplate="<b>%{y}</b><br>Faltas: %{x}")
    st.plotly_chart(graf_contas, use_container_width=True)

    st.markdown("### 🏆 Top Marcas com mais Faltas")
    top_marcas = df_long.groupby("Marca")["Faltas"].sum().reset_index().sort_values("Faltas", ascending=False).head(10)
    graf_marcas = px.bar(top_marcas, x="Faltas", y="Marca", orientation="h", title="Top Marcas com mais Faltas",
                         color_discrete_sequence=["#2ca02c"])
    st.plotly_chart(graf_marcas, use_container_width=True)

    st.markdown("### 📌 Contas com mais SKUs zerados")
    top_contas = df_long[df_long["Faltas"] == 1].groupby("Conta_Exibicao")["SKU"].count().reset_index(name="SKUs Zerados")
    top_contas = top_contas.sort_values("SKUs Zerados", ascending=False).head(10)
    graf_zerados = px.bar(top_contas, x="SKUs Zerados", y="Conta_Exibicao", orientation="h", title="Contas com mais SKUs zerados",
                          color_discrete_sequence=["#d62728"])
    st.plotly_chart(graf_zerados, use_container_width=True)

    st.markdown("### 📋 Tabela Geral de Dados")
    tabela_detalhada = df_long[["SKU", "Titulo", "Estoque", "Marca", "Conta_Exibicao", "Faltas"]]
    conta_filtro = st.selectbox("📁 Conta", ["Todas"] + sorted(df_long["Conta_Exibicao"].unique()))
    marca_filtro = st.selectbox("🏷️ Marca", ["Todas"] + sorted(df_long["Marca"].unique()))
    if conta_filtro != "Todas":
        tabela_detalhada = tabela_detalhada[tabela_detalhada["Conta_Exibicao"] == conta_filtro]
    if marca_filtro != "Todas":
        tabela_detalhada = tabela_detalhada[tabela_detalhada["Marca"] == marca_filtro]
    st.dataframe(tabela_detalhada.sort_values("Faltas", ascending=False), use_container_width=True, height=400)

with tabs[1]:
    st.markdown("## 📈 Evolução das Faltas")
    col1, col2 = st.columns(2)
    data_inicio = col1.date_input("📅 Data Inicial", value=datetime.today())
    data_fim = col2.date_input("📅 Data Final", value=datetime.today())
    df_historico["Data"] = pd.to_datetime(df_historico["Data"])
    df_periodo = df_historico[(df_historico["Data"] >= pd.to_datetime(data_inicio)) & (df_historico["Data"] <= pd.to_datetime(data_fim))]
    graf_hist = px.line(df_periodo, x="Data", y="Total Faltas", markers=True)
    st.plotly_chart(graf_hist, use_container_width=True)

with tabs[2]:
    st.markdown("## 🚨 Alertas de Faltas")
    st.subheader("🔴 Contas com 50+ Faltas")
    contas_alerta = df_faltas[df_faltas["Faltas"] >= 50]
    st.dataframe(contas_alerta)

    st.subheader("🟠 SKUs com falta em 5+ contas")
    skus_alerta = df_long[df_long["Faltas"] == 1].groupby("SKU")["Conta_Exibicao"].count().reset_index(name="Contas com Falta")
    st.dataframe(skus_alerta[skus_alerta["Contas com Falta"] >= 5])

with tabs[3]:
    st.markdown("## 📥 Exportar Dados")
    st.download_button("⬇️ Exportar Faltas por Conta", df_faltas.to_csv(index=False).encode("utf-8"), file_name="faltas_por_conta.csv")
    st.download_button("⬇️ Exportar Detalhado por SKU", df_long.to_csv(index=False).encode("utf-8"), file_name="faltas_detalhadas.csv")
    st.download_button("⬇️ Exportar Histórico de Faltas", df_historico.to_csv(index=False).encode("utf-8"), file_name="historico_faltas.csv")

with tabs[4]:
    st.markdown("## 📂 Base Criados")
    st.dataframe(df_base, use_container_width=True)

with tabs[5]:
    st.markdown("## ⚙️ Configurações Avançadas")
    sku = st.text_input("🔍 Buscar SKU específico")
    if sku:
        resultado = df_long[df_long["SKU"].str.contains(sku, case=False, na=False)]
        st.dataframe(resultado)

    uploaded_file = st.file_uploader("📤 Upload manual da planilha (.xlsx)", type="xlsx")
    if uploaded_file:
        df_uploaded = pd.read_excel(uploaded_file)
        st.dataframe(df_uploaded.head())

    if st.button("🗑️ Limpar histórico local"):
        if os.path.exists(historico_path):
            os.remove(historico_path)
            st.success("Histórico deletado com sucesso!")

with tabs[6]:
    st.markdown("## 👤 Perfil do Usuário")
    st.success(f"Usuário atual: **{usuario_local}**")
    st.markdown("**Função:** Desenvolvedor & Automatizador de Processos")

st.divider()
st.markdown("📌 Desenvolvido por Jair Jales com base na ideia de Ronald Costa")
