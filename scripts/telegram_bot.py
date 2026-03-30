import os
import joblib
import pandas as pd
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Base do projeto
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

            # -------------------------------
            # BANCO DE DADOS
            # -------------------------------
            db_url = os.getenv("DATABASE_URL")

            if db_url and db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+psycopg://")

            cls._instance.engine = create_engine(
                db_url,
                connect_args={"prepare_threshold": 0} if "psycopg" in db_url else {},
                pool_pre_ping=True
            )

            # -------------------------------
            # MODELOS
            # -------------------------------
            try:
                model_path = BASE_DIR / "models" / "pipeline_random_forest.pkl"
                meta_path = BASE_DIR / "models" / "features_metadata.joblib"

                cls._instance.pipeline = joblib.load(model_path)
                cls._instance.features = joblib.load(meta_path)

                logger.info("🧠 Modelos carregados com sucesso")

            except Exception as e:
                logger.error(f"Erro ao carregar modelos: {e}")

        return cls._instance


# -------------------------------
# FUNÇÃO PRINCIPAL
# -------------------------------
async def processar_analise(update: Update, context: ContextTypes.DEFAULT_TYPE, id_obra: str):
    res = MLResources.get_all()

    if res.pipeline is None:
        await update.message.reply_text("⚠️ IA indisponível. Tente novamente em instantes.")
        return

    status_msg = await update.message.reply_text("🔍 Processando análise...")

    try:
        query = text("""
            SELECT * 
            FROM view_analise_preditiva 
            WHERE UPPER(id_obra) = :val 
            LIMIT 1
        """)

        with res.engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"val": id_obra.upper()})

        if df.empty:
            await status_msg.edit_text(f"❌ Obra `{id_obra.upper()}` não encontrada.")
            return

        # -------------------------------
        # 🔥 CORREÇÃO CRÍTICA AQUI
        # -------------------------------

        # Reindex
        X = df.reindex(columns=res.features, fill_value=0)

        # Converter tudo para numérico
        X = X.apply(pd.to_numeric, errors="coerce")

        # Substituir NaN por 0
        X = X.fillna(0)

        logger.info(f"Dados para predição:\n{X.head()}")

        # -------------------------------
        # PREDIÇÃO
        # -------------------------------
        prediction = res.pipeline.predict(X)

        risco_val = float(prediction[0])

        # -------------------------------
        # CLASSIFICAÇÃO
        # -------------------------------
        if risco_val <= 7:
            status_cor, emoji = "NORMAL", "🟢"
        elif risco_val <= 12:
            status_cor, emoji = "ALERTA", "🟡"
        else:
            status_cor, emoji = "CRÍTICO", "🔴"

        resultado = (
            f"🏗️ *Análise Preditiva*\n\n"
            f"📍 Obra: `{id_obra.upper()}`\n"
            f"📊 Status: {emoji} *{status_cor}*\n"
            f"⏳ Atraso: `{risco_val:.1f} dias`"
        )

        await status_msg.edit_text(resultado, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Erro na análise: {e}", exc_info=True)
        await status_msg.edit_text("⚠️ Erro ao processar análise.")
