import streamlit as st
import pandas as pd
import plotly.express as px
import os
import base64
from datetime import datetime
import getpass

st.set_page_config(layout="wide", page_title="Dashboard de Faltas")

# ====== FUNDO PERSONALIZADO ======
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
        .main-container {{
            background: rgba(255, 255, 255, 0.08);
            padding: 2rem;
            border-radius: 20px;
            backdrop-filter: blur(6px);
            -webkit-backdrop-filter: blur(6px);
            margin-top: 20px;
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
        </style>
    """, unsafe_allow_html=True)

set_background("fundo_interface.jpeg")

# ====== LOGO E TÍTULO ======
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("logo.png", width=200)
with col_title:
    st.markdown("""
        <div style='display: flex; align-items: center; height: 200px;'>
            <h1 style='color: white; margin: 0;'>📊 Dashboard de Faltas - Mercado Livre</h1>
        </div>
    """, unsafe_allow_html=True)

# ====== CAMINHO PLANILHA ======
st.markdown("📁 **Caminho da planilha sincronizada no OneDrive ou GitHub (pasta planilhas/):**")
col_path, col_btn = st.columns([5, 1])
caminho = col_path.text_input("", value="planilhas/FALTAS MERCADO LIVRE 2025.xlsx")
atualizar = col_btn.button("🔄 Atualizar")

if not os.path.exists(caminho):
    st.error("Caminho inválido. Verifique se a planilha está sincronizada no OneDrive.")
    st.stop()

# ====== LEITURA DE DADOS ======
try:
    df_raw = pd.read_excel(caminho, sheet_name="Geral", header=[4, 5], dtype=str)
    df_detalhado = pd.read_excel(caminho, sheet_name="Geral", header=5, dtype=str)
    df_base = pd.read_excel(caminho, sheet_name="Base Criados", header=2, dtype=str)

    contas = []
    faltas = []
    for col in df_raw.columns[4:]:
        valor, nome = col
        if isinstance(nome, str) and str(valor).isdigit():
            nome_limpo = nome.split('.')[0].strip().upper()
            contas.append(nome_limpo)
            faltas.append(int(valor))

    df_faltas = pd.DataFrame({"Conta_Exibicao": contas, "Faltas": faltas}).drop_duplicates("Conta_Exibicao")
    df_detalhado = df_detalhado.fillna("0")

    colunas_validas = df_detalhado.columns[4:]
    df_long = df_detalhado.melt(
        id_vars=["SKU", "Estoque", "Marca", "Titulo"],
        value_vars=colunas_validas,
        var_name="Conta", value_name="Check"
    )
    df_long["Conta_Exibicao"] = df_long["Conta"].str.split(".").str[0].str.upper().str.strip()
    df_long["Faltas"] = df_long["Check"].apply(lambda x: 1 if str(x).strip() == "0" else 0)

except Exception as e:
    st.error(f"Erro ao processar a planilha: {e}")
    st.stop()

# ====== HISTÓRICO LOCAL ======
historico_path = "historico_faltas.csv"
hoje = datetime.today().strftime('%Y-%m-%d')
faltas_atuais = int(df_faltas["Faltas"].sum())

if os.path.exists(historico_path):
    df_historico = pd.read_csv(historico_path)
    if hoje not in df_historico["Data"].values:
        df_historico = pd.concat([
            df_historico,
            pd.DataFrame([{"Data": hoje, "Total Faltas": faltas_atuais}])
        ], ignore_index=True)
        df_historico.to_csv(historico_path, index=False)
else:
    df_historico = pd.DataFrame([{"Data": hoje, "Total Faltas": faltas_atuais}])
    df_historico.to_csv(historico_path, index=False)

df_historico["Data"] = pd.to_datetime(df_historico["Data"])

# ====== INÍCIO DAS ABAS ======
tabs = st.tabs(["📊 Dashboard Geral", "📈 Histórico", "🚨 Alertas", "📥 Exportações", "📂 Base Criados", "⚙️ Configurações", "👤 Perfil"])

with tabs[0]:
    st.markdown('<div class="main-container">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div style='background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px;'>
            <h2>📌 Total de Faltas: <span style='color: #FFDDDD'>{}</span></h2>
        </div>""".format(df_faltas['Faltas'].sum()), unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div style='background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px;'>
            <h2>📂 Contas Ativas: <span style='color: #DDFFDD'>{}</span></h2>
        </div>""".format(df_faltas['Conta_Exibicao'].nunique()), unsafe_allow_html=True)

    st.markdown("### 📊 Gráfico de Faltas por Conta")
    fig = px.bar(
        df_faltas.sort_values("Faltas", ascending=True),
        x="Faltas", y="Conta_Exibicao", orientation="h",
        labels={"Conta_Exibicao": "Conta", "Faltas": "Nº de Faltas"},
        color_discrete_sequence=["#3e8ed0"]*len(df_faltas),
        title="Contas com maior número de faltas"
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='white',
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📄 Visão Geral de Faltas")
    conta_filtro = st.selectbox("📁 Conta", ["Todas"] + sorted(df_long["Conta_Exibicao"].unique()))
    marca_filtro = st.selectbox("🏷️ Marca", ["Todas"] + sorted(df_long["Marca"].unique()))

    df_filtrado = df_long.copy()
    if conta_filtro != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Conta_Exibicao"] == conta_filtro]
    if marca_filtro != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Marca"] == marca_filtro]

    st.dataframe(df_filtrado[["SKU", "Titulo", "Estoque", "Marca", "Conta_Exibicao", "Faltas"]])
    st.markdown('</div>', unsafe_allow_html=True)
