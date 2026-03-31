import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import os

# Configuração da página (Estilo moderno conforme documentação)
st.set_page_config(
    page_title="Predição de Riscos - BJJ Dev",
    page_icon="🏗️",
    layout="wide"
)

# --- FUNÇÕES COM CACHE (Conforme tutorial oficial) ---

@st.cache_resource
def load_model():
    """Carrega o modelo de Machine Learning (Sklearn 1.8.0)"""
    try:
        # Caminho relativo para o GitHub
        model_path = 'pipeline_random_forest.pkl'
        if os.path.exists(model_path):
            return joblib.load(model_path)
        return None
    except Exception as e:
        st.error(f"Erro ao carregar modelo: {e}")
        return None

@st.cache_data
def load_data():
    """Carrega o dataset consolidado"""
    try:
        df = pd.read_csv('df_mestre_consolidado.csv.gz', compression='gzip')
        # Garantir conversão de datas como no tutorial Uber
        if 'data_inicio_prevista' in df.columns:
            df['data_inicio_prevista'] = pd.to_datetime(df['data_inicio_prevista'])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None

# --- INÍCIO DO APP ---

st.title('🏗️ Análise de Riscos e Atrasos em Obras')
st.markdown("""
Esta aplicação utiliza **Inteligência Artificial** para prever o atraso estimado em dias 
com base em fatores climáticos, logística e histórico de fornecedores.
""")

# Carregamento de recursos
pipeline = load_model()
df_full = load_data()

if pipeline is None:
    st.warning("⚠️ O modelo 'pipeline_random_forest.pkl' não foi encontrado no repositório.")
    st.stop()

# --- SIDEBAR DE FILTROS (Interatividade conforme tutorial) ---
st.sidebar.header("Parâmetros da Obra")

with st.sidebar:
    cidade = st.selectbox("Cidade", ["recife", "manaus", "sao_paulo", "fortaleza"])
    etapa = st.selectbox("Etapa da Obra", ["fundação", "estrutura", "acabamento", "instalações"])
    material = st.selectbox("Material Principal", ["concreto", "aço", "madeira", "piso"])
    
    st.divider()
    
    chuva = st.slider("Chuva Prevista (mm)", 0, 500, 50)
    confiabilidade = st.select_slider("Rating de Confiabilidade do Fornecedor", 
                                    options=[1, 2, 3, 4, 5], value=3)

# --- ÁREA DE PREDIÇÃO ---

# Criar dataframe de entrada para o modelo
input_dict = {
    'etapa': [etapa],
    'status': ['Em Andamento'],
    'cidade': [cidade],
    'data_inicio_prevista': [pd.Timestamp.now()],
    'material': [material],
    'tipo_solo': ['arenoso'], # Valor default
    'chuva_mm': [float(chuva)],
    'rating_confiabilidade': [float(confiabilidade)],
    'orcamento_estimado': [1000000.0],
    'prazo_previsto_dias': [120],
    'prazo_real_dias': [0],
    'atrasou': [0],
    'atrasou_entrega': [0],
    'nivel_chuva': [float(chuva)],
    'complexidade_obra': [15.0],
    'taxa_insucesso_fornecedor': [0.5],
    'fator_clima_solo': [100.0],
    'score_logistica': [3.0]
}

input_df = pd.DataFrame(input_dict)

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Resultado da Predição")
    try:
        predicao = pipeline.predict(input_df)[0]
        
        # Estilização do resultado
        cor_alerta = "red" if predicao > 5 else "orange" if predicao > 2 else "green"
        st.metric(label="Atraso Estimado", value=f"{predicao:.1f} dias", delta_color="inverse")
        
        if predicao > 5:
            st.error("🚨 Risco Alto de Atraso detectado!")
        elif predicao > 2:
            st.warning("⚠️ Risco Moderado.")
        else:
            st.success("✅ Obra dentro do cronograma esperado.")
            
    except Exception as e:
        st.error(f"Erro na predição: {e}")

with col2:
    st.subheader("Análise de Sensibilidade")
    # Gráfico simples de impacto da chuva (Simulando variação)
    faixa_chuva = list(range(0, 501, 50))
    impacto = []
    for c in faixa_chuva:
        temp_df = input_df.copy()
        temp_df['chuva_mm'] = float(c)
        temp_df['nivel_chuva'] = float(c)
        impacto.append(pipeline.predict(temp_df)[0])
    
    fig = px.line(x=faixa_chuva, y=impacto, labels={'x':'Chuva (mm)', 'y':'Atraso (dias)'},
                 title="Impacto do Clima no Cronograma")
    st.plotly_chart(fig, use_container_width=True)

# --- VISUALIZAÇÃO DE DADOS (Checkbox como no tutorial Uber) ---
if st.checkbox('Ver base de dados histórica (Raw Data)'):
    st.subheader('Dados Consolidados')
    if df_full is not None:
        st.dataframe(df_full.head(100))
    else:
        st.info("Dataset não disponível para visualização.")
