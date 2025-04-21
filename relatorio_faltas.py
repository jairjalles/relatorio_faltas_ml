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
    st.image("logotipo.png", width=200)
with col_title:
    st.markdown("""
        <div style='display: flex; align-items: center; height: 200px;'>
            <h1 style='color: white; margin: 0;'>📊 Dashboard de Faltas - Mercado Livre</h1>
        </div>
    """, unsafe_allow_html=True)

# ===== CAMINHO DA PLANILHA =====
st.markdown("📁 **Caminho da planilha sincronizada no OneDrive:**")
col_path, col_btn = st.columns([5, 1])
caminho = col_path.text_input("📂 Caminho do arquivo:", value="planilhas/FALTAS MERCADO LIVRE 2025.xlsx")
atualizar = col_btn.button("🔄 Atualizar")

planilha_online = caminho.startswith("https://") or caminho.startswith("http://")

# ===== LOGICA DE CARREGAMENTO =====
df_faltas = pd.DataFrame()
df_base = pd.DataFrame()
df_long = pd.DataFrame()
df_historico = pd.DataFrame()
erro_carregamento = ""

if not planilha_online:
    if not os.path.exists(caminho):
        st.error("Caminho inválido. Verifique se a planilha está sincronizada no OneDrive.")
    else:
        try:
            df_raw = pd.read_excel(caminho, sheet_name="Geral", header=[4, 5], dtype=str)
            df_detalhado = pd.read_excel(caminho, sheet_name="Geral", header=5, dtype=str)
            df_base = pd.read_excel(caminho, sheet_name="Base Criados", header=2, dtype=str)

            contas, faltas = [], []
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
            erro_carregamento = f"Erro ao processar a planilha: {e}"

else:
    st.warning("Este é um link online. O botão de edição estará disponível, mas a leitura da planilha será ignorada.")

# ===== BOTÃO PARA EDITAR SE FOR LINK =====
if planilha_online:
    st.link_button("📝 Editar manualmente no SharePoint", caminho)

# ===== ERRO DE LEITURA =====
if erro_carregamento:
    st.error(erro_carregamento)

# ===== HISTÓRICO DE FALTAS =====
historico_path = "historico_faltas.csv"
hoje = datetime.today().strftime('%Y-%m-%d')
if not df_faltas.empty:
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

# ===== ABAS =====
tabs = st.tabs(["📊 Dashboard Geral", "📈 Histórico", "🚨 Alertas", "📥 Exportações", "📂 Base Criados", "⚙️ Configurações", "👤 Perfil"])

# ===== ABA: DASHBOARD GERAL =====
with tabs[0]:
    if not df_faltas.empty:
        st.markdown("""
            <style>
            .card-container { display: flex; gap: 30px; margin-top: 10px; margin-bottom: 30px; }
            .card {
                background-color: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 16px;
                padding: 25px;
                min-width: 200px;
                text-align: center;
            }
            .card h2 { font-size: 18px; margin-bottom: 8px; color: white; }
            .card p { font-size: 24px; font-weight: bold; color: white; }
            </style>
            <div class="card-container">
                <div class="card"><h2>Total de Faltas</h2><p>{}</p></div>
                <div class="card"><h2>Contas Ativas</h2><p>{}</p></div>
            </div>
        """.format(df_faltas["Faltas"].sum(), df_faltas["Conta_Exibicao"].nunique()), unsafe_allow_html=True)

        st.markdown("### 📊 Gráfico de Faltas por Conta")
        graf_contas = px.bar(df_faltas.sort_values("Faltas", ascending=False), x="Faltas", y="Conta_Exibicao", orientation="h")
        st.plotly_chart(graf_contas, use_container_width=True)

        st.markdown("### 📄 Visão Geral de Faltas")
        st.dataframe(df_faltas.sort_values("Faltas", ascending=False), use_container_width=True)

        st.markdown("### 📋 Tabela Geral de Dados por SKU e Conta")
        tabela_detalhada = df_long[["SKU", "Titulo", "Estoque", "Marca", "Conta_Exibicao", "Faltas"]]
        tabela_detalhada = tabela_detalhada.rename(columns={"Conta_Exibicao": "Conta"})
        st.dataframe(tabela_detalhada.sort_values("Faltas", ascending=False), use_container_width=True, height=400)

# ===== ABA: HISTÓRICO =====
with tabs[1]:
    st.markdown("## 📈 Evolução das Faltas")
    if not df_historico.empty:
        col1, col2 = st.columns(2)
        data_inicio = col1.date_input("📅 Data Inicial", value=datetime.today())
        data_fim = col2.date_input("📅 Data Final", value=datetime.today())
        df_periodo = df_historico[(df_historico["Data"] >= pd.to_datetime(data_inicio)) & (df_historico["Data"] <= pd.to_datetime(data_fim))]
        graf_hist = px.line(df_periodo, x="Data", y="Total Faltas", markers=True)
        st.plotly_chart(graf_hist, use_container_width=True)

# ===== RESTANTE DAS ABAS PODEM SER INCLUÍDAS AQUI CONFORME SUA VERSÃO ANTERIOR

st.divider()
st.markdown("📌 Desenvolvido por Jair Jales com base na ideia de Ronald Costa")
