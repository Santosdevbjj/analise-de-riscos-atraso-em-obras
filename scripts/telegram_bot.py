import os
import sys
import io
import joblib
import pandas as pd
import pytz
import logging
import asyncio
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, text

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

from telegram import Update, InputFile
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Configurações de Path e I18n
BASE_DIR = Path(__file__).resolve().parent.parent
BR_TIMEZONE = pytz.timezone('America/Sao_Paulo')

# Importações locais seguras
sys.path.append(str(BASE_DIR / "scripts"))
import database
from i18n import get_text

# Cache de Recursos com suporte a Psycopg 3 (Regra 2026)
RESOURCES = {"pipeline": None, "features": None, "df_base": None, "engine": None}

def get_resources():
    if RESOURCES["engine"] is None:
        db_url = os.getenv("DATABASE_URL")
        # Força o uso do driver psycopg para compatibilidade com o Pooler do Supabase
        if db_url and "postgresql://" in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+psycopg://")
        
        RESOURCES["engine"] = create_engine(
            db_url,
            connect_args={"prepare_threshold": 0}, # Obrigatório para porta 6543
            pool_pre_ping=True
        )
        # Carregamento dos modelos
        RESOURCES["pipeline"] = joblib.load(BASE_DIR / "models/pipeline_random_forest.pkl")
        RESOURCES["features"] = joblib.load(BASE_DIR / "models/features_metadata.joblib")
        RESOURCES["df_base"] = pd.read_csv(BASE_DIR / "data/processed/df_mestre_consolidado.csv.gz", compression="gzip")
    return RESOURCES

async def processar_analise(update: Update, context: ContextTypes.DEFAULT_TYPE, id_obra: str):
    user_id = update.effective_user.id
    lang = database.get_language(user_id)
    res = get_resources()
    
    try:
        # Busca no Supabase via Transaction Pooler
        query = text("SELECT * FROM view_analise_preditiva WHERE UPPER(id_obra) = :val LIMIT 1")
        with res["engine"].connect() as conn:
            df = pd.read_sql(query, conn, params={"val": id_obra.upper()})

        if df.empty:
            await update.message.reply_text(get_text(lang, "not_found"))
            return

        # Predição de Risco
        X = df.reindex(columns=res["features"], fill_value=0)
        prediction = res["pipeline"].predict(X)
        risco_val = float(prediction[0])
        status = "🟢 NORMAL" if risco_val <= 7 else "🟡 ALERTA" if risco_val <= 10 else "🔴 CRÍTICO"

        # Resposta em texto
        await update.message.reply_text(
            f"🏗️ *Relatório IA: {id_obra}*\nStatus: {status}\nImpacto: {risco_val:.1f} dias",
            parse_mode=ParseMode.MARKDOWN
        )

    except Exception as e:
        logging.error(f"Erro na análise: {e}")
        await update.message.reply_text("⚠️ Erro interno no processamento.")
