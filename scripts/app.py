import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
import numpy as np
import os
import sys
from pathlib import Path

# --- CONFIGURAÇÃO DE AMBIENTE ---
file_path = Path(__file__).resolve()
scripts_dir = file_path.parent
root_dir = scripts_dir.parent

if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="CCBJJ - Inteligência de Risco", 
    page_icon="🏗️", 
    layout="wide"
)

# Estilização
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
    m_path = root_dir / "models" / "pipeline_random_forest.pkl"
    f_path = root_dir / "models" / "features_metadata.joblib"
    d_path = root_dir / "data" / "processed" / "df_mestre_consolidado.csv.gz"
    
    try:
        pipeline = joblib.load(m_path)
        # Tenta carregar metadados, se falhar, usa as colunas padrão identificadas no PKL
        try:
            features_metadata = joblib.load(f_path)
        except:
            # Colunas extraídas do erro de log (ordem do OneHotEncoder + StandardScaler)
            features_metadata = [
                'etapa', 'status', 'cidade', 'data_inicio_prevista', 'id_fornecedor', 
                'material', 'tipo_solo', 'dias_atraso', 'orcamento_estimado', 
                'prazo_previsto_dias', 'prazo_real_dias', 'chuva_mm', 'atrasou', 
                'atrasou_entrega', 'rating_confiabilidade', 'nivel_chuva', 
                'complexidade_obra', 'taxa_insucesso_fornecedor', 'fator_clima_solo', 
                'score_logistica'
            ]
        
        # Carregamento do DataFrame
        df = pd.DataFrame()
        if d_path.exists():
            df = pd.read_csv(d_path, compression='gzip')
        else:
            alt_path = root_dir / "data" / "processed" / "df_mestre_consolidado.csv"
            if alt_path.exists():
                df = pd.read_csv(alt_path)
            
        return pipeline, features_metadata, df
    except Exception as e:
        st.error(f"Erro ao carregar arquivos do modelo: {e}")
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
st.title("🛡️ CCBJJ Engenharia: Análise Preditiva")
st.caption("Previsão de cronograma baseada em Random Forest")

if pipeline is None:
    st.warning("⚠️ Aguardando carregamento dos modelos de IA...")
else:
    try:
        # 1. OBTER VALORES DE REFERÊNCIA
        if not df_base.empty:
            filt = df_base[df_base['cidade'].astype(str).str.lower() == cidade_ui.lower()]
            if filt.empty: filt = df_base
            
            orcamento = filt['orcamento_estimado'].median() if 'orcamento_estimado' in filt.columns else 10000000.0
            prazo_prev = filt['prazo_previsto_dias'].median() if 'prazo_previsto_dias' in filt.columns else 180.0
            complexidade = filt['complexidade_obra'].median() if 'complexidade_obra' in filt.columns else 10.0
            taxa_forn = filt['taxa_insucesso_fornecedor'].mean() if 'taxa_insucesso_fornecedor' in filt.columns else 0.1
            fator_clima = filt['fator_clima_solo'].mean() if 'fator_clima_solo' in filt.columns else 1.0
            logistica = filt['score_logistica'].mean() if 'score_logistica' in filt.columns else 3.0
        else:
            orcamento, prazo_prev, complexidade, taxa_forn, fator_clima, logistica = 10000000.0, 180.0, 10.0, 0.1, 1.0, 3.0

        # 2. CONSTRUÇÃO DOS DADOS DE ENTRADA
        # Criamos um dicionário com TODAS as colunas que o modelo viu no treinamento
        data_dict = {
            'etapa': etapa_ui.lower(),
            'status': 'em andamento',
            'cidade': cidade_ui.lower(),
            'data_inicio_prevista': '2025-01-01',
            'id_fornecedor': 'FORN-DEFAULT',
            'material': material_ui.lower(),
            'tipo_solo': solo_ui.lower(),
            'dias_atraso': 0.0,
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
            'fator_clima_solo': float(fator_clima),
            'score_logistica': float(logistica)
        }

        # Garantir que apenas as colunas esperadas pelo Pipeline sejam passadas e na ordem certa
        input_df = pd.DataFrame([data_dict])
        
        # Se 'expected_features' for uma lista de colunas, filtramos e ordenamos
        if isinstance(expected_features, list):
            # Adiciona colunas faltantes com valor zero se necessário (segurança)
            for col in expected_features:
                if col not in input_df.columns:
                    input_df[col] = 0.0
            final_input = input_df[expected_features]
        else:
            final_input = input_df

        # 3. PREDICÃO
        pred_dias = float(pipeline.predict(final_input)[0])
        pred_dias = max(0, pred_dias)

        # MÉTRICAS PRINCIPAIS
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Atraso Estimado", f"{pred_dias:.1f} Dias")
        with m2:
            status_cor = "🔴 Crítico" if pred_dias > 12 else "🟡 Alerta" if pred_dias > 6 else "🟢 Estável"
            st.metric("Risco do Cenário", status_cor)
        with m3:
            custo_est = pred_dias * 4500
            st.metric("Impacto Financeiro (Est.)", f"R$ {custo_est:,.2f}")

        # GRÁFICOS
        st.divider()
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Simulação de Clima")
            faixa_chuva = np.linspace(0, 800, 10)
            preds_chuva = []
            for c in faixa_chuva:
                sim_df = final_input.copy()
                if 'chuva_mm' in sim_df.columns: sim_df['chuva_mm'] = float(c)
                if 'nivel_chuva' in sim_df.columns: sim_df['nivel_chuva'] = float(c)
                preds_chuva.append(pipeline.predict(sim_df)[0])
            
            fig_chuva = px.line(x=faixa_chuva, y=preds_chuva, markers=True, 
                               labels={'x': 'Chuva (mm)', 'y': 'Atraso Estimado'},
                               template="plotly_white")
            fig_chuva.update_traces(line_color='#1B5E20')
            st.plotly_chart(fig_chuva, use_container_width=True)
            
        with c2:
            st.subheader("Risco por Confiabilidade")
            ratings = [1, 2, 3, 4, 5]
            preds_rate = []
            for r in ratings:
                sim_df = final_input.copy()
                if 'rating_confiabilidade' in sim_df.columns: sim_df['rating_confiabilidade'] = float(r)
                preds_rate.append(pipeline.predict(sim_df)[0])
            
            fig_rate = px.bar(x=ratings, y=preds_rate, color=preds_rate, 
                             color_continuous_scale="RdYlGn_r",
                             labels={'x': 'Rating Fornecedor', 'y': 'Atraso Estimado'})
            st.plotly_chart(fig_rate, use_container_width=True)

    except Exception as e:
        st.error(f"Erro na predição: {e}")
        st.info("Dica: Verifique se as colunas do modelo coincidem com os dados de entrada.")

st.markdown("---")
st.markdown("<center><b>CCBJJ Engenharia & Data Science v2.1</b></center>", unsafe_allow_html=True)
