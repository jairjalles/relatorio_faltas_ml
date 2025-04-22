# ====================== INÍCIO DO CÓDIGO ======================
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
def load_css(image_path):
    img_b64 = base64.b64encode(open(image_path, "rb").read()).decode()
    st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{img_b64}");
        background-size: cover;
        background-attachment: fixed;
        font-family: 'Segoe UI', 'Roboto', sans-serif;
    }}

    section.main > div {{
        background-color: rgba(255, 255, 255, 0.12) !important;
        border-radius: 20px;
        padding: 25px;
        margin-top: 10px;
        backdrop-filter: blur(8px);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    }}

    h1,h2,h3,h4,h5,h6,label,span,p {{
        color: white !important;
    }}

    .stButton > button {{
        background: linear-gradient(90deg, #235C9B, #012C4E) !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        border-radius: 10px !important;
        padding: 10px 20px !important;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}

    .stButton > button:hover {{
        transform: scale(1.05);
        box-shadow: 0 0 10px #50BFFF;
    }}

    .stTabs [data-baseweb="tab"] {{
        font-size: 20px !important;
        padding: 30px 40px !important;
        font-weight: bold !important;
        color: white !important;
        border-radius: 10px 10px 0 0 !important;
        background-color: rgba(255, 255, 255, 0.08) !important;
        transition: all 0.3s ease;
    }}

    .stTabs [data-baseweb="tab"]:hover {{
        background-color: rgba(255, 255, 255, 0.15) !important;
        transform: translateY(-2px);
    }}

    .stTabs [aria-selected="true"] {{
        background-color: rgba(255, 255, 255, 0.25) !important;
        border-bottom: 4px solid #50BFFF !important;
        transform: scale(1.03);
    }}

    .custom-card {{
        background-color: rgba(255, 255, 255, 0.07);
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        transition: transform 0.4s ease, box-shadow 0.4s ease;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
        animation: fadeIn 1s ease forwards;
        opacity: 0;
    }}

    .custom-card:hover {{
        transform: scale(1.04);
        box-shadow: 0 6px 20px rgba(80, 191, 255, 0.4);
    }}

    .custom-card h3 {{
        font-size: 20px;
        margin-bottom: 10px;
    }}

    @keyframes fadeIn {{
        0% {{ opacity: 0; transform: translateY(20px); }}
        100% {{ opacity: 1; transform: translateY(0); }}
    }}

    .elemento-emoji::before {{
        content: "📊 ";
        margin-right: 5px;
    }}

    .metric-label {{
        font-weight: 600;
        color: #ffffff;
        font-size: 15px;
    }}

    .dataframe th {{
        background-color: #235C9B !important;
        color: white !important;
    }}

    .dataframe td {{
        background-color: rgba(255, 255, 255, 0.03);
        color: white;
    }}

    .block-container {{
        padding-top: 1rem;
    }}
    </style>
    """, unsafe_allow_html=True)

# 🖼️ Aplica o fundo
load_css("fundo_interface.jpeg")

# 📛 Logo + título principal
col1, col2 = st.columns([1, 5])
with col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=180)
    else:
        st.warning("⚠️ Arquivo logo.png não encontrado.")
with col2:
    st.markdown("""
    <div style='display:flex;align-items:center;height:180px;'>
        <h1 style='margin:0;'>📊 Dashboard de Faltas - Mercado Livre</h1>
    </div>
    """, unsafe_allow_html=True)
    
st.markdown("""
<style>
.caminho-container {
    display: flex;
    align-items: center;
    gap: 15px;
    margin-top: 10px;
}
.caminho-label {
    font-weight: bold;
    font-size: 22px;
    color: white;
}
</style>
<div class='caminho-container'>
    <div class='caminho-label'>📁 Caminho da planilha sincronizada:</div>
    <div style='flex: 1;'>
""", unsafe_allow_html=True)

planilha = st.text_input("", value=st.session_state.get("input_path", "planilhas/FALTAS MERCADO LIVRE 2025.xlsx"), key="input_path")

st.markdown("</div></div>", unsafe_allow_html=True)

if not os.path.isfile(planilha):
    st.error("Caminho inválido. Verifique a localização do arquivo.")
    st.stop()

try:
    df_headered = pd.read_excel(planilha, sheet_name="Geral", header=[4,5], dtype=str)
    contas, faltas = [], []
    for col in df_headered.columns[4:]:
        valor, nome = col
        if str(valor).isdigit() and pd.notna(nome):
            contas.append(str(nome).strip().upper())
            faltas.append(int(valor))
    df_faltas = pd.DataFrame({"Conta_Exibicao": contas, "Faltas": faltas})

    df_det = pd.read_excel(planilha, sheet_name="Geral", header=5, dtype=str)
    df_base = pd.read_excel(planilha, sheet_name="Base Criados", header=[0, 1], dtype=str)
    df_base.columns = [str(c[1]).strip().upper() for c in df_base.columns]
    df_base_long = df_base.melt(ignore_index=False, var_name="Conta_Exibicao", value_name="SKU")
    df_base_long = df_base_long[["Conta_Exibicao", "SKU"]].dropna()

    cols = df_det.columns[4:]
    df_long = df_det.melt(
        id_vars=["SKU", "Estoque", "Marca", "Titulo"],
        value_vars=cols,
        var_name="Conta", value_name="Check"
    )
    df_long["Conta_Exibicao"] = df_long["Conta"].str.split(".").str[0].str.upper().str.strip()
    df_long = df_long.merge(df_base_long.drop_duplicates(), on=["SKU", "Conta_Exibicao"], how="left", indicator="_base_")
    df_long = df_long.query("_base_ == 'left_only'").drop(columns="_base_")
    df_long["Faltas"] = df_long["Check"].fillna("0").apply(lambda x: 1 if str(x).strip() == "0" else 0)

except Exception as e:
    st.error(f"Erro ao processar a planilha: {e}")
    st.stop()
    
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

user = getpass.getuser()

# Tabs principais
tabs = st.tabs([
    "📊 Dashboard Geral", "📈 Histórico", "🚨 Alertas",
    "📥 Exportações", "📂 Base Criados", "⚙️ Configurações", "👤 Perfil"
])

# Recupera filtros da aba Configurações (com fallback para "Todas")
conta_sel = st.session_state.get("filtro_conta_config", "Todas")
marca_sel = st.session_state.get("filtro_marca_config", "Todas")

# Aplica os filtros no dataframe
df_fil = df_long.copy()
if conta_sel != "Todas":
    df_fil = df_fil[df_fil["Conta_Exibicao"] == conta_sel]
if marca_sel != "Todas":
    df_fil = df_fil[df_fil["Marca"] == marca_sel]
    
with tabs[0]:
    if df_long.empty:
        st.warning("Nenhum dado disponível.")
        
    else:
        # CSS dos cards compactos e centralizados
        st.markdown("""
        <style>
        .custom-card {
            background-color: rgba(255, 255, 255, 0.07);
            padding: 15px;
            border-radius: 12px;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
            height: 100px;

            /* Centralização total */
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }
        .custom-card:hover {
            transform: scale(1.03);
            box-shadow: 0 6px 16px rgba(80, 191, 255, 0.3);
        }
        .custom-card h3 {
            margin: 0;
            font-size: 16px;
            color: white;
        }
        .custom-card p {
            margin-top: 8px;
            font-size: 22px;
            font-weight: bold;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

        # Dados dinâmicos
        tz = pytz.timezone("America/Sao_Paulo")
        now = datetime.now(tz).strftime("%d/%m/%Y %H:%M")
        
        # --- CARDS ---
        col1, col2, col3 = st.columns(3, gap="medium")

        with col1:
            st.markdown(f"""
            <div class="custom-card">
                <h3>📦 Total de Faltas</h3>
                <p>{tot_hoje}</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="custom-card">
                <h3>🏬 Contas Ativas</h3>
                <p>{df_faltas["Conta_Exibicao"].nunique()}</p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="custom-card">
                <h3>📅 Atualização</h3>
                <p>{now}</p>
            </div>
            """, unsafe_allow_html=True)

        # --- LINHA DIVISÓRIA ---
        st.markdown("<hr style='margin-top: 20px; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.1);' />", unsafe_allow_html=True)

        # --- GRÁFICO DE FALTAS POR CONTA ---
        st.markdown("### 📊 Faltas por Conta")
        try:
            df_raw_sem_header = pd.read_excel(planilha, sheet_name="Geral", header=None)
            linha_faltas = df_raw_sem_header.iloc[4, 4:]
            cabecalhos = df_raw_sem_header.iloc[5, 4:]

            contas, faltas = [], []
            for val, conta in zip(linha_faltas, cabecalhos):
                if pd.notna(val) and str(val).isdigit():
                    if conta_sel == "Todas" or str(conta).strip().upper() == conta_sel:
                        contas.append(str(conta).strip().upper())
                        faltas.append(int(val))

            df_faltas_corrigido = pd.DataFrame({"Conta_Exibicao": contas, "Faltas": faltas})

            g1 = px.bar(
                df_faltas_corrigido.sort_values("Faltas", ascending=True),
                x="Faltas", y="Conta_Exibicao", orientation="h",
                color="Faltas", text="Faltas"
            )
            g1.update_layout(
                plot_bgcolor="rgba(255,255,255,0.02)",
                paper_bgcolor="rgba(255,255,255,0.02)",
                height=500
            )
            g1.update_traces(textposition="outside")
            st.plotly_chart(g1, use_container_width=True, key="g_contas")

        except Exception as erro:
            st.error(f"Erro ao gerar gráfico: {erro}")

        # --- GRÁFICO DE MARCAS ---
        st.markdown("### 🏷️ Top Marcas com mais Faltas")
        top_m = (
            df_fil.groupby("Marca")["Faltas"]
            .sum()
            .reset_index()
            .sort_values("Faltas", ascending=False)
            .head(10)
        )
        g2 = px.bar(top_m, x="Faltas", y="Marca", orientation="h", color="Faltas", text="Faltas")
        g2.update_layout(
            plot_bgcolor="rgba(255,255,255,0.02)",
            paper_bgcolor="rgba(255,255,255,0.02)",
            height=500
        )
        g2.update_traces(textposition="outside")
        st.plotly_chart(g2, use_container_width=True, key="g_marcas")

        # --- TABELA DETALHADA ---
        st.markdown("### 📋 Tabela Geral de Dados")
        st.dataframe(
            df_fil[["SKU", "Titulo", "Estoque", "Marca", "Conta_Exibicao", "Faltas"]],
            height=400, use_container_width=True
        )
# --- TAB 1: Histórico ---
with tabs[1]:
    st.markdown("## 📈 Histórico de Faltas por Dia")

    if df_hist.empty:
        st.warning("Histórico vazio.")
        st.stop()

    try:
        # Convertendo corretamente para datetime.date
        data_max_ts = pd.to_datetime(df_hist["Data"].max())
        data_min_ts = pd.to_datetime(df_hist["Data"].min())

        if pd.isna(data_max_ts) or pd.isna(data_min_ts):
            raise ValueError("Datas inválidas")

        data_max = data_max_ts.date()
        data_min = data_min_ts.date()

        default_ini = max(data_min, data_max - timedelta(days=7))
        default_fim = data_max

        col1, col2 = st.columns(2)
        ini = col1.date_input("📅 De", value=default_ini, min_value=data_min, max_value=data_max, key="data_ini")
        fim = col2.date_input("📅 Até", value=default_fim, min_value=data_min, max_value=data_max, key="data_fim")

        df_periodo = df_hist[(df_hist["Data"] >= pd.to_datetime(ini)) & (df_hist["Data"] <= pd.to_datetime(fim))]

        if df_periodo.empty:
            st.warning("⚠️ Nenhum dado encontrado no período selecionado.")
        else:
            if len(df_periodo) >= 2:
                anterior = df_periodo.iloc[-2]["Total Faltas"]
                atual = df_periodo.iloc[-1]["Total Faltas"]
                variacao = atual - anterior
                pct = (variacao / anterior * 100) if anterior > 0 else 0
                emoji = "🔺" if variacao > 0 else "✅"
                st.markdown(f"**{emoji} Variação desde ontem:** {variacao:+} faltas ({pct:+.1f}%)")
            else:
                st.info("ℹ️ Selecione pelo menos dois dias para exibir comparativo.")

            st.markdown("### 📊 Evolução das Faltas")
            graf = px.line(
                df_periodo, x="Data", y="Total Faltas",
                markers=True, title="Tendência de Faltas por Dia"
            )
            graf.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis_title="Data",
                yaxis_title="Total de Faltas",
                title_x=0.5,
                height=500
            )
            st.plotly_chart(graf, use_container_width=True, key="graf_historico")

            st.markdown("### 📋 Tabela de Histórico")
            st.dataframe(df_periodo.sort_values("Data"), use_container_width=True, height=300)
            st.download_button("⬇️ Exportar Período Selecionado", df_periodo.to_csv(index=False).encode(), file_name="historico_periodo.csv", key="export_hist")
    except Exception as erro:
        st.error(f"❌ Erro ao configurar filtro de datas: {erro}")
# --- TAB 2: Alertas ---
with tabs[2]:
    st.markdown("## 🚨 Alertas Inteligentes")

    st.subheader("🔴 Contas com 50+ faltas")
    st.dataframe(df_faltas.query("Faltas>=50"), use_container_width=True)

    st.subheader("🟠 SKUs com Falta em 5+ Contas")
    sa = (
        df_long[df_long["Faltas"] == 1]
        .groupby("SKU")["Conta_Exibicao"]
        .agg([
            ("Contas", lambda x: ", ".join(sorted({str(i).strip().upper() for i in x if pd.notna(i)}))),
            ("Total", lambda x: sum(pd.notna(x)))
        ])
        .reset_index()
        .query("Total >= 5")
    )

    def alerta_emoji(total):
        if total >= 10:
            return "📛 " + str(total)
        else:
            return "✅ " + str(total)

    sa["Total"] = sa["Total"].apply(alerta_emoji)
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
with tabs[5]:  # ⚙️ Configurações
    st.markdown("## ⚙️ Configurações de Filtros")
    st.markdown("Use os filtros abaixo para ajustar os dados exibidos nos gráficos e na tabela da aba *Dashboard Geral*.")

    # Lista de opções
    contas_opcoes = ["Todas"] + sorted(df_long["Conta_Exibicao"].dropna().unique().tolist())
    marcas_opcoes = ["Todas"] + sorted(df_long["Marca"].dropna().unique().tolist())

    # Índice atual salvo no session_state
    conta_sel_index = contas_opcoes.index(st.session_state.get("filtro_conta_config", "Todas"))
    marca_sel_index = marcas_opcoes.index(st.session_state.get("filtro_marca_config", "Todas"))

    # Filtros visuais
    nova_conta = st.selectbox("📁 Filtrar por Conta", contas_opcoes, index=conta_sel_index)
    nova_marca = st.selectbox("🏷️ Filtrar por Marca", marcas_opcoes, index=marca_sel_index)

    # Botões
    col_btn1, col_btn2 = st.columns([1, 1])

    with col_btn1:
        if st.button("✅ Aplicar Filtros"):
            st.session_state["filtro_conta_config"] = nova_conta
            st.session_state["filtro_marca_config"] = nova_marca
            st.success("🎯 Filtros aplicados! Volte à aba *Dashboard Geral* para visualizar os resultados.", icon="✅")

    with col_btn2:
        if st.button("🔄 Limpar Filtros"):
            st.session_state["filtro_conta_config"] = "Todas"
            st.session_state["filtro_marca_config"] = "Todas"
            st.info("🧹 Filtros redefinidos. Todos os dados serão exibidos no Dashboard.", icon="ℹ️")

# --- TAB 6: Perfil ---
with tabs[6]:
    st.markdown("## 👤 Perfil do Usuário")
    st.success(f"Usuário: **{user}**")
    st.markdown("**Função:** Desenvolvedor & Automatizador de Processos")

st.divider()
st.markdown("📌 Desenvolvido por Jair Jales com base na ideia de Ronald Costa")
