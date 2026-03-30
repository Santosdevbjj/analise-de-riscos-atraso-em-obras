import os
import joblib
import pandas as pd
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Configurações de Path
BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)

# Cache de Recursos em Nível de Módulo (Singleton)
class MLResources:
    _instance = None
    
    def __init__(self):
        self.pipeline = None
        self.features = None
        self.engine = None

    @classmethod
    def get_all(cls):
        if cls._instance is None:
            cls._instance = cls()
            
            # 1. Configuração do Banco de Dados (Padrão Supabase/Render 2026)
            db_url = os.getenv("DATABASE_URL")
            if db_url and db_url.startswith("postgresql://"):
                # Atualiza para o driver assíncrono/moderno psycopg
                db_url = db_url.replace("postgresql://", "postgresql+psycopg://")
            
            cls._instance.engine = create_engine(
                db_url,
                # prepare_threshold=0 é vital para Transaction Poolers (como do Supabase)
                connect_args={"prepare_threshold": 0} if "psycopg" in db_url else {},
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            
            # 2. Carregamento dos Modelos (Caminhos relativos ao BASE_DIR)
            try:
                model_path = BASE_DIR / "pipeline_random_forest.pkl"
                meta_path = BASE_DIR / "features_metadata.joblib"
                
                cls._instance.pipeline = joblib.load(model_path)
                cls._instance.features = joblib.load(meta_path)
                logger.info("🧠 Modelos de IA carregados com sucesso.")
            except Exception as e:
                logger.error(f"Erro ao carregar modelos: {e}")
                
        return cls._instance

async def processar_analise(update: Update, context: ContextTypes.DEFAULT_TYPE, id_obra: str):
    """
    Lógica de negócio para busca no banco e predição via IA.
    """
    res = MLResources.get_all()
    
    # Feedback visual para o usuário (UX)
    status_msg = await update.message.reply_text("🔍 Consultando base de dados e processando IA...")

    try:
        # Busca otimizada (apenas as colunas necessárias para o modelo)
        query = text("SELECT * FROM view_analise_preditiva WHERE UPPER(id_obra) = :val LIMIT 1")
        
        with res.engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"val": id_obra.upper()})

        if df.empty:
            await status_msg.edit_text(f"❌ Obra `{id_obra.upper()}` não localizada no sistema.")
            return

        # --- PIPELINE DE IA ---
        # Reordena e garante que todas as colunas do treino existam (fill_value=0 para novas)
        X = df.reindex(columns=res.features, fill_value=0)
        
        # Predição (Randon Forest)
        prediction = res.pipeline.predict(X)
        risco_val = float(prediction[0])
        
        # Lógica de Classificação de Risco
        if risco_val <= 7:
            status_cor, emoji = "NORMAL", "🟢"
        elif risco_val <= 12:
            status_cor, emoji = "ALERTA", "🟡"
        else:
            status_cor, emoji = "CRÍTICO", "🔴"

        # Resposta Final formatada
        resultado_texto = (
            f"🏗️ *Análise Preditiva CCBJJ*\n\n"
            f"📍 Obra: `{id_obra.upper()}`\n"
            f"📊 Status: {emoji} *{status_cor}*\n"
            f"⏳ Atraso Estimado: `{risco_val:.1f} dias`"
        )
        
        await status_msg.edit_text(resultado_texto, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Erro na análise da obra {id_obra}: {e}")
        await status_msg.edit_text("⚠️ Erro técnico ao processar análise. Tente novamente mais tarde.")
