import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import os

# Configuração da página
st.set_page_config(
    page_title="Predição de Riscos - BJJ Dev",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONFIGURAÇÃO DE CAMINHOS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'pipeline_random_forest.pkl')
METADATA_PATH = os.path.join(BASE_DIR, 'models', 'features_metadata.joblib')
DATA_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'df_mestre_consolidado.csv.gz')
LOGO_PATH = os.path.join(BASE_DIR, 'assets', 'logo_ccbjj.png')

# --- FUNÇÕES DE CARREGAMENTO ---
@st.cache_resource
def load_ml_resources():
    resources = {'pipeline': None, 'metadata': None}
    try:
        if os.path.exists(MODEL_PATH):
            resources['pipeline'] = joblib.load(MODEL_PATH)
        if os.path.exists(METADATA_PATH):
            resources['metadata'] = joblib.load(METADATA_PATH)
        return resources
    except Exception as e:
        st.error(f"Erro ao carregar recursos de ML: {e}")
        return resources

@st.cache_data
def load_historical_data():
    try:
        if os.path.exists(DATA_PATH):
            df = pd.read_csv(DATA_PATH, compression='gzip')
            if 'data_inicio_prevista' in df.columns:
                df['data_inicio_prevista'] = pd.to_datetime(df['data_inicio_prevista'])
            return df
        return None
    except Exception as e:
        st.error(f"Erro ao carregar banco de dados: {e}")
        return None

# --- INTERFACE PRINCIPAL ---
if os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, width=200)

st.title('🏗️ Dashboard de Riscos e Atrasos em Obras')
st.info("Sistema Inteligente de Predição de Cronograma - Versão 2026")

resources = load_ml_resources()
pipeline = resources['pipeline']
metadata = resources['metadata']
df_full = load_historical_data()

if pipeline is None:
    st.error(f"❌ Erro Crítico: Modelo não encontrado em `{MODEL_PATH}`")
    st.stop()

# --- SIDEBAR ---
st.sidebar.header("🛠️ Parâmetros da Obra")
with st.sidebar:
    lista_cidades = sorted(df_full['cidade'].unique()) if df_full is not None else ["recife", "manaus", "sao_paulo"]
    lista_etapas = sorted(df_full['etapa'].unique()) if df_full is not None else ["fundação", "estrutura", "acabamento"]
    lista_materiais = sorted(df_full['material'].unique()) if df_full is not None else ["concreto", "aço", "piso"]
    lista_solos = sorted(df_full['tipo_solo'].unique()) if df_full is not None and 'tipo_solo' in df_full.columns else ["arenoso", "argiloso", "rochoso"]

    cidade = st.selectbox("Localidade", lista_cidades)
    etapa = st.selectbox("Etapa Atual", lista_etapas)
    material = st.selectbox("Material Principal", lista_materiais)
    tipo_solo = st.selectbox("Tipo do Solo", lista_solos)

    st.divider()
    chuva = st.slider("Previsão Pluviométrica (mm)", 0, 500, 50)
    confiabilidade = st.select_slider("Rating do Fornecedor", options=[1, 2, 3, 4, 5], value=3)
    orcamento = st.number_input("Orçamento Estimado (R$)", min_value=10000, value=1000000)

    st.divider()
    st.markdown("### 👨‍💻 Desenvolvedor")
    st.write("**Sérgio Santos**")
    st.markdown("[🌐 Portfólio](https://portfoliosantossergio.vercel.app)")
    st.markdown("[🔗 LinkedIn](https://www.linkedin.com/in/santossergioluiz)")
    st.caption("BJJ Dev Analytics © 2026")

# --- LÓGICA DE PREDIÇÃO ---
input_data = {
    'etapa': [etapa],
    'status': ['Em Andamento'],
    'cidade': [cidade],
    'data_inicio_prevista': ['2025-01-01'],  # valor fixo conhecido pelo modelo
    'material': [material],
    'tipo_solo': [tipo_solo],
    'chuva_mm': [float(chuva)],
    'rating_confiabilidade': [float(confiabilidade)],
    'orcamento_estimado': [float(orcamento)],
    'prazo_previsto_dias': [120.0],
    'prazo_real_dias': [0.0],
    'atrasou': [0],
    'atrasou_entrega': [0],
    'nivel_chuva': [float(chuva)],
    'complexidade_obra': [15.0],
    'taxa_insucesso_fornecedor': [0.5],
    'fator_clima_solo': [100.0],
    'score_logistica': [float(confiabilidade)],
    'id_fornecedor': ['FORN-GENERICO'],
    'dias_atraso': [0.0]
}
input_df = pd.DataFrame(input_data)

if metadata and 'features' in metadata:
    expected_cols = set(metadata['features'])
    missing_cols = expected_cols - set(input_df.columns)
    if missing_cols:
        st.error(f"❌ Colunas ausentes no input: {missing_cols}")
        st.stop()

# --- DASHBOARD ---
st.markdown("## 📊 Resultado da IA e Relatórios Avançados")

col1, col2, col3 = st.columns([1, 1, 1])

try:
    prediction = pipeline.predict(input_df)[0]
    resultado_dias = max(0, prediction)

    # Cores vivas para UX/UI
    if resultado_dias > 7:
        col1.metric("Atraso Estimado", f"{resultado_dias:.1f} dias", delta="ALTO", delta_color="inverse")
        st.error("🚨 **Risco Crítico**")
    elif resultado_dias > 3:
        col1.metric("Atraso Estimado", f"{resultado_dias:.1f} dias", delta="MÉDIO", delta_color="off")
        st.warning("⚠️ **Risco Moderado**")
    else:
        col1.metric("Atraso Estimado", f"{resultado_dias:.1f} dias", delta="BAIXO", delta_color="normal")
        st.success("✅ **Baixo Risco**")

    # Relatório sintético
    col2.markdown("### 🔎 Insights")
    col2.write(f"- Cidade: **{cidade.title()}**")
    col2.write(f"- Etapa: **{etapa}**")
    col2.write(f"- Material: **{material}**")
    col2.write(f"- Tipo de Solo: **{tipo_solo}**")
    col2.write(f"- Previsão de chuva: **{chuva} mm**")
    col2.write(f"- Rating fornecedor: **{confiabilidade}**")
    col2.write(f"- Orçamento: R$ {orcamento:,.0f}")

    # Distribuição histórica
    if df_full is not None and 'dias_atraso' in df_full.columns:
        fig_hist = px.histogram(df_full, x="dias_atraso", nbins=30,
                                title="Distribuição Histórica de Atrasos",
                                color_discrete_sequence=["#FF5722"])
        col3.plotly_chart(fig_hist, use_container_width=True)

except Exception as e:
    st.error(f"Erro na análise: {e}")

# --- Simulação de Clima vs Atraso ---
st.markdown("## 🌦️ Simulação de Impacto Climático")
try:
    faixa_chuva = np.linspace(0, 500, 15).tolist()
    impacto_clima = []
    for c in faixa_chuva:
        temp_df = input_df.copy()
        temp_df['chuva_mm'] = float(c)
        temp_df['nivel_chuva'] = float(c)
        val = pipeline.predict(temp_df)[0]
        impacto_clima.append(max(0, val))

    fig = px.line(
        x=faixa_chuva,
        y=impacto_clima,
        labels={'x': 'Chuva Esperada (mm)', 'y': 'Dias de Atraso'},
        title="Impacto da Chuva no Cronograma",
        color)
