# Arquivo: dashboard_faltas_final.py
# Autor: Jair Jales - Versão Profissional Enxuta e Corrigida

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

# ===== CSS GLOBAL (fundo + caixas translúcidas + botões + abas) =====
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
    /* Botões */
    .stButton > button {{
        background: linear-gradient(90deg,#235C9B,#012C4E) !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 12px !important;
        transition: all 0.3s ease;
    }}
    .stButton > button:hover {{
        background: linear-gradient(90deg,#3D8BFF,#235C9B) !important;
        transform: scale(1.05);
        box-shadow: 0 0 12px #50BFFF;
    }}
    /* Abas (aumentadas) */
    .stTabs [data-baseweb="tab"] {{
        font-size: 20px !important;
        padding: 16px 32px !important;
        font-weight: bold !important;
        color: white !important;
        border-radius: 10px 10px 0 0 !important;
        background-color: rgba(255,255,255,0.06) !important;
        transition: all 0.3s ease;
    }}
    .stTabs [aria-selected="true"] {{
        background-color: rgba(255,255,255,0.25) !important;
        border-bottom: 4px solid #50BFFF !important;
        transform: scale(1.05);
    }}
    .stTabs [data-baseweb="tab"]:hover {{
        background-color: rgba(255,255,255,0.15) !important;
        cursor: pointer;
        transform: translateY(-2px);
    }}
    /* Cards informativos */
    .custom-card {{
        background-color: rgba(255,255,255,0.07);
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        transition: all 0.3s ease-in-out;
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
        <h1 style='margin:0;'>📊 Dashboard de Faltas - Mercado Livre</h1>
    </div>
    """, unsafe_allow_html=True)

# ===== CAMINHO DA PLANILHA =====
st.markdown("📁 **Caminho da planilha sincronizada:**")
c_path, c_btn = st.columns([5,1])
planilha = c_path.text_input("", "planilhas/FALTAS MERCADO LIVRE 2025.xlsx", key="input_path")
if c_btn.button("🔄 Atualizar", key="btn_refresh"):
    st.experimental_rerun()

if not os.path.isfile(planilha):
    st.error("Caminho inválido. Verifique a localização do arquivo.")
    st.stop()

# ===== LEITURA E TRANSFORMAÇÃO DOS DADOS =====
try:
    df_raw = pd.read_excel(planilha, sheet_name="Geral", header=[4,5], dtype=str)
    df_det = pd.read_excel(planilha, sheet_name="Geral", header=5, dtype=str)
    df_base = pd.read_excel(planilha, sheet_name="Base Criados", header=2, dtype=str)

    contas, faltas = [], []
    for v, n in df_raw.columns[4:]:
        if isinstance(n, str) and str(v).isdigit():
            contas.append(n.split('.')[0].strip().upper())
            faltas.append(int(v))
    df_faltas = pd.DataFrame({
        "Conta_Exibicao": contas,
        "Faltas": faltas
    }).drop_duplicates("Conta_Exibicao")

    cols = df_det.columns[4:]
    df_long = df_det.melt(
        id_vars=["SKU","Estoque","Marca","Titulo"],
        value_vars=cols,
        var_name="Conta", value_name="Check"
    )
    df_long["Conta_Exibicao"] = (
        df_long["Conta"].str.split(".").str[0]
        .str.upper().str.strip()
    )
    df_long["Faltas"] = df_long["Check"].fillna("0")\
        .apply(lambda x: 1 if str(x).strip()=="0" else 0)

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
        df_hist = pd.concat([
            df_hist,
            pd.DataFrame([{"Data":hoje,"Total Faltas":tot_hoje}])
        ], ignore_index=True)
        df_hist.to_csv(hist_path, index=False)
else:
    df_hist = pd.DataFrame([{"Data":hoje,"Total Faltas":tot_hoje}])
    df_hist.to_csv(hist_path, index=False)

df_hist["Data"] = pd.to_datetime(df_hist["Data"])

# ===== PERFIL =====
user = getpass.getuser()

# ===== TABS =====
tabs = st.tabs([
    "📊 Dashboard Geral", "📈 Histórico", "🚨 Alertas",
    "📥 Exportações", "📂 Base Criados", "⚙️ Configurações", "👤 Perfil"
])

# --- TAB 0: Dashboard Geral ---
with tabs[0]:
    if df_long.empty:
        st.warning("Nenhum dado disponível.")
    else:
        tz = pytz.timezone("America/Sao_Paulo")
        now = datetime.now(tz).strftime("%d/%m/%Y %H:%M")

        semana = (datetime.now(tz) - timedelta(days=7)).strftime("%Y-%m-%d")
        prev = df_hist.loc[df_hist["Data"] == semana, "Total Faltas"].sum()
        diff = tot_hoje - prev
        pct = (diff/prev*100) if prev > 0 else 0
        emoji = "🔺" if pct > 0 else "✅"
        msg_sem = f"{emoji} {'Aumento' if pct>0 else 'Redução'} de {abs(pct):.1f}% desde semana passada"

        imp = (
            df_long[df_long["Faltas"]==1]
            .groupby("SKU")["Conta_Exibicao"]
            .count().reset_index(name="Qtd")
            .sort_values("Qtd", ascending=False)
        )
        msg_imp = (
            f"⚠️ SKU {imp.iloc[0]['SKU']} em falta em {imp.iloc[0]['Qtd']} contas"
            if not imp.empty else "✅ Nenhum SKU crítico hoje"
        )

        skus_hj = df_long[df_long["Faltas"]==1]["SKU"].nunique()
        msg_skus = f"🆕 {skus_hj} SKUs com falta hoje"

        st.markdown(f"""
        <div style='display:flex;gap:20px;flex-wrap:wrap;margin-bottom:30px;'>
          <div class='custom-card'><h3>📦 Total de Faltas</h3><p style='font-size:26px;font-weight:bold;'>{tot_hoje}</p></div>
          <div class='custom-card'><h3>🏬 Contas Ativas</h3><p style='font-size:26px;font-weight:bold;'>{df_faltas["Conta_Exibicao"].nunique()}</p></div>
          <div class='custom-card'><h3>📅 Atualização</h3><p style='font-size:20px;font-weight:bold;'>{now}</p></div>
        </div>
        <div style='margin-bottom:30px;color:white;'>
          <h4>🔔 Alertas:</h4>
          <ul style='font-size:16px;'>
            <li>{msg_sem}</li>
            <li>{msg_imp}</li>
            <li>{msg_skus}</li>
          </ul>
        </div>
        """, unsafe_allow_html=True)

        # filtros lado a lado
        st.markdown(
            "<div style='background-color:rgba(255,255,255,0.07);padding:20px;border-radius:15px;margin-bottom:20px;'>",
            unsafe_allow_html=True
        )
        fcol1, fcol2 = st.columns(2)
        contas_opts = ["Todas"] + sorted(df_long["Conta_Exibicao"].dropna().astype(str).unique().tolist())
        marcas_opts = ["Todas"] + sorted(df_long["Marca"].dropna().astype(str).unique().tolist())
        conta_sel = fcol1.selectbox("📁 Filtrar por Conta", contas_opts, key="filtro_conta")
        marca_sel = fcol2.selectbox("🏷️ Filtrar por Marca", marcas_opts, key="filtro_marca")
        st.markdown("</div>", unsafe_allow_html=True)

        df_fil = df_long.copy()
        if conta_sel != "Todas":
            df_fil = df_fil[df_fil["Conta_Exibicao"] == conta_sel]
        if marca_sel != "Todas":
            df_fil = df_fil[df_fil["Marca"] == marca_sel]

        st.markdown("### 📊 Faltas por Conta")
        g1 = px.bar(
            df_faltas.sort_values("Faltas"),
            x="Faltas", y="Conta_Exibicao", orientation="h",
            color="Faltas", text="Faltas"
        )
        g1.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        g1.update_traces(textposition="outside")
        st.plotly_chart(g1, use_container_width=True, key="g_contas")

        st.markdown("### 🏷️ Top Marcas com mais Faltas")
        top_m = (
            df_fil.groupby("Marca")["Faltas"]
            .sum().reset_index()
            .sort_values("Faltas", ascending=False)
            .head(10)
        )
        g2 = px.bar(
            top_m, x="Faltas", y="Marca", orientation="h",
            color="Faltas", text="Faltas"
        )
        g2.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
        g2.update_traces(textposition="outside")
        st.plotly_chart(g2, use_container_width=True, key="g_marcas")

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
    df_p = df_hist[
        (df_hist["Data"]>=pd.to_datetime(ini)) &
        (df_hist["Data"]<=pd.to_datetime(fim))
    ]
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
    st.download_button("⬇️ Faltas Detalhadas", df_long.to_csv(index=False).encode(), file_name="detalhado.csv", key="e2")
    st.download_button("⬇️ Histórico", df_hist.to_csv(index=False).encode(), file_name="hist.csv", key="e3")

# --- TAB 4: Base Criados ---
with tabs[4]:
    st.markdown("## 📂 Base Criados")
    st.dataframe(df_base, use_container_width=True)
    st.markdown(
        "[🔧 Editar no SharePoint]"
        "(https://topshopbrasil.sharepoint.com/:x:/r/sites/criacao/...)",
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
