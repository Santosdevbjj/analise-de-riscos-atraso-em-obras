import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
import numpy as np
import os
import sys
from pathlib import Path

# --- CONFIGURAÇÃO DE AMBIENTE (Streamlit Cloud) ---
file_path = Path(__file__).resolve()
scripts_dir = file_path.parent
root_dir = scripts_dir.parent

# Garante que o Python encontre os módulos na raiz
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="CCBJJ - Inteligência de Risco", 
    page_icon="🏗️", 
    layout="wide"
)

# Estilização Profissional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    [data-testid="metric-container"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #1B5E20;
    }
    .stMetric label { font-size: 1.1rem !important; font-weight: 600 !important; color: #1B5E20 !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARREGAMENTO DE ATIVOS (Cacheado)
@st.cache_resource
def load_assets():
    # Caminhos baseados na estrutura do repositório
    m_path = root_dir / "models" / "pipeline_random_forest.pkl"
    f_path = root_dir / "models" / "features_metadata.joblib"
    d_path = root_dir / "data" / "processed" / "df_mestre_consolidado.csv.gz"
    
    try:
        # Carrega o Pipeline (que já contém o ColumnTransformer)
        pipeline = joblib.load(m_path)
        
        # Carrega a lista de colunas EXATAS que o modelo espera (fit_columns)
        # De acordo com os logs, o modelo espera colunas como 'etapa', 'status', 'cidade', etc.
        features_metadata = joblib.load(f_path)
        
        # Carrega os dados históricos para preencher a UI
        if d_path.exists():
            df = pd.read_csv(d_path, compression='gzip')
        else:
            # Tenta sem compressão caso o arquivo esteja extraído
            alt_path = root_dir / "data" / "processed" / "df_mestre_consolidado.csv"
            df = pd.read_csv(alt_path) if alt_path.exists() else pd.DataFrame()
            
        return pipeline, features_metadata, df
    except Exception as e:
        st.error(f"Erro crítico no carregamento: {e}")
        return None, None, pd.DataFrame()

pipeline, expected_features, df_base = load_assets()

# --- PAINEL LATERAL ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/construction.png", width=80)
    st.title("🕹️ Parâmetros")
    
    def get_opts(column):
        if not df_base.empty and column in df_base.columns:
            return sorted([str(x).title() for x in df_base[column].unique() if pd.notna(x)])
        return ["Padrão"]

    cidade_ui = st.selectbox("Localização", get_opts('cidade'))
    etapa_ui = st.selectbox("Etapa da Obra", get_opts('etapa'))
    solo_ui = st.selectbox("Tipo de Solo", get_opts('tipo_solo'))
    material_ui = st.selectbox("Material Crítico", get_opts('material'))
    
    st.divider()
    val_chuva = st.slider("Precipitação (mm)", 0, 800, 150)
    val_rating = st.select_slider("Rating Fornecedor", options=[1, 2, 3, 4, 5], value=3)

# --- CONTEÚDO PRINCIPAL ---
st.title("🛡️ CCBJJ Engenharia: Análise Preditiva de Risco")
st.caption("Previsão de cronograma baseada em Random Forest e histórico consolidado")

if pipeline is None:
    st.warning("⚠️ O sistema está aguardando os arquivos de IA para iniciar.")
else:
    try:
        # 1. OBTER MÉDIAS HISTÓRICAS PARA O CONTEXTO
        # O modelo precisa de colunas que não estão na UI (ex: orcamento_estimado, risco_etapa)
        if not df_base.empty:
            filt = df_base[df_base['cidade'].str.lower() == cidade_ui.lower()]
            if filt.empty: filt = df_base
            
            # Valores de referência para o cenário selecionado
            orcamento = filt['orcamento_estimado'].median()
            prazo_prev = filt['prazo_previsto_dias'].median()
            complexidade = filt['complexidade_obra'].median()
            taxa_forn = filt['taxa_insucesso_fornecedor'].mean()
            risco_etapa = filt['risco_etapa'].mean()
            clima_solo = filt['fator_clima_solo'].mean()
            logistica = filt['score_logistica'].mean()
        else:
            orcamento, prazo_prev, complexidade, taxa_forn, risco_etapa, clima_solo, logistica = 10000000.0, 180, 10.0, 0.1, 5.0, 1.0, 3.0

        # 2. CONSTRUÇÃO DO DATAFRAME DE ENTRADA
        # O Pipeline espera as colunas ORIGINAIS (antes do One-Hot Encoding)
        # O erro de "Feature names mismatch" ocorria porque você passava as colunas já transformadas
        input_data = pd.DataFrame([{
            'etapa': etapa_ui.lower(),
            'status': 'em andamento',
            'cidade': cidade_ui.lower(),
            'data_inicio_prevista': '2025-01-01', # Placeholder
            'id_fornecedor': 'FORN-DEFAULT',
            'material': material_ui.lower(),
            'tipo_solo': solo_ui.lower(),
            'dias_atraso': 0, 
            'orcamento_estimado': float(orcamento),
            'prazo_previsto_dias': float(prazo_prev),
            'prazo_real_dias': float(prazo_prev),
            'chuva_mm': float(val_chuva),
            'atrasou': 0,
            'atrasou_entrega': 0,
            'rating_confiabilidade': float(val_rating),
            'nivel_chuva': float(val_chuva),
            'complexidade_obra': float(complexidade),
            'taxa_insucesso_fornecedor': float(taxa_forn),
            'fator_clima_solo': float(clima_solo),
            'score_logistica': float(logistica),
            'risco_etapa': float(risco_etapa)
        }])

        # Reordena as colunas para o que o Pipeline viu no fit()
        # Isso garante que o ColumnTransformer não quebre
        final_input = input_data[expected_features]

        # 3. PREDICÃO
        pred_dias = float(pipeline.predict(final_input)[0])
        pred_dias = max(0, pred_dias)

        # EXIBIÇÃO DE RESULTADOS
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Atraso Estimado", f"{pred_dias:.1f} Dias")
        with m2:
            status = "🔴 Crítico" if pred_dias > 12 else "🟡 Alerta" if pred_dias > 6 else "🟢 Estável"
            st.metric("Risco do Cenário", status)
        with m3:
            custo_est = pred_dias * 4500 # Custo diário estimado
            st.metric("Impacto Financeiro (Est.)", f"R$ {custo_est:,.2f}")

        # GRÁFICOS DE SENSIBILIDADE
        st.divider()
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Simulação de Clima")
            faixa_chuva = np.linspace(0, 800, 15)
            preds_chuva = []
            for c in faixa_chuva:
                sim_df = final_input.copy()
                sim_df['chuva_mm'] = c
                sim_df['nivel_chuva'] = c
                preds_chuva.append(pipeline.predict(sim_df)[0])
            
            fig_chuva = px.line(x=faixa_chuva, y=preds_chuva, markers=True, 
                               labels={'x': 'Chuva (mm)', 'y': 'Atraso'}, template="plotly_white")
            fig_chuva.update_traces(line_color='#1B5E20')
            st.plotly_chart(fig_chuva, use_container_width=True)
            
        with c2:
            st.subheader("Risco por Fornecedor")
            ratings = [1, 2, 3, 4, 5]
            preds_rate = []
            for r in ratings:
                sim_df = final_input.copy()
                sim_df['rating_confiabilidade'] = r
                preds_rate.append(pipeline.predict(sim_df)[0])
            
            fig_rate = px.bar(x=ratings, y=preds_rate, color=preds_rate, 
                             color_continuous_scale="Greens", labels={'x': 'Rating', 'y': 'Atraso'})
            st.plotly_chart(fig_rate, use_container_width=True)

        st.info(f"💡 Dica: O cenário em {cidade_ui} para a etapa de {etapa_ui} sugere foco em {material_ui}.")

    except Exception as e:
        st.error(f"Erro na predição: {e}")
        st.info("O modelo espera colunas específicas. Verifique os logs do terminal.")

st.markdown("---")
st.markdown("<center><b>CCBJJ Engenharia & Data Science v2.0</b> | Sergio Santos</center>", unsafe_allow_html=True)
