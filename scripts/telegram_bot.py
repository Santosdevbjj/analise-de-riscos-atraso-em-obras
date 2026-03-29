import os
import sys
import io
import joblib
import pandas as pd
import pytz
import logging
from pathlib import Path
from sqlalchemy import create_engine, text

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Configurações de Path
BASE_DIR = Path(__file__).resolve().parent.parent
BR_TIMEZONE = pytz.timezone('America/Sao_Paulo')

# Cache de Recursos (Lazy Loading para economizar RAM no Render)
RESOURCES = {"pipeline": None, "features": None, "engine": None}

def get_resources():
    if RESOURCES["engine"] is None:
        db_url = os.getenv("DATABASE_URL")
        
        # Regra 2026: Forçar driver psycopg + Transaction Pooler (Porta 6543)
        if db_url and "postgresql://" in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://")
        
        RESOURCES["engine"] = create_engine(
            db_url,
            connect_args={"prepare_threshold": 0}, # Crucial para o Pooler do Supabase
            pool_pre_ping=True
        )
        
        # Carregamento dos modelos
        RESOURCES["pipeline"] = joblib.load(BASE_DIR / "models/pipeline_random_forest.pkl")
        RESOURCES["features"] = joblib.load(BASE_DIR / "models/features_metadata.joblib")
        
    return RESOURCES

async def processar_analise(update: Update, context: ContextTypes.DEFAULT_TYPE, id_obra: str):
    res = get_resources()
    try:
        # Busca no Supabase (Transaction Mode) via SQLAlchemy
        query = text("SELECT * FROM view_analise_preditiva WHERE UPPER(id_obra) = :val LIMIT 1")
        with res["engine"].connect() as conn:
            df = pd.read_sql(query, conn, params={"val": id_obra.upper()})

        if df.empty:
            await update.message.reply_text(f"❌ Obra `{id_obra}` não encontrada no banco.")
            return

        # Execução da IA
        X = df.reindex(columns=res["features"], fill_value=0)
        prediction = res["pipeline"].predict(X)
        risco_val = float(prediction[0])
        status = "🟢 NORMAL" if risco_val <= 7 else "🟡 ALERTA" if risco_val <= 10 else "🔴 CRÍTICO"

        await update.message.reply_text(
            f"🏗️ *Análise Preditiva CCBJJ*\n\n"
            f"ID: `{id_obra.upper()}`\n"
            f"Status: *{status}*\n"
            f"Atraso Estimado: `{risco_val:.1f} dias`",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logging.error(f"Erro na análise: {e}")
        await update.message.reply_text("⚠️ Erro ao acessar o banco de dados.")
