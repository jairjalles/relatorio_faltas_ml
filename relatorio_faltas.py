# Arquivo: dashboard_faltas_final.py
# Autor: Jair Jales - Versao Profissional com todas as melhorias e ajustes finais

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

# ===== FUNDO PERSONALIZADO COM CAIXA OPACA =====
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
        section.main > div {{
            background-color: rgba(255, 255, 255, 0.08);
            border-radius: 18px;
            padding: 25px;
            margin-top: 10px;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.2);
            transition: all 0.4s ease-in-out;
        }}
        h1,h2,h3,h4,h5,h6,p,label,span {{
            color: white !important;
        }}
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
        .stTabs [data-baseweb="tab"] {{
            font-size: 18px !important;
            padding: 12px 28px !important;
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

# Uma camada extra de opacidade para o bloco principal
st.markdown("""
    <style>
    section.main > div {
        background-color: rgba(255,255,255,0.10) !important;
    }
    </style>
""", unsafe_allow_html=True)

set_background("fundo_interface.jpeg")

# ===== LOGO + TÍTULO =====
col_logo, col_title = st.columns([1, 5])
with col_logo:
    st.image("logo.png", width=200)
with col_title:
    st.markdown("""
        <div style='display:flex;align-items:center;height:200px;'>
            <h1 style='color:white;margin:0;'>📊 Dashboard de Faltas - Mercado Livre</h1>
        </div>
    """, unsafe_allow_html=True)

# ===== CAMINHO DO ARQUIVO =====
st.markdown("📁 **Caminho da planilha sincronizada:**")
col_path, col_btn = st.columns([5,1])
caminho = col_path.text_input("planilhas/", value="planilhas/FALTAS MERCADO LIVRE 2025.xlsx", key="input_path")
atualizar = col_btn.button("🔄 Atualizar", key="btn_atualizar")

if not os.path.isfile(caminho):
    st.error("Caminho inválido. Verifique se a planilha está na pasta correta.")
    st.stop()

# ===== LEITURA E PROCESSAMENTO =====
try:
    df_raw = pd.read_excel(caminho, sheet_name="Geral", header=[4,5], dtype=str)
    df_detalhado = pd.read_excel(caminho, sheet_name="Geral", header=5, dtype=str)
    df_base = pd.read_excel(caminho, sheet_name="Base Criados", header=2, dtype=str)

    contas, faltas = [], []
    for col in df_raw.columns[4:]:
        valor, nome = col
        if isinstance(nome,str) and str(valor).isdigit():
            contas.append(nome.split('.')[0].strip().upper())
            faltas.append(int(valor))
    df_faltas = (
        pd.DataFrame({"Conta_Exibicao":contas,"Faltas":faltas})
          .drop_duplicates("Conta_Exibicao")
    )

    colunas_validas = df_detalhado.columns[4:]
    df_long = df_detalhado.melt(
        id_vars=["SKU","Estoque","Marca","Titulo"],
        value_vars=colunas_validas,
        var_name="Conta", value_name="Check"
    )
    df_long["Conta_Exibicao"] = (
        df_long["Conta"].str.split(".").str[0].str.upper().str.strip()
    )
    df_long["Faltas"] = df_long["Check"].fillna("0")\
                             .apply(lambda x: 1 if str(x).strip()=="0" else 0)
except Exception as e:
    st.error(f"Erro ao processar a planilha: {e}")
    st.stop()

# ===== HISTÓRICO =====
historico_path = "historico_faltas.csv"
hoje = datetime.today().strftime("%Y-%m-%d")
totais_atuais = df_faltas["Faltas"].sum()

if os.path.exists(historico_path):
    df_historico = pd.read_csv(historico_path)
    if hoje not in df_historico["Data"].values:
        df_historico = pd.concat([
            df_historico,
            pd.DataFrame([{"Data":hoje,"Total Faltas":totais_atuais}])
        ], ignore_index=True)
        df_historico.to_csv(historico_path, index=False)
else:
    df_historico = pd.DataFrame([{"Data":hoje,"Total Faltas":totais_atuais}])
    df_historico.to_csv(historico_path, index=False)

df_historico["Data"] = pd.to_datetime(df_historico["Data"])

# ===== PERFIL DO USUÁRIO =====
usuario_local = getpass.getuser()

# ===== ABAS =====
tabs = st.tabs([
    "📊 Dashboard Geral", "📈 Histórico", "🚨 Alertas",
    "📥 Exportações", "📂 Base Criados", "⚙️ Configurações", "👤 Perfil"
])

with tabs[0]:
    if df_long.empty or "Conta_Exibicao" not in df_long.columns:
        st.warning("Nenhum dado disponível para exibir.")
    else:
        # ==== Dados completos, sem filtro por conta ====
        df_filtrado = df_long.copy()

        # Hora com fuso do Brasil
        fuso_br = pytz.timezone("America/Sao_Paulo")
        agora = datetime.now(fuso_br)
        ultima_atualizacao = agora.strftime("%d/%m/%Y %H:%M")

        # Comparativo semanal
        semana_passada = (agora - timedelta(days=7)).strftime("%Y-%m-%d")
        total_hoje = int(df_faltas["Faltas"].sum())
        total_anteriores = df_historico.loc[
            df_historico["Data"] == semana_passada, "Total Faltas"
        ].sum()
        diferenca = total_hoje - total_anteriores
        percentual = (diferenca / total_anteriores * 100) if total_anteriores > 0 else 0

        # Mensagens de alerta
        emoji_variacao = "🔺" if percentual > 0 else "✅"
        mensagem_semana = (
            f"{emoji_variacao} {'Aumento' if percentual > 0 else 'Redução'} "
            f"de {abs(percentual):.1f}% nas faltas desde a semana passada"
        )

        sku_impacto = (
            df_long[df_long["Faltas"] == 1]
            .groupby("SKU")["Conta_Exibicao"]
            .count()
            .reset_index(name="Qtd Contas")
        )
        sku_top = sku_impacto.sort_values("Qtd Contas", ascending=False).head(1)
        if not sku_top.empty:
            sku_maior = sku_top.iloc[0]["SKU"]
            qtd_maior = sku_top.iloc[0]["Qtd Contas"]
            impacto_mensagem = (
                f"⚠️ SKU {sku_maior} aparece com falta em {qtd_maior} contas"
            )
        else:
            impacto_mensagem = "✅ Nenhum SKU com alto impacto detectado hoje"

        skus_hoje = df_long[df_long["Faltas"] == 1]["SKU"].nunique()
        alerta_skus = (
            f"🆕 {skus_hoje} SKU{'s' if skus_hoje > 1 else ''} com faltas identificadas hoje"
        )

        # ==== CARDS ====
        st.markdown(f"""
        <div style='display:flex;gap:20px;flex-wrap:wrap;margin-bottom:30px;'>
            <div class='custom-card'>
                <h3>📦 Total de Faltas</h3>
                <p style='font-size:26px;font-weight:bold;'>{total_hoje}</p>
            </div>
            <div class='custom-card'>
                <h3>🏬 Contas Ativas</h3>
                <p style='font-size:26px;font-weight:bold;'>{df_faltas["Conta_Exibicao"].nunique()}</p>
            </div>
            <div class='custom-card'>
                <h3>📅 Última Atualização</h3>
                <p style='font-size:20px;font-weight:bold;'>{ultima_atualizacao}</p>
            </div>
        </div>
        <div style='margin-bottom:30px;color:white;'>
            <h4>🔔 Alertas do Sistema:</h4>
            <ul style='font-size:16px;'>
                <li>{mensagem_semana}</li>
                <li>{impacto_mensagem}</li>
                <li>{alerta_skus}</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

        # ==== GRÁFICO DE CONTAS ====
        st.markdown("### 📊 Faltas por Conta")
        graf_contas = px.bar(
            df_faltas.sort_values("Faltas"),
            x="Faltas", y="Conta_Exibicao", orientation="h",
            color="Faltas", text="Faltas"
        )
        graf_contas.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        graf_contas.update_traces(textposition="outside")
        st.plotly_chart(graf_contas, use_container_width=True, key="chart_contas")

        # ==== GRÁFICO DE MARCAS ====
        st.markdown("### 🏷️ Top Marcas com mais Faltas")
        top_marcas = (
            df_filtrado.groupby("Marca")["Faltas"]
            .sum().reset_index()
            .sort_values("Faltas", ascending=False)
            .head(10)
        )
        graf_marcas = px.bar(
            top_marcas, x="Faltas", y="Marca", orientation="h",
            color="Faltas", text="Faltas"
        )
        graf_marcas.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)"
        )
        graf_marcas.update_traces(textposition="outside")
        st.plotly_chart(graf_marcas, use_container_width=True, key="chart_marcas")

        # ==== TABELA DETALHADA ====
        st.markdown("### 📋 Tabela Geral de Dados")
        st.dataframe(
            df_filtrado[["SKU","Titulo","Estoque","Marca","Conta_Exibicao","Faltas"]],
            use_container_width=True,
            height=400
        )
    else:
        st.warning("Nenhum dado disponível para exibir.")

# === ABA 1: Histórico ===
with tabs[1]:
    st.markdown("## 📈 Evolução das Faltas")
    col1, col2 = st.columns(2)
    data_inicio = col1.date_input("De", value=datetime.today(), key="hist_de")
    data_fim = col2.date_input("Até", value=datetime.today(), key="hist_ate")
    df_periodo = df_historico[
        (df_historico["Data"]>=pd.to_datetime(data_inicio)) &
        (df_historico["Data"]<=pd.to_datetime(data_fim))
    ]
    graf_hist = px.line(df_periodo, x="Data", y="Total Faltas", markers=True)
    st.plotly_chart(
        graf_hist,
        use_container_width=True,
        key="chart_hist"
    )

# === ABA 2: Alertas ===
with tabs[2]:
    st.markdown("## 🚨 Alertas Inteligentes")
    st.subheader("🔴 Contas com 50+ faltas")
    st.dataframe(df_faltas[df_faltas["Faltas"]>=50])
    st.subheader("🟠 SKUs com falta em 5+ contas")
    skus_alerta = (
        df_long[df_long["Faltas"]==1]
        .groupby("SKU")["Conta_Exibicao"]
        .count().reset_index(name="Contas com Falta")
    )
    st.dataframe(skus_alerta[skus_alerta["Contas com Falta"]>=5])

# === ABA 3: Exportações ===
with tabs[3]:
    st.markdown("## 📥 Exportações")
    st.download_button(
        "⬇️ Faltas por Conta",
        df_faltas.to_csv(index=False).encode("utf-8"),
        file_name="faltas_por_conta.csv",
        key="down_faltas"
    )
    st.download_button(
        "⬇️ Detalhado por SKU",
        df_long.to_csv(index=False).encode("utf-8"),
        file_name="faltas_detalhadas.csv",
        key="down_detalhado"
    )
    st.download_button(
        "⬇️ Histórico de Faltas",
        df_historico.to_csv(index=False).encode("utf-8"),
        file_name="historico_faltas.csv",
        key="down_historico"
    )

# === ABA 4: Base Criados ===
with tabs[4]:
    st.markdown("## 📂 Base Criados")
    st.dataframe(df_base, use_container_width=True)
    st.link_button(
        "🔧 Editar manualmente no SharePoint",
        "https://topshopbrasil.sharepoint.com/:x:/r/sites/criacao/_layouts/15/Doc.aspx?"
        "sourcedoc=%7BE87C6408-4F5C-4882-BB8E-5FB2A0845FD6%7D&"
        "file=FALTAS%20MERCADO%20LIVRE%202025%20-%20Copia.xlsx&"
        "action=default&mobileredirect=true",
        key="link_sp"
    )

# === ABA 5: Configurações ===
with tabs[5]:
    st.markdown("## ⚙️ Configurações")
    sku = st.text_input("🔍 Buscar SKU específico", key="cfg_sku")
    if sku:
        resultado = df_long[
            df_long["SKU"].str.contains(sku, case=False, na=False)
        ]
        st.dataframe(resultado)
    if st.button("🗑️ Limpar histórico local", key="cfg_reset"):
        if os.path.exists(historico_path):
            os.remove(historico_path)
            st.success("Histórico deletado com sucesso!")

# === ABA 6: Perfil ===
with tabs[6]:
    st.markdown("## 👤 Perfil do Usuário")
    st.success(f"Usuário atual: **{usuario_local}**")
    st.markdown("**Função:** Desenvolvedor & Automatizador de Processos")

st.divider()
st.markdown("📌 Desenvolvido por Jair Jales com base na ideia de Ronald Costa")
