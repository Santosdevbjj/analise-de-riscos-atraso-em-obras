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
# Definindo caminhos relativos baseados na estrutura do seu repositório
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, 'models', 'pipeline_random_forest.pkl')
METADATA_PATH = os.path.join(BASE_DIR, 'models', 'features_metadata.joblib')
DATA_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'df_mestre_consolidado.csv.gz')

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

st.title('🏗️ Análise de Riscos e Atrasos em Obras')
st.info("Sistema Inteligente de Predição de Cronograma - Versão 2026")

# Carregar recursos
resources = load_ml_resources()
pipeline = resources['pipeline']
metadata = resources['metadata']
df_full = load_historical_data()

# Verificação de integridade dos arquivos
if pipeline is None:
    st.error(f"❌ Erro Crítico: Modelo não encontrado em `{MODEL_PATH}`")
    st.markdown("Verifique se o arquivo `pipeline_random_forest.pkl` está na pasta `models/`.")
    st.stop()

# --- SIDEBAR: ENTRADA DE DADOS ---
st.sidebar.header("🛠️ Parâmetros da Obra")

with st.sidebar:
    # Seleção de Cidade e Etapa baseada nos dados se disponíveis
    lista_cidades = sorted(df_full['cidade'].unique()) if df_full is not None else ["recife", "manaus", "sao_paulo"]
    lista_etapas = sorted(df_full['etapa'].unique()) if df_full is not None else ["fundação", "estrutura", "acabamento"]
    lista_materiais = sorted(df_full['material'].unique()) if df_full is not None else ["concreto", "aço", "piso"]
    
    cidade = st.selectbox("Localidade", lista_cidades)
    etapa = st.selectbox("Etapa Atual", lista_etapas)
    material = st.selectbox("Material Principal", lista_materiais)
    
    st.divider()
    
    chuva = st.slider("Previsão Pluviométrica (mm)", 0, 500, 50, help="Volume de chuva esperado para o período da etapa")
    confiabilidade = st.select_slider("Rating do Fornecedor", options=[1, 2, 3, 4, 5], value=3)
    orcamento = st.number_input("Orçamento Estimado (R$)", min_value=10000, value=1000000)

# --- LÓGICA DE PREDIÇÃO ---

# Criando o DataFrame de entrada com TODAS as colunas que o modelo espera
# O modelo Random Forest exige exatamente as mesmas colunas do treinamento
input_data = {
    'etapa': [etapa],
    'status': ['Em Andamento'],
    'cidade': [cidade],
    'data_inicio_prevista': [pd.Timestamp.now()],
    'material': [material],
    'tipo_solo': ['arenoso'], # Valor padrão
    'chuva_mm': [float(chuva)],
    'rating_confiabilidade': [float(confiabilidade)],
    'orcamento_estimado': [float(orcamento)],
    'prazo_previsto_dias': [120],
    'prazo_real_dias': [0],
    'atrasou': [0],
    'atrasou_entrega': [0],
    'nivel_chuva': [float(chuva)],
    'complexidade_obra': [15.0],
    'taxa_insucesso_fornecedor': [0.5],
    'fator_clima_solo': [100.0],
    'score_logistica': [float(confiabilidade)],
    'id_fornecedor': ['FORN-GENERICO'] # Adicionado para evitar erro de coluna ausente
}

input_df = pd.DataFrame(input_data)

# Layout de colunas para resultados
res_col1, res_col2 = st.columns([1, 1.5])

with res_col1:
    st.subheader("📊 Resultado da IA")
    try:
        # Realiza a predição
        resultado_dias = pipeline.predict(input_df)[0]
        
        # Define cor e status
        if resultado_dias > 7:
            st.error(f"**Risco Crítico**")
            cor = "inverse"
        elif resultado_dias > 3:
            st.warning(f"**Risco Moderado**")
            cor = "normal"
        else:
            st.success(f"**Baixo Risco**")
            cor = "normal"

        st.metric(label="Atraso Estimado", value=f"{resultado_dias:.1f} dias", delta_color=cor)
        
        st.write("---")
        st.write("**Resumo da Análise:**")
        st.caption(f"A combinação de fatores em {cidade.title()} para a etapa de {etapa} indica uma variação provável no cronograma.")

    except Exception as e:
        st.error(f"Falha na Predição: {e}")
        st.info("Dica: Verifique se as colunas do modelo coincidem com o input.")

with res_col2:
    st.subheader("📈 Simulação de Clima vs Atraso")
    # Gerando variação dinâmica para o gráfico
    faixa_chuva = np.linspace(0, 500, 10).tolist()
    impacto_clima = []
    
    for c in faixa_chuva:
        temp_df = input_df.copy()
        temp_df['chuva_mm'] = c
        temp_df['nivel_chuva'] = c
        impacto_clima.append(pipeline.predict(temp_df)[0])
    
    fig = px.area(x=faixa_chuva, y=impacto_clima, 
                 labels={'x': 'Chuva Esperada (mm)', 'y': 'Dias de Atraso'},
                 title="Sensibilidade Pluviométrica",
                 color_discrete_sequence=['#1B5E20'])
    st.plotly_chart(fig, use_container_width=True)

# --- VISUALIZAÇÃO DE DADOS HISTÓRICOS ---
st.divider()
expander = st.expander("📂 Explorar Dados Históricos (Dataset Consolidado)")
with expander:
    if df_full is not None:
        st.write(f"Exibindo amostra de {len(df_full)} registros carregados de `{DATA_PATH}`")
        # Filtro rápido na visualização
        filtro_cidade = st.multiselect("Filtrar por Cidade", options=df_full['cidade'].unique())
        if filtro_cidade:
            st.dataframe(df_full[df_full['cidade'].isin(filtro_cidade)].head(50))
        else:
            st.dataframe(df_full.head(50))
    else:
        st.warning("⚠️ Base de dados histórica não encontrada no caminho especificado.")

st.sidebar.caption("BJJ Dev Analytics © 2026")
