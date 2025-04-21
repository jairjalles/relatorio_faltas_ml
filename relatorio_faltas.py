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
        .block-container {{
            padding-top: 1rem;
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
st.markdown("📁 **Caminho da planilha sincronizada no OneDrive:**")
col_path, col_btn = st.columns([5, 1])
caminho = col_path.text_input("", value="C:/Users/Jair Jales/OneDrive - Top Shop/BASE/FALTAS MERCADO LIVRE 2025 - Copia.xlsx")
atualizar = col_btn.button("🔄 Atualizar")

if not os.path.exists(caminho):
    st.error("Caminho inválido. Verifique se a planilha está sincronizada no OneDrive.")
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

# ===== HISTÓRICO =====
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

df_historico["Data"] = pd.to_datetime(df_historico["Data"])

# ===== USUÁRIO LOCAL DETECTADO =====
usuario_local = getpass.getuser()

# ===== ABAS =====
tabs = st.tabs(["📊 Dashboard Geral", "📈 Histórico", "🚨 Alertas", "📥 Exportações", "📂 Base Criados", "⚙️ Configurações", "👤 Perfil"])

with tabs[0]:
    st.markdown("## 📌 Visão Geral")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("📦 Total de Faltas", faltas_atuais)
    with col2:
        st.metric("📁 Contas Ativas", df_faltas["Conta_Exibicao"].nunique())

    st.markdown("### 📊 Filtros")
    colf1, colf2 = st.columns(2)
    conta_filtro = colf1.selectbox("📁 Conta", ["Todas"] + sorted(df_long["Conta_Exibicao"].dropna().unique().tolist()))
    marca_filtro = colf2.selectbox("🏷️ Marca", ["Todas"] + sorted(df_long["Marca"].dropna().unique().tolist()))

    df_filtrado = df_long.copy()
    if conta_filtro != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Conta_Exibicao"] == conta_filtro]
    if marca_filtro != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Marca"] == marca_filtro]

    st.markdown("### 📈 Gráfico de Faltas por Conta")
    graf_contas = px.bar(df_faltas.sort_values("Faltas", ascending=False),
                         x="Faltas", y="Conta_Exibicao", orientation="h",
                         color="Faltas", color_continuous_scale="Blues",
                         template="plotly_white")
    graf_contas.update_layout(height=450)
    st.plotly_chart(graf_contas, use_container_width=True)

    st.markdown("### 🏆 Top Marcas com mais Faltas")
    top_marcas = df_filtrado.groupby("Marca")["Faltas"].sum().reset_index().sort_values("Faltas", ascending=False).head(10)
    graf_marcas = px.bar(top_marcas, x="Faltas", y="Marca", orientation="h",
                         color="Faltas", color_continuous_scale="Purples",
                         template="plotly_white")
    st.plotly_chart(graf_marcas, use_container_width=True)

    st.markdown("### 📋 Tabela Geral de Dados")
    tabela_final = df_filtrado[["SKU", "Titulo", "Estoque", "Marca", "Conta_Exibicao", "Faltas"]]
    st.dataframe(tabela_final, use_container_width=True, height=400)

with tabs[1]:
    st.markdown("## 📈 Histórico de Faltas")
    df_hist = df_historico.copy()
    col1, col2 = st.columns(2)
    data_inicio = col1.date_input("📅 Data Inicial", value=datetime.today())
    data_fim = col2.date_input("📅 Data Final", value=datetime.today())
    df_filtrado = df_hist[(df_hist["Data"] >= pd.to_datetime(data_inicio)) & (df_hist["Data"] <= pd.to_datetime(data_fim))]
    graf_hist = px.line(df_filtrado, x="Data", y="Total Faltas", markers=True, template="plotly_white")
    st.plotly_chart(graf_hist, use_container_width=True)

with tabs[2]:
    st.markdown("## 🚨 Alertas")
    st.subheader("🔴 Contas com 50+ Faltas")
    contas_alerta = df_faltas[df_faltas["Faltas"] >= 50]
    st.dataframe(contas_alerta)

    st.subheader("🟠 SKUs com falta em 5+ contas")
    skus_alerta = df_long[df_long["Faltas"] == 1].groupby("SKU")["Conta_Exibicao"].count().reset_index(name="Contas com Falta")
    st.dataframe(skus_alerta[skus_alerta["Contas com Falta"] >= 5])

with tabs[3]:
    st.markdown("## 📥 Exportar Dados")
    st.download_button("⬇️ Faltas por Conta", df_faltas.to_csv(index=False).encode("utf-8"), file_name="faltas_por_conta.csv")
    st.download_button("⬇️ Detalhado por SKU", df_long.to_csv(index=False).encode("utf-8"), file_name="faltas_detalhadas.csv")
    st.download_button("⬇️ Histórico de Faltas", df_historico.to_csv(index=False).encode("utf-8"), file_name="historico_faltas.csv")

with tabs[4]:
    st.markdown("## 📂 Base Criados")
    st.dataframe(df_base, use_container_width=True)

with tabs[5]:
    st.markdown("## ⚙️ Configurações")
    sku = st.text_input("🔍 Buscar SKU específico")
    if sku:
        resultado = df_long[df_long["SKU"].str.contains(sku, case=False, na=False)]
        st.dataframe(resultado)

    if st.button("🗑️ Limpar Histórico"):
        if os.path.exists(historico_path):
            os.remove(historico_path)
            st.success("Histórico resetado!")

with tabs[6]:
    st.markdown("## 👤 Perfil")
    st.success(f"Usuário atual: **{usuario_local}**")
    st.markdown("**Função:** Desenvolvedor & Automatizador de Processos")

st.divider()
st.markdown("📌 Desenvolvido por Jair Jales com base na ideia de Ronald Costa")
