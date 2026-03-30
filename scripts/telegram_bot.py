import os
import joblib
import pandas as pd
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Configurações de Path (BASE_DIR é a raiz do projeto)
BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)

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
            
            # 1. Banco de Dados
            db_url = os.getenv("DATABASE_URL")
            if db_url and db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+psycopg://")
            
            cls._instance.engine = create_engine(
                db_url,
                connect_args={"prepare_threshold": 0} if "psycopg" in db_url else {},
                pool_pre_ping=True
            )
            
            # 2. Carregamento dos Modelos (Caminho corrigido para a pasta models/)
            try:
                # O BASE_DIR aponta para a raiz. Adicionamos 'models' ao caminho.
                model_path = BASE_DIR / "models" / "pipeline_random_forest.pkl"
                meta_path = BASE_DIR / "models" / "features_metadata.joblib"
                
                # Verificação extra de existência para o log do Render
                if not model_path.exists():
                    logger.error(f"❌ ARQUIVO NÃO ENCONTRADO: {model_path}")
                
                cls._instance.pipeline = joblib.load(model_path)
                cls._instance.features = joblib.load(meta_path)
                logger.info("🧠 Modelos de IA carregados com sucesso da pasta /models.")
            except Exception as e:
                logger.error(f"Erro crítico ao carregar modelos: {e}")
                
        return cls._instance

async def processar_analise(update: Update, context: ContextTypes.DEFAULT_TYPE, id_obra: str):
    res = MLResources.get_all()
    
    # Validação amigável se os modelos falharam ao carregar
    if res.pipeline is None:
        await update.message.reply_text("⚠️ O sistema de IA está reiniciando. Tente em 30 segundos.")
        return

    status_msg = await update.message.reply_text("🔍 Consultando base de dados e processando IA...")

    try:
        query = text("SELECT * FROM view_analise_preditiva WHERE UPPER(id_obra) = :val LIMIT 1")
        
        with res.engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"val": id_obra.upper()})

        if df.empty:
            await status_msg.edit_text(f"❌ Obra `{id_obra.upper()}` não encontrada no banco.")
            return

        # Execução da Predição
        X = df.reindex(columns=res.features, fill_value=0)
        prediction = res.pipeline.predict(X)
        risco_val = float(prediction[0])
        
        if risco_val <= 7:
            status_cor, emoji = "NORMAL", "🟢"
        elif risco_val <= 12:
            status_cor, emoji = "ALERTA", "🟡"
        else:
            status_cor, emoji = "CRÍTICO", "🔴"

        resultado_texto = (
            f"🏗️ *Análise Preditiva CCBJJ*\n\n"
            f"📍 Obra: `{id_obra.upper()}`\n"
            f"📊 Status: {emoji} *{status_cor}*\n"
            f"⏳ Atraso Estimado: `{risco_val:.1f} dias`"
        )
        
        await status_msg.edit_text(resultado_texto, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Erro na análise: {e}")
        await status_msg.edit_text("⚠️ Erro técnico ao processar análise no banco de dados.")
