# Arquivo: dashboard_faltas_final.py
# Autor: Jair Jales - Versao Profissional com todas as melhorias e ajustes finais

import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os
import getpass
from datetime import datetime

st.set_page_config(layout="wide", page_title="Dashboard de Faltas", initial_sidebar_state="expanded")

# ===== FUNDO PERSONALIZADO COM CAIXA OPACA =====
def set_background(image_file):
    with open(image_file, "rb") as f:
        img64 = base64.b64encode(f.read()).decode()
    st.markdown(f"""
        <style>
        /* Fundo com imagem */
        .stApp {{
            background-image: url("data:image/png;base64,{img64}");
            background-size: cover;
            background-attachment: fixed;
        }}

        /* Caixa translúcida global envolvendo o conteúdo */
        .block-container {{
            background-color: rgba(255, 255, 255, 0.10);
            border-radius: 20px;
            padding: 30px;
            margin-top: 20px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }}

        /* Textos e títulos em branco */
        h1, h2, h3, h4, h5, h6, p, label, span {{
            color: white !important;
        }}

        /* Botões */
        .stButton > button {{
            background: linear-gradient(90deg,#235C9B,#012C4E)!important;
            color: white!important;
            font-weight: bold!important;
            border-radius: 12px!important;
        }}

        /* Abas grandes e visíveis */
        .stTabs [data-baseweb="tab"] {{
            font-size: 18px;
            padding: 10px 24px;
            color: white !important;
        }}
        </style>
    """, unsafe_allow_html=True)

set_background("fundo_interface.jpeg")

st.markdown("""
    <style>
    section.main > div {{
        background-color: rgba(255, 255, 255, 0.10);
        border-radius: 15px;
        padding: 25px;
        margin-top: 10px;
    }}
    </style>
""", unsafe_allow_html=True)

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
st.markdown("📁 **Caminho da planilha sincronizada:**")
col_path, col_btn = st.columns([5, 1])
caminho = col_path.text_input("planilhas/", value="planilhas/FALTAS MERCADO LIVRE 2025.xlsx")
atualizar = col_btn.button("🔄 Atualizar")

if not os.path.isfile(caminho):
    st.error("Caminho inválido. Verifique se a planilha está na pasta correta.")
    st.stop()

try:
    df_raw = pd.read_excel(caminho, sheet_name="Geral", header=[4, 5], dtype=str)
    df_detalhado = pd.read_excel(caminho, sheet_name="Geral", header=5, dtype=str)
    df_base = pd.read_excel(caminho, sheet_name="Base Criados", header=2, dtype=str)

    contas, faltas = [], []
    for col in df_raw.columns[4:]:
        valor, nome = col
        if isinstance(nome, str) and str(valor).isdigit():
            contas.append(str(nome).split('.')[0].strip().upper())
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

# ===== HISTÓRICO =====
historico_path = "historico_faltas.csv"
hoje = datetime.today().strftime('%Y-%m-%d')
faltas_atuais = df_faltas["Faltas"].sum()

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
    if not df_long.empty and "Conta_Exibicao" in df_long.columns:
        contas_unicas = sorted(df_long["Conta_Exibicao"].dropna().unique())
        conta_filtro = st.selectbox("📁 Filtrar por Conta", ["Todas"] + list(contas_unicas), key="filtro_conta_dashboard")
        df_filtrado = df_long if conta_filtro == "Todas" else df_long[df_long["Conta_Exibicao"] == conta_filtro]

        # ==== CARDS RESUMO ====
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
                <div style='background-color: rgba(255,255,255,0.08); padding: 20px; border-radius: 12px; text-align: center;'>
                    <h3>📦 Total de Faltas</h3>
                    <p style='font-size: 26px; font-weight: bold;'>{int(df_faltas["Faltas"].sum())}</p>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
                <div style='background-color: rgba(255,255,255,0.08); padding: 20px; border-radius: 12px; text-align: center;'>
                    <h3>🏬 Contas Ativas</h3>
                    <p style='font-size: 26px; font-weight: bold;'>{df_faltas["Conta_Exibicao"].nunique()}</p>
                </div>
            """, unsafe_allow_html=True)

        # ==== GRÁFICO 1: Faltas por Conta ====
        st.markdown("### 📊 Faltas por Conta")
        graf_contas = px.bar(df_faltas.sort_values("Faltas", ascending=True), 
                             x="Faltas", y="Conta_Exibicao", orientation="h",
                             color="Faltas", text="Faltas",
                             labels={"Faltas": "Faltas", "Conta_Exibicao": "Conta"})
        graf_contas.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        graf_contas.update_traces(marker_line_width=1, textposition="outside")
        st.plotly_chart(graf_contas, use_container_width=True)

        # ==== GRÁFICO 2: Top Marcas ====
st.markdown("### 🏷️ Top Marcas com mais Faltas")
top_marcas = df_filtrado.groupby("Marca")["Faltas"].sum().reset_index()
top_marcas = top_marcas.sort_values("Faltas", ascending=False).head(10)

graf_marcas = px.bar(
    top_marcas,
    x="Faltas",
    y="Marca",
    orientation="h",
    color="Faltas",
    text="Faltas",
    labels={"Marca": "Marca", "Faltas": "Qtd. Faltas"}
)
graf_marcas.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    hoverlabel=dict(bgcolor="#235C9B", font_size=14, font_color="white")
)
graf_marcas.update_traces(marker_line_width=1, textposition="outside")

st.plotly_chart(graf_marcas, use_container_width=True)

        # ==== TABELA DETALHADA ====
        st.markdown("### 📋 Tabela Geral de Dados")
        st.dataframe(df_filtrado[["SKU", "Titulo", "Estoque", "Marca", "Conta_Exibicao", "Faltas"]],
                     use_container_width=True, height=400)
    else:
        st.warning("Nenhum dado disponível para exibir.")

with tabs[1]:
    st.markdown("## 📈 Evolução das Faltas")
    col1, col2 = st.columns(2)
    data_inicio = col1.date_input("De", value=datetime.today())
    data_fim = col2.date_input("Até", value=datetime.today())
    df_periodo = df_historico[(df_historico["Data"] >= pd.to_datetime(data_inicio)) & (df_historico["Data"] <= pd.to_datetime(data_fim))]
    graf_hist = px.line(df_periodo, x="Data", y="Total Faltas", markers=True)
    st.plotly_chart(graf_hist, use_container_width=True)

with tabs[2]:
    st.markdown("## 🚨 Alertas Inteligentes")
    st.subheader("🔴 Contas com 50+ faltas")
    st.dataframe(df_faltas[df_faltas["Faltas"] >= 50])
    st.subheader("🟠 SKUs com falta em 5+ contas")
    skus_alerta = df_long[df_long["Faltas"] == 1].groupby("SKU")["Conta_Exibicao"].count().reset_index(name="Contas com Falta")
    st.dataframe(skus_alerta[skus_alerta["Contas com Falta"] >= 5])

with tabs[3]:
    st.markdown("## 📥 Exportações")
    st.download_button("⬇️ Faltas por Conta", df_faltas.to_csv(index=False).encode("utf-8"), file_name="faltas_por_conta.csv")
    st.download_button("⬇️ Detalhado por SKU", df_long.to_csv(index=False).encode("utf-8"), file_name="faltas_detalhadas.csv")
    st.download_button("⬇️ Histórico de Faltas", df_historico.to_csv(index=False).encode("utf-8"), file_name="historico_faltas.csv")

with tabs[4]:
    st.markdown("## 📂 Base Criados")
    st.dataframe(df_base, use_container_width=True)
    st.link_button("🔧 Editar manualmente no SharePoint",
        "https://topshopbrasil.sharepoint.com/:x:/r/sites/criacao/_layouts/15/Doc.aspx?"
        "sourcedoc=%7BE87C6408-4F5C-4882-BB8E-5FB2A0845FD6%7D&file=FALTAS%20MERCADO%20LIVRE%202025%20-%20Copia.xlsx&"
        "action=default&mobileredirect=true")

with tabs[5]:
    st.markdown("## ⚙️ Configurações")
    sku = st.text_input("🔍 Buscar SKU específico")
    if sku:
        resultado = df_long[df_long["SKU"].str.contains(sku, case=False, na=False)]
        st.dataframe(resultado)

    st.markdown("### 🔁 Resetar Histórico")
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
