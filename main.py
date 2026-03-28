import os
import logging
import asyncio
import threading
import urllib.parse
import io
import pytz
from datetime import datetime

# Bibliotecas para Gráficos e PDF
import matplotlib
matplotlib.use("Agg") # Necessário para rodar em servidores sem monitor
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

from fastapi import FastAPI
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes
from sqlalchemy import create_engine, Column, BigInteger, String, Text, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func

# 1. Logging e Configurações
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
RAW_DB_URL = os.environ.get("DATABASE_URL")
BR_TIMEZONE = pytz.timezone('America/Sao_Paulo')

# 2. Tratamento de Conexão com Supabase (Driver pg8000)
def get_sanitized_engine(url):
    try:
        if not url: raise ValueError("DATABASE_URL ausente!")
        if "postgresql+pg8000" not in url:
            url = url.replace("postgres://", "postgresql://")
            result = urllib.parse.urlparse(url)
            password = urllib.parse.quote_plus(result.password) if result.password else ""
            url = f"postgresql+pg8000://{result.username}:{password}@{result.hostname}:{result.port or 5432}{result.path}"
        
        return create_engine(url, connect_args={"ssl_context": True}, pool_pre_ping=True)
    except Exception as e:
        logger.error(f"Erro no Engine: {e}")
        return create_engine(url.replace("postgres://", "postgresql://"))

engine = get_sanitized_engine(RAW_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. Modelo de Log
class RegistroObra(Base):
    __tablename__ = "registros_obras"
    id = Column(BigInteger, primary_key=True, index=True)
    telegram_id = Column(BigInteger)
    usuario = Column(String(255))
    descricao = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

Base.metadata.create_all(bind=engine)

# 4. Geradores de Mídia (Integrado do telegram_bot.py)
def gerar_grafico(risco_valor, id_obra):
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(8, 4))
    cor = 'green' if risco_valor <= 7 else 'orange' if risco_valor <= 10 else 'red'
    ax.barh(['Risco Estimado'], [risco_valor], color=cor)
    ax.set_xlim(0, 15)
    ax.set_title(f"Análise de Risco: {id_obra}")
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    return buf

def gerar_pdf(id_obra, risco, status, graf_buf):
    pdf_buf = io.BytesIO()
    c = canvas.Canvas(pdf_buf, pagesize=A4)
    width, height = A4
    now = datetime.now(BR_TIMEZONE).strftime('%d/%m/%Y %H:%M')

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 3*cm, "RELATÓRIO TÉCNICO CCBJJ ENGENHARIA")
    c.setFont("Helvetica", 12)
    c.drawString(2*cm, height - 5*cm, f"ID da Obra: {id_obra}")
    c.drawString(2*cm, height - 5.6*cm, f"Data da Análise: {now}")
    c.drawString(2*cm, height - 6.2*cm, f"Status: {status}")
    c.drawString(2*cm, height - 6.8*cm, f"Impacto Predito: {risco:.1f} dias")
    
    graf_buf.seek(0)
    img = ImageReader(graf_buf)
    c.drawImage(img, 2*cm, height - 15*cm, width=17*cm, preserveAspectRatio=True)
    
    c.showPage()
    c.save()
    pdf_buf.seek(0)
    return pdf_buf

# 5. Handlers do Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏗️ **CCBJJ Intelligence Ativo**\nUse `/analise [ID]` para relatórios completos.")

async def analise_preditiva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Informe o ID da obra.")
        return

    id_obra = context.args[0].upper()
    query = text('SELECT * FROM view_analise_preditiva WHERE id_obra = :id LIMIT 1')
    
    with engine.connect() as conn:
        res = conn.execute(query, {"id": id_obra}).fetchone()

    if res:
        risco = getattr(res, 'risco_etapa', 0)
        status = "🟢 OK" if risco <= 7 else "🟡 ALERTA" if risco <= 10 else "🔴 CRÍTICO"
        
        # Enviar Texto
        await update.message.reply_text(f"📊 Análise iniciada para {id_obra}...")
        
        # Gerar e Enviar Gráfico
        graf = gerar_grafico(risco, id_obra)
        await update.message.reply_photo(photo=graf, caption=f"Status: {status}")
        
        # Gerar e Enviar PDF
        pdf = gerar_pdf(id_obra, risco, status, graf)
        await update.message.reply_document(
            document=InputFile(pdf, filename=f"Relatorio_{id_obra}.pdf"),
            caption="Segue o relatório executivo detalhado."
        )
    else:
        await update.message.reply_text("❌ Obra não encontrada.")

# 6. Ciclo de Vida e FastAPI
app = FastAPI()
ptb = Application.builder().token(TOKEN).build()
ptb.add_handler(CommandHandler("start", start))
ptb.add_handler(CommandHandler("analise", analise_preditiva))

async def run_bot():
    await ptb.initialize()
    await ptb.start()
    await ptb.updater.start_polling()
    while True: await asyncio.sleep(3600)

@app.on_event("startup")
async def startup():
    threading.Thread(target=lambda: asyncio.run(run_bot()), daemon=True).start()

@app.get("/")
async def health(): return {"status": "active"}
