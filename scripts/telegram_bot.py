import os
import joblib
import pandas as pd
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

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

            # DB
            db_url = os.getenv("DATABASE_URL")

            if not db_url:
                raise RuntimeError("DATABASE_URL não definido")

            if db_url.startswith("postgresql://"):
                db_url = db_url.replace("postgresql://", "postgresql+psycopg://")

            cls._instance.engine = create_engine(
                db_url,
                pool_pre_ping=True
            )

            # MODELOS
            try:
                model_path = BASE_DIR / "models" / "pipeline_random_forest.pkl"
                meta_path = BASE_DIR / "models" / "features_metadata.joblib"

                if not model_path.exists():
                    raise FileNotFoundError(model_path)

                cls._instance.pipeline = joblib.load(model_path)
                cls._instance.features = joblib.load(meta_path)

                logger.info("🧠 Modelos carregados com sucesso")

            except Exception as e:
                logger.error(f"Erro ao carregar modelos: {e}")

        return cls._instance


async def processar_analise(update: Update, context: ContextTypes.DEFAULT_TYPE, id_obra: str):
    res = MLResources.get_all()

    if res.pipeline is None:
        await update.message.reply_text("⚠️ IA indisponível no momento.")
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
            df = pd.read_sql(query, conn, params={"val": id_obra})

        if df.empty:
            await status_msg.edit_text(f"❌ Obra `{id_obra}` não encontrada.")
            return

        # 🔥 CORREÇÃO CRÍTICA AQUI
        X = df.reindex(columns=res.features, fill_value=0)

        # CONVERTE TUDO PARA NUMÉRICO
        X = X.apply(pd.to_numeric, errors="coerce")

        # REMOVE NaN
        X = X.fillna(0)

        # GARANTE FLOAT
        X = X.astype(float)

        logger.info(f"📊 Input modelo:\n{X.head()}")

        prediction = res.pipeline.predict(X)

        risco_val = float(prediction[0])

        # CLASSIFICAÇÃO
        if risco_val <= 7:
            status_cor, emoji = "NORMAL", "🟢"
        elif risco_val <= 12:
            status_cor, emoji = "ALERTA", "🟡"
        else:
            status_cor, emoji = "CRÍTICO", "🔴"

        texto = (
            f"🏗️ *Análise Preditiva*\n\n"
            f"📍 Obra: `{id_obra}`\n"
            f"📊 Status: {emoji} *{status_cor}*\n"
            f"⏳ Atraso: `{risco_val:.1f} dias`"
        )

        await status_msg.edit_text(texto, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Erro na análise: {e}")
        await status_msg.edit_text("⚠️ Erro ao processar análise.")
