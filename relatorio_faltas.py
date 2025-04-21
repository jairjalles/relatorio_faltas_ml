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
    if os.path.exists(image_file):
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
    if os.path.exists("logo.png"):
        st.image("logo.png", width=200)
with col_title:
    st.markdown("""
        <div style='display: flex; align-items: center; height: 200px;'>
            <h1 style='color: white; margin: 0;'>📊 Dashboard de Faltas - Mercado Livre</h1>
        </div>
    """, unsafe_allow_html=True)

# ===== CAMINHO DO ARQUIVO =====
st.markdown("📁 **Informe o caminho da planilha ou link do SharePoint:**")
col_path, col_btn = st.columns([5, 1])
caminho = col_path.text_input("", value="planilhas/FALTAS MERCADO LIVRE 2025 - Copia.xlsx")
atualizar = col_btn.button("🔄 Atualizar")

# ===== VARIAVEIS DE CONTROLE =====
link_detectado = caminho.startswith("http")
leitura_sucesso = False

if not link_detectado and os.path.exists(caminho):
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

        leitura_sucesso = True
    except Exception as e:
        st.error(f"Erro ao processar a planilha: {e}")

elif link_detectado:
    st.info("🔗 Link do SharePoint detectado. O botão de edição será exibido na aba Base Criados.")
else:
    st.error("Caminho inválido. Verifique se a planilha existe ou informe um link válido.")

# ===== HISTÓRICO =====
if leitura_sucesso:
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

# ===== ABAS COMPLETAS =====
tabs = st.tabs(["📊 Dashboard Geral", "📈 Histórico", "🚨 Alertas", "📥 Exportações", "📂 Base Criados", "⚙️ Configurações", "👤 Perfil"])

with tabs[0]:
    if leitura_sucesso:
        st.metric("📦 Total de Faltas", int(df_faltas["Faltas"].sum()))
        st.metric("📁 Contas Ativas", df_faltas["Conta_Exibicao"].nunique())
        st.plotly_chart(px.bar(df_faltas.sort_values("Faltas", ascending=False), x="Faltas", y="Conta_Exibicao", orientation="h"), use_container_width=True)

        top_marcas = df_long.groupby("Marca")["Faltas"].sum().reset_index().sort_values("Faltas", ascending=False).head(10)
        st.plotly_chart(px.bar(top_marcas, x="Faltas", y="Marca", orientation="h"), use_container_width=True)

        top_contas = df_long[df_long["Faltas"] == 1].groupby("Conta_Exibicao")["SKU"].count().reset_index(name="SKUs Zerados")
        top_contas = top_contas.sort_values("SKUs Zerados", ascending=False).head(10)
        st.plotly_chart(px.bar(top_contas, x="SKUs Zerados", y="Conta_Exibicao", orientation="h"), use_container_width=True)

        st.dataframe(df_faltas.sort_values("Faltas", ascending=False))

        tabela_detalhada = df_long[["SKU", "Titulo", "Estoque", "Marca", "Conta_Exibicao", "Faltas"]]
        st.dataframe(tabela_detalhada.rename(columns={"Conta_Exibicao": "Conta"}).sort_values("Faltas", ascending=False), use_container_width=True, height=450)

with tabs[1]:
    if leitura_sucesso:
        col1, col2 = st.columns(2)
        data_inicio = col1.date_input("📅 Data Inicial", value=datetime.today())
        data_fim = col2.date_input("📅 Data Final", value=datetime.today())
        df_periodo = df_historico[(df_historico["Data"] >= pd.to_datetime(data_inicio)) & (df_historico["Data"] <= pd.to_datetime(data_fim))]
        st.plotly_chart(px.line(df_periodo, x="Data", y="Total Faltas", markers=True), use_container_width=True)

with tabs[2]:
    if leitura_sucesso:
        st.subheader("🔴 Contas com 50+ Faltas")
        st.dataframe(df_faltas[df_faltas["Faltas"] >= 50])

        st.subheader("🟠 SKUs com falta em 5+ contas")
        skus_alerta = df_long[df_long["Faltas"] == 1].groupby("SKU")["Conta_Exibicao"].count().reset_index(name="Contas com Falta")
        st.dataframe(skus_alerta[skus_alerta["Contas with Falta"] >= 5])

with tabs[3]:
    if leitura_sucesso:
        st.download_button("⬇️ Exportar Faltas por Conta", df_faltas.to_csv(index=False).encode("utf-8"), file_name="faltas_por_conta.csv")
        st.download_button("⬇️ Exportar Detalhado por SKU", df_long.to_csv(index=False).encode("utf-8"), file_name="faltas_detalhadas.csv")
        st.download_button("⬇️ Exportar Histórico de Faltas", df_historico.to_csv(index=False).encode("utf-8"), file_name="historico_faltas.csv")

with tabs[4]:
    if leitura_sucesso:
        st.dataframe(df_base, use_container_width=True)
    if link_detectado:
        st.link_button("🔧 Editar manualmente no SharePoint", caminho)

with tabs[5]:
    if leitura_sucesso:
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
    st.success(f"Usuário atual: **{usuario_local}**")
    st.markdown("**Função:** Desenvolvedor & Automatizador de Processos")

st.divider()
st.markdown("📌 Desenvolvido por Jair Jales com base na ideia de Ronald Costa")
