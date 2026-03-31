import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import os

# Configuração da página para o padrão moderno de 2026
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

# --- FUNÇÕES DE CARREGAMENTO COM CACHE ---

@st.cache_resource
def load_ml_resources():
    """Carrega o modelo e metadados de features"""
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
    """Carrega o dataset consolidado para análise histórica"""
    try:
        if os.path.exists(DATA_PATH):
            df = pd.read_csv(DATA_PATH, compression='gzip')
            # Tratamento de datas
            date_cols = ['data_inicio_prevista']
            for col in date_cols:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col])
            return df
        return None
    except Exception as e:
        st.error(f"Erro ao carregar banco de dados: {e}")
        return None

# --- INTERFACE PRINCIPAL ---

# Exibição do Logo
if os.path.exists(LOGO_PATH):
    st.image(LOGO_PATH, width=200)

st.title('🏗️ Análise de Riscos e Atrasos em Obras')
st.info("Sistema Inteligente de Predição de Cronograma - Versão 2026")

# Carregar recursos
resources = load_ml_resources()
pipeline = resources['pipeline']
metadata = resources['metadata']
df_full = load_historical_data()

# Verificação de integridade do modelo
if pipeline is None:
    st.error(f"❌ Erro Crítico: Modelo não encontrado em `{MODEL_PATH}`")
    st.stop()

# --- SIDEBAR: ENTRADA DE DADOS ---
st.sidebar.header("🛠️ Parâmetros da Obra")

with st.sidebar:
    # Opções dinâmicas baseadas no histórico
    lista_cidades = sorted(df_full['cidade'].unique()) if df_full is not None else ["recife", "manaus", "sao_paulo"]
    lista_etapas = sorted(df_full['etapa'].unique()) if df_full is not None else ["fundação", "estrutura", "acabamento"]
    lista_materiais = sorted(df_full['material'].unique()) if df_full is not None else ["concreto", "aço", "piso"]
    
    cidade = st.selectbox("Localidade", lista_cidades)
    etapa = st.selectbox("Etapa Atual", lista_etapas)
    material = st.selectbox("Material Principal", lista_materiais)
    
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

# Criando o DataFrame de entrada
# NOTA: Adicionada a coluna 'dias_atraso' com valor 0 pois o Pipeline treinado a exige no transformador
input_data = {
    'etapa': [etapa],
    'status': ['Em Andamento'],
    'cidade': [cidade],
    'data_inicio_prevista': [pd.Timestamp.now()],
    'material': [material],
    'tipo_solo': ['arenoso'], 
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
    'dias_atraso': [0.0]  # COLUNA ESSENCIAL PARA EVITAR O ERRO DE VALIDACAO DO SKLEARN
}

input_df = pd.DataFrame(input_data)

# Layout de colunas para resultados
res_col1, res_col2 = st.columns([1, 1.5])

with res_col1:
    st.subheader("📊 Resultado da IA")
    try:
        # Predição principal
        prediction = pipeline.predict(input_df)[0]
        # Garantir que não mostre valores negativos
        resultado_dias = max(0, prediction)
        
        if resultado_dias > 7:
            st.error("**Risco Crítico**")
            cor_delta = "inverse"
        elif resultado_dias > 3:
            st.warning("**Risco Moderado**")
            cor_delta = "normal"
        else:
            st.success("**Baixo Risco**")
            cor_delta = "normal"

        st.metric(label="Atraso Estimado", value=f"{resultado_dias:.1f} dias", delta_color=cor_delta)
        
        st.write("---")
        st.write("**Análise Sintética:**")
        st.caption(f"A análise para {etapa} em {cidade.title()} considera variáveis climáticas e o histórico do material {material}.")

    except Exception as e:
        st.error(f"Erro na análise: {e}")
        st.info("O modelo requer todas as colunas de treinamento presentes no input.")

with res_col2:
    st.subheader("📈 Simulação de Clima vs Atraso")
    try:
        faixa_chuva = np.linspace(0, 500, 15).tolist()
        impacto_clima = []
        
        for c in faixa_chuva:
            temp_df = input_df.copy()
            temp_df['chuva_mm'] = float(c)
            temp_df['nivel_chuva'] = float(c)
            # A predição aqui também usará o 'dias_atraso' fictício do temp_df
            val = pipeline.predict(temp_df)[0]
            impacto_clima.append(max(0, val))
        
        fig = px.area(x=faixa_chuva, y=impacto_clima, 
                     labels={'x': 'Chuva Esperada (mm)', 'y': 'Dias de Atraso'},
                     title="Impacto Pluviométrico no Cronograma",
                     color_discrete_sequence=['#1B5E20'])
        
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Não foi possível gerar o gráfico de simulação: {e}")

# --- VISUALIZAÇÃO DE DADOS HISTÓRICOS ---
st.divider()
expander = st.expander("📂 Explorar Base de Dados Histórica")
with expander:
    if df_full is not None:
        st.write(f"Total de registros: {len(df_full)}")
        cidades_disponiveis = df_full['cidade'].unique()
        filtro = st.multiselect("Filtrar visualização por cidade:", cidades_disponiveis)
        
        df_display = df_full[df_full['cidade'].isin(filtro)] if filtro else df_full
        st.dataframe(df_display.head(100), use_container_width=True)
    else:
        st.warning("Base histórica não carregada.")
