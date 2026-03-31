import streamlit as st
import pandas as pd
import joblib
import plotly.express as px
import numpy as np
import os
import sys
from pathlib import Path

# --- CORREÇÃO DE PATHS PARA STREAMLIT CLOUD ---
# Resolve o erro "ModuleNotFoundError: No module named 'scripts'"
file_path = Path(__file__).resolve()
scripts_dir = file_path.parent
root_dir = scripts_dir.parent

if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

# 1. CONFIGURAÇÃO DA PÁGINA (Padrão Executivo)
st.set_page_config(
    page_title="CCbjj - Engenharia", 
    page_icon="🏗️", 
    layout="wide"
)

# Estilização CSS para um visual profissional
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stMetric label { font-weight: bold; color: #1B5E20; }
    </style>
    """, unsafe_allow_html=True)

# 2. CARREGAMENTO DE ASSETS (Otimizado com caminhos relativos ao Root)
@st.cache_resource
def load_assets():
    # Caminhos baseados na raiz do projeto
    m_path = root_dir / "models" / "pipeline_random_forest.pkl"
    f_path = root_dir / "models" / "features_metadata.joblib"
    d_path = root_dir / "data" / "processed" / "df_mestre_consolidado.csv.gz"
    
    # Carregamento do Modelo e Metadados
    pipeline = joblib.load(m_path) if m_path.exists() else None
    features = joblib.load(f_path) if f_path.exists() else None
    
    # Carregamento do Dataframe
    df = pd.DataFrame()
    if d_path.exists():
        try:
            df = pd.read_csv(d_path, compression='gzip')
        except Exception:
            df = pd.read_csv(d_path) # Tenta sem compressão se falhar
    else:
        # Fallback para CSV comum na mesma pasta
        alt_path = root_dir / "data" / "processed" / "df_mestre_consolidado.csv"
        if alt_path.exists():
            df = pd.read_csv(alt_path)
            
    return pipeline, features, df

pipeline, features_order, df_base = load_assets()

# --- INTERFACE LATERAL (PAINEL DE CONTROLE) ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/construction.png", width=80)
    st.title("🕹️ Parâmetros da Obra")
    st.markdown("Ajuste as variáveis para simulação em tempo real.")
    
    def get_options(col, default_list):
        if not df_base.empty and col in df_base.columns:
            opts = [str(x).title() for x in df_base[col].unique() if pd.notna(x)]
            return sorted(list(set(opts)))
        return default_list

    cidade_ui = st.selectbox("Localização", get_options('cidade', ['Recife', 'São Paulo']))
    etapa_ui = st.selectbox("Etapa Construtiva", get_options('etapa', ['Fundação', 'Estrutura', 'Acabamento']))
    solo_ui = st.selectbox("Geologia do Terreno", get_options('tipo_solo', ['Argiloso', 'Arenoso', 'Rochoso']))
    material_ui = st.selectbox("Insumo Crítico", get_options('material', ['Cimento', 'Aço', 'Brita']))
    
    st.markdown("---")
    val_chuva = st.slider("Previsão Pluviométrica (mm)", 0, 800, 150)
    val_rating = st.select_slider("Rating de Confiança do Fornecedor", options=[1, 2, 3, 4, 5], value=3)

# --- CORPO DO DASHBOARD ---
st.title("🛡️ CCBJJ Engenharia & Inteligência de Risco 2.0")
st.caption("Sistema Preditivo de Atrasos para Decisão de Diretoria e Logística")
st.markdown("---")

if pipeline is None or features_order is None:
    st.error(f"🚨 **Erro de Deploy:** Ativos da IA não encontrados. Verifique se os arquivos estão em: `{root_dir}/models/`")
else:
    try:
        # Extração de Dados de Contexto
        if not df_base.empty:
            contexto = df_base[(df_base['cidade'].str.lower() == cidade_ui.lower()) & 
                               (df_base['etapa'].str.lower() == etapa_ui.lower())]
            if not contexto.empty:
                orcamento = contexto['orcamento_estimado'].mean()
                complexidade = contexto['complexidade_obra'].mean()
                risco_etapa = contexto['risco_etapa'].mean()
                taxa_forn = contexto['taxa_insucesso_fornecedor'].mean()
            else:
                orcamento, complexidade, risco_etapa, taxa_forn = 12000000.0, 15.0, 5.0, 0.12
        else:
            orcamento, complexidade, risco_etapa, taxa_forn = 10000000.0, 10.0, 4.0, 0.10

        # Montagem do DataFrame para Predição
        input_dict = {
            'orcamento_estimado': float(orcamento),
            'rating_confiabilidade': float(val_rating),
            'taxa_insucesso_fornecedor': float(taxa_forn),
            'complexidade_obra': float(complexidade),
            'risco_etapa': float(risco_etapa),
            'nivel_chuva': float(val_chuva),
            'tipo_solo': solo_ui.lower(),
            'material': material_ui.lower(),
            'cidade': cidade_ui.lower(),
            'etapa': etapa_ui.lower()
        }
        
        input_df = pd.DataFrame([input_dict])
        
        # Alinhamento de Features (One-Hot Encoding Manual / Reindex)
        # Cria colunas faltantes com valor 0
        input_prepared = pd.get_dummies(input_df)
        input_prepared = input_prepared.reindex(columns=features_order, fill_value=0)

        # Execução da IA
        pred_dias = float(pipeline.predict(input_prepared)[0])
        pred_dias = max(0, pred_dias)

        # MÉTRICAS
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Atraso Estimado", f"{pred_dias:.1f} Dias")
        with m2:
            status = "🔴 Crítico" if pred_dias > 12 else "🟡 Alerta" if pred_dias > 7 else "🟢 Estável"
            st.metric("Status do Risco", status)
        with m3:
            st.metric("Custo de Oportunidade (Est.)", f"R$ {pred_dias * 5000:,.2f}")

        st.markdown("### 📈 Análise de Sensibilidade")
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("Simulação: Chuva vs. Atraso")
            faixas = np.linspace(0, 800, 20)
            lista_sim = []
            for f in faixas:
                temp_df = input_prepared.copy()
                temp_df['nivel_chuva'] = float(f)
                lista_sim.append(pipeline.predict(temp_df)[0])
            
            fig_chuva = px.line(x=faixas, y=lista_sim, markers=True, template="plotly_white",
                               labels={'x': 'Chuva (mm)', 'y': 'Dias de Atraso'})
            fig_chuva.update_traces(line_color='#2E7D32')
            st.plotly_chart(fig_chuva, use_container_width=True)

        with col_b:
            st.subheader("Impacto por Geologia")
            solos = ['arenoso', 'argiloso', 'rochoso']
            lista_solo = []
            for s in solos:
                temp_df = input_df.copy()
                temp_df['tipo_solo'] = s
                temp_prepared = pd.get_dummies(temp_df).reindex(columns=features_order, fill_value=0)
                lista_solo.append(pipeline.predict(temp_prepared)[0])
            
            fig_solo = px.bar(x=[s.title() for s in solos], y=lista_solo, color=lista_solo,
                             color_continuous_scale='Greens', labels={'x': 'Solo', 'y': 'Atraso'})
            st.plotly_chart(fig_solo, use_container_width=True)

        st.info(f"💡 **Nota:** Simulação baseada no cenário de {cidade_ui} para a etapa de {etapa_ui}.")

    except Exception as e:
        st.error(f"Erro na inferência da IA: {e}")

st.markdown("<br><hr><center><b>CCBJJ Engenharia & Inteligência de Risco v2.0</b> | Sergio Santos</center>", unsafe_allow_html=True)
