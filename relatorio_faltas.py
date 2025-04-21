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
    st.error("Caminho inválido. Verifique se a planilha está sincronizada no OneDrive ou GitHub.")
    st.stop()

# ===== LEITURA DOS DADOS =====
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

# ===== USUÁRIO LOCAL DETECTADO =====
usuario_local = getpass.getuser()

# ===== INTERFACE: DADOS GERAIS COM CARDS =====
st.markdown("""
    <style>
    .card-metric {{
        background: linear-gradient(to right, rgba(255,255,255,0.05), rgba(255,255,255,0.03));
        padding: 25px 40px;
        border-radius: 20px;
        font-size: 24px;
        margin-bottom: 25px;
    }}
    </style>
    <div class='card-metric'>
        <div style='font-size: 28px;'>📌 <b>Total de Faltas:</b> {df_faltas['Faltas'].sum()}</div>
        <div style='font-size: 26px;'>📁 <b>Contas Ativas:</b> {df_faltas['Conta_Exibicao'].nunique()}</div>
    </div>
""", unsafe_allow_html=True)

# ===== GRAFICO DE FALTAS POR CONTA =====
st.markdown("""
    <h2>📊 Gráfico de Faltas por Conta</h2>
    <p><b>Contas com maior número de faltas</b></p>
""", unsafe_allow_html=True)

fig = px.bar(df_faltas.sort_values("Faltas", ascending=False),
             x="Faltas", y="Conta_Exibicao", orientation="h",
             labels={"Faltas": "Quantidade de Faltas", "Conta_Exibicao": "Conta"},
             color_discrete_sequence=["#5390d9"])
fig.update_layout(hoverlabel=dict(bgcolor="#333", font_size=13, font_family="Arial"))
fig.update_traces(marker=dict(line=dict(width=0.5, color='white')))
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
