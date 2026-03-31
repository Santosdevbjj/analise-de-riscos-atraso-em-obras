import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt
import shap
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

# --- LÓGICA DE PREDIÇÃO ---
input_data = {
    'etapa': [etapa],
    'status': ['Em Andamento'],
    'cidade': [cidade],
    'data_inicio_prevista': ['2025-01-01'],
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

# --- DASHBOARD ---
st.markdown("## 📊 Resultado da IA e Relatórios Avançados")

try:
    prediction = pipeline.predict(input_df)[0]
    resultado_dias = max(0, prediction)

    if resultado_dias > 7:
        st.error(f"🚨 Risco Crítico: {resultado_dias:.1f} dias de atraso")
    elif resultado_dias > 3:
        st.warning(f"⚠️ Risco Moderado: {resultado_dias:.1f} dias de atraso")
    else:
        st.success(f"✅ Baixo Risco: {resultado_dias:.1f} dias de atraso")

    st.markdown("### 🔎 Insights")
    st.write(f"- Cidade: **{cidade.title()}**")
    st.write(f"- Etapa: **{etapa}**")
    st.write(f"- Material: **{material}**")
    st.write(f"- Tipo de Solo: **{tipo_solo}**")
    st.write(f"- Previsão de chuva: **{chuva} mm**")
    st.write(f"- Rating fornecedor: **{confiabilidade}**")
    st.write(f"- Orçamento: R$ {orcamento:,.0f}")

except Exception as e:
    st.error(f"Erro na análise: {e}")

# --- Comparação entre cidades/etapas ---
st.markdown("## 🏙️ Comparação entre Cidades e Etapas")
if df_full is not None:
    fig_comp = px.box(df_full, x="cidade", y="dias_atraso", color="etapa",
                      title="Comparação de Atrasos por Cidade e Etapa",
                      color_discrete_sequence=px.colors.qualitative.Bold)
    st.plotly_chart(fig_comp, use_container_width=True)

# --- Heatmap de correlação ---
st.markdown("## 🔥 Heatmap de Correlação")
if df_full is not None:
    corr = df_full.corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
    st.pyplot(fig)

# --- Explicabilidade com SHAP ---
st.markdown("## 🧠 Explicabilidade do Modelo (SHAP)")
try:
    explainer = shap.Explainer(pipeline)
    shap_values = explainer(input_df)
    st.set_option('deprecation.showPyplotGlobalUse', False)
    shap.summary_plot(shap_values, input_df, plot_type="bar")
    st.pyplot(bbox_inches='tight')
except Exception as e:
    st.warning(f"Não foi possível gerar explicabilidade SHAP: {e}")

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
        color_discrete_sequence=["#2196F3"]
    ) 
     fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#f8f9fa",
        font=dict(size=14, color="#212121"),
        title_font=dict(size=18, color="#0d47a1", family="Arial Black"),
        xaxis=dict(showgrid=True, gridcolor="#e0e0e0"),
        yaxis=dict(showgrid=True, gridcolor="#e0e0e0")
    )
    st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
    st.warning(f"Não foi possível gerar o gráfico de simulação: {e}") 
