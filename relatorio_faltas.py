# Arquivo: dashboard_faltas_final.py
# Autor: Jair Jales – Versão Profissional Enxuta e Corrigida

import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import os
import getpass
from datetime import datetime, timedelta
import pytz

st.set_page_config(
    layout="wide",
    page_title="Dashboard de Faltas",
    initial_sidebar_state="expanded"
)

# ===== CSS GLOBAL (fundo, caixas translúcidas, botões e abas animados) =====
def load_css(image_path):
    img_b64 = base64.b64encode(open(image_path, "rb").read()).decode()
    st.markdown(f"""
    <style>
    /* Fundo da app */
    .stApp {{
        background-image: url("data:image/png;base64,{img_b64}");
        background-size: cover;
        background-attachment: fixed;
    }}
    /* Container principal */
    section.main > div {{
        background-color: rgba(255,255,255,0.10) !important;
        border-radius: 20px;
        padding: 30px;
        margin-top: 10px;
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
        transition: all 0.4s ease-in-out;
    }}
    /* Texto branco */
    h1,h2,h3,h4,h5,h6,p,label,span {{
        color: white !important;
    }}
    /* Botões gerais */
    .stButton > button {{
        background: linear-gradient(90deg,#235C9B,#012C4E) !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    .stButton > button:hover {{
        transform: scale(1.05);
        box-shadow: 0 0 12px #50BFFF;
    }}
    /* Abas animadas */
    .stTabs [data-baseweb="tab"] {{
        font-size: 20px !important;
        padding: 16px 32px !important;
        font-weight: bold !important;
        color: white !important;
        border-radius: 10px 10px 0 0 !important;
        background-color: rgba(255,255,255,0.06) !important;
        transition: transform 0.3s ease, background-color 0.3s ease;
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        transform: translateY(-2px);
        background-color: rgba(255,255,255,0.15) !important;
    }}
    .stTabs [aria-selected="true"] {{
        transform: scale(1.05);
        background-color: rgba(255,255,255,0.25) !important;
        border-bottom: 4px solid #50BFFF !important;
    }}
    /* Cards informativos */
    .custom-card {{
        background-color: rgba(255,255,255,0.07);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }}
    .custom-card:hover {{
        transform: scale(1.03);
        box-shadow: 0 6px 20px rgba(80,191,255,0.4);
    }}
    </style>
    """, unsafe_allow_html=True)

load_css("fundo_interface.jpeg")

# ===== LOGO + TÍTULO =====
col1, col2 = st.columns([1,5])
with col1:
    st.image("logo.png", width=200)
with col2:
    st.markdown("""
    <div style='display:flex;align-items:center;height:200px;'>
        <h1 style='margin:0;'>📊 Dashboard de Faltas – Mercado Livre</h1>
    </div>
    """, unsafe_allow_html=True)

# ===== CAMINHO DA PLANILHA EDITÁVEL =====
st.markdown("📁 **Caminho da planilha sincronizada:**")
planilha = st.text_input(
    "",
    value=st.session_state.get("input_path", "planilhas/FALTAS MERCADO LIVRE 2025.xlsx"),
    key="input_path"
)
# o Streamlit re-executa automaticamente ao editar este campo
if not os.path.isfile(planilha):
    st.error("Caminho inválido. Verifique a localização do arquivo.")
    st.stop()
    
# ===== LEITURA E TRANSFORMAÇÃO DOS DADOS =====
try:
    # leitura da aba Geral
    df_raw = pd.read_excel(planilha, sheet_name="Geral", header=[4,5], dtype=str)
    df_det = pd.read_excel(planilha, sheet_name="Geral", header=5, dtype=str)

    # leitura da Base Criados (com dois níveis de header: data e nome da conta)
    df_base = pd.read_excel(planilha, sheet_name="Base Criados", header=[0, 1], dtype=str)

    # transforma MultiIndex em nome único tipo: "Walker Tape"
    df_base.columns = [str(c[1]).strip().upper() for c in df_base.columns]

    # cria DataFrame long com: Conta_Exibicao e SKU
    df_base_long = df_base.melt(ignore_index=False, var_name="Conta_Exibicao", value_name="SKU")
    df_base_long = df_base_long[["Conta_Exibicao", "SKU"]].dropna()

    # Faltas por conta
    # LEITURA DA LINHA 5 COM AS FALTAS POR CONTA (valores usados na planilha Excel)
    df_raw = pd.read_excel(planilha, sheet_name="Geral", header=[4,5], dtype=str)

    contas, faltas = [], []
    def ler_faltas_linha5(path):
    df_raw = pd.read_excel(path, sheet_name="Geral", header=None)
    linha_faltas = df_raw.iloc[4, 4:]  # linha 5 (index 4), colunas E em diante
    cabecalhos = df_raw.iloc[5, 4:]    # linha 6 (index 5), nomes das contas
    contas, faltas = [], []
    for val, conta in zip(linha_faltas, cabecalhos):
        if pd.notna(val) and str(val).isdigit():
            contas.append(str(conta).strip().upper())
            faltas.append(int(val))
    return pd.DataFrame({"Conta_Exibicao": contas, "Faltas": faltas})
    
    # Detalhado (long)
    cols = df_det.columns[4:]
    df_long = df_det.melt(
        id_vars=["SKU", "Estoque", "Marca", "Titulo"],
        value_vars=cols,
        var_name="Conta", value_name="Check"
    )
    df_long["Conta_Exibicao"] = (
        df_long["Conta"].str.split(".").str[0].str.upper().str.strip()
    )

    # remove os que já foram criados
    df_long = (
        df_long
        .merge(df_base_long.drop_duplicates(), on=["SKU", "Conta_Exibicao"], how="left", indicator="_base_")
        .query("_base_ == 'left_only'")
        .drop(columns="_base_")
    )

    # aplica regra de falta
    df_long["Faltas"] = df_long["Check"].fillna("0").apply(lambda x: 1 if str(x).strip() == "0" else 0)

except Exception as e:
    st.error(f"Erro ao processar a planilha: {e}")
    st.stop()
# ===== HISTÓRICO =====
hist_path = "historico_faltas.csv"
hoje = datetime.today().strftime("%Y-%m-%d")
tot_hoje = int(df_faltas["Faltas"].sum())

if os.path.exists(hist_path):
    df_hist = pd.read_csv(hist_path)
    if hoje not in df_hist["Data"].values:
        df_hist = pd.concat([df_hist, pd.DataFrame([{"Data":hoje,"Total Faltas":tot_hoje}])], ignore_index=True)
        df_hist.to_csv(hist_path, index=False)
else:
    df_hist = pd.DataFrame([{"Data":hoje,"Total Faltas":tot_hoje}])
    df_hist.to_csv(hist_path, index=False)

df_hist["Data"] = pd.to_datetime(df_hist["Data"])

# ===== PERFIL =====
user = getpass.getuser()

# ===== ABAS =====
tabs = st.tabs([
    "📊 Dashboard Geral", "📈 Histórico", "🚨 Alertas",
    "📥 Exportações", "📂 Base Criados", "⚙️ Configurações", "👤 Perfil"
])

# --- TAB 0: Dashboard Geral ---
with tabs[0]:
    if df_long.empty:
        st.warning("Nenhum dado disponível.")
    else:
        # ==== CARDS ====
        tz = pytz.timezone("America/Sao_Paulo")
        now = datetime.now(tz).strftime("%d/%m/%Y %H:%M")
        st.markdown(f"""
        <div style='display:flex;gap:20px;flex-wrap:wrap;margin-bottom:30px;'>
          <div class='custom-card'>
            <h3>📦 Total de Faltas</h3>
            <p style='font-size:26px;font-weight:bold;'>{tot_hoje}</p>
          </div>
          <div class='custom-card'>
            <h3>🏬 Contas Ativas</h3>
            <p style='font-size:26px;font-weight:bold;'>{df_faltas["Conta_Exibicao"].nunique()}</p>
          </div>
          <div class='custom-card'>
            <h3>📅 Atualização</h3>
            <p style='font-size:20px;font-weight:bold;'>{now}</p>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # ==== FILTROS (conta + marca) ====
        st.markdown(
            "<div style='background-color:rgba(255,255,255,0.07);"
            "padding:20px;border-radius:15px;margin-bottom:20px;'>",
            unsafe_allow_html=True
        )
        f1, f2 = st.columns(2)
        contas_opts = ["Todas"] + sorted(df_long["Conta_Exibicao"].dropna().astype(str).unique().tolist())
        marcas_opts = ["Todas"] + sorted(df_long["Marca"].dropna().astype(str).unique().tolist())
        conta_sel = f1.selectbox("📁 Filtrar por Conta", contas_opts, key="filtro_conta")
        marca_sel = f2.selectbox("🏷️ Filtrar por Marca", marcas_opts, key="filtro_marca")
        st.markdown("</div>", unsafe_allow_html=True)

        # aplica filtros
        df_fil = df_long.copy()
        if conta_sel != "Todas":
            df_fil = df_fil[df_fil["Conta_Exibicao"] == conta_sel]
        if marca_sel != "Todas":
            df_fil = df_fil[df_fil["Marca"] == marca_sel]

        # ==== GRÁFICO: Faltas por Conta ====
        st.markdown("### 📊 Faltas por Conta")
        g1 = px.bar(
            df_fil.groupby("Conta_Exibicao")["Faltas"].sum()
                  .reset_index().sort_values("Faltas"),
            x="Faltas", y="Conta_Exibicao", orientation="h",
            color="Faltas", text="Faltas"
        )
        g1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        g1.update_traces(textposition="outside")
        st.plotly_chart(g1, use_container_width=True, key="g_contas")

        # ==== GRÁFICO: Top Marcas ====
        st.markdown("### 🏷️ Top Marcas com mais Faltas")
        top_m = (
            df_fil.groupby("Marca")["Faltas"].sum()
                  .reset_index().sort_values("Faltas", ascending=False)
                  .head(10)
        )
        g2 = px.bar(top_m, x="Faltas", y="Marca", orientation="h",
                    color="Faltas", text="Faltas")
        g2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        g2.update_traces(textposition="outside")
        st.plotly_chart(g2, use_container_width=True, key="g_marcas")

        # ==== TABELA DETALHADA ====
        st.markdown("### 📋 Tabela Geral de Dados")
        st.dataframe(
            df_fil[["SKU","Titulo","Estoque","Marca","Conta_Exibicao","Faltas"]],
            height=400, use_container_width=True
        )

# --- TAB 1: Histórico ---
with tabs[1]:
    st.markdown("## 📈 Evolução das Faltas")
    d1, d2 = st.columns(2)
    ini = d1.date_input("De", datetime.today(), key="h_ini")
    fim = d2.date_input("Até", datetime.today(), key="h_fim")
    df_p = df_hist[(df_hist["Data"] >= pd.to_datetime(ini)) & (df_hist["Data"] <= pd.to_datetime(fim))]
    gh = px.line(df_p, x="Data", y="Total Faltas", markers=True)
    st.plotly_chart(gh, use_container_width=True, key="g_hist")

# --- TAB 2: Alertas ---
with tabs[2]:
    st.markdown("## 🚨 Alertas Inteligentes")
    st.subheader("🔴 Contas com 50+ faltas")
    st.dataframe(df_faltas.query("Faltas>=50"), use_container_width=True)
    st.subheader("🟠 SKUs em 5+ contas")
    sa = (
        df_long[df_long["Faltas"]==1]
        .groupby("SKU")["Conta_Exibicao"]
        .count().reset_index(name="Contas")
        .query("Contas>=5")
    )
    st.dataframe(sa, use_container_width=True)

# --- TAB 3: Exportações ---
with tabs[3]:
    st.markdown("## 📥 Exportações")
    st.download_button("⬇️ Faltas por Conta", df_faltas.to_csv(index=False).encode(), file_name="faltas.csv", key="e1")
    st.download_button("⬇️ Detalhado por SKU", df_long.to_csv(index=False).encode(), file_name="detalhado.csv", key="e2")
    st.download_button("⬇️ Histórico", df_hist.to_csv(index=False).encode(), file_name="historico.csv", key="e3")

# --- TAB 4: Base Criados ---
with tabs[4]:
    st.markdown("## 📂 Base Criados")
    st.dataframe(df_base, use_container_width=True)
    st.markdown(
        "[🔧 Editar no SharePoint](https://topshopbrasil.sharepoint.com/...)",
        unsafe_allow_html=True
    )

# --- TAB 5: Configurações ---
with tabs[5]:
    st.markdown("## ⚙️ Configurações")
    sku_search = st.text_input("🔍 Buscar SKU", key="cfg_sku")
    if sku_search:
        st.dataframe(
            df_long[df_long["SKU"].str.contains(sku_search, case=False, na=False)],
            use_container_width=True
        )
    if st.button("🗑️ Limpar histórico", key="cfg_clear"):
        if os.path.exists(hist_path):
            os.remove(hist_path)
            st.success("Histórico removido.")

# --- TAB 6: Perfil ---
with tabs[6]:
    st.markdown("## 👤 Perfil do Usuário")
    st.success(f"Usuário: **{user}**")
    st.markdown("**Função:** Desenvolvedor & Automatizador de Processos")

st.divider()
st.markdown("📌 Desenvolvido por Jair Jales com base na ideia de Ronald Costa")
