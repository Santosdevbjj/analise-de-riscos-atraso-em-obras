import os
import logging
import asyncio
import threading
import io
import pytz
from datetime import datetime

# --- CONFIGURAÇÃO GRÁFICA PARA SERVIDOR ---
import matplotlib
matplotlib.use("Agg") 
import matplotlib.pyplot as plt

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

from fastapi import FastAPI
from telegram import Update, InputFile
from telegram.ext import Application, CommandHandler, ContextTypes
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base

# 1. Logging e Configurações
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
RAW_DB_URL = os.environ.get("DATABASE_URL")
BR_TIMEZONE = pytz.timezone('America/Sao_Paulo')

# 2. Conexão Otimizada para Transaction Pooler (Porta 6543)
def get_modern_engine(url):
    try:
        if not url:
            raise ValueError("DATABASE_URL não encontrada!")
        
        # Ajuste do dialeto para Psycopg 3
        if url.startswith("postgres://"):
            new_url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            new_url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        else:
            new_url = url

        logger.info("🔌 Conectando via Supabase Transaction Pooler (IPv4 Mode)...")
        
        return create_engine(
            new_url,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                # OBRIGATÓRIO para o modo Transaction do Supabase:
                "prepare_threshold": None, 
                "gssencmode": "disable",
                "connect_timeout": 20
            }
        )
    except Exception as e:
        logger.error(f"💥 Erro crítico no Engine: {e}")
        raise e

engine = get_modern_engine(RAW_DB_URL)
Base = declarative_base()

# 3. Geradores de Mídia
def gerar_grafico(risco_valor, id_obra):
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(8, 4))
    cor = 'green' if risco_valor <= 7 else 'orange' if risco_valor <= 10 else 'red'
    ax.barh(['Risco Estimado'], [risco_valor], color=cor)
    ax.set_xlim(0, 15)
    ax.set_title(f"Análise de Risco IA: {id_obra}")
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

# 4. Handlers do Telegram (Padronizados para UPPER)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏗️ **CCBJJ Intelligence Ativo**\nUse `/analise [ID]`")

async def analise_preditiva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Informe o ID da obra. Ex: `/analise CCBJJ-101`")
        return
    
    id_obra_input = context.args[0].upper()
    logger.info(f"🔍 Buscando obra: {id_obra_input}")

    try:
        # Busca padronizada em UPPER
        query = text('SELECT risco_etapa FROM view_analise_preditiva WHERE UPPER(id_obra) = :id LIMIT 1')
        
        with engine.connect() as conn:
            result = conn.execute(query, {"id": id_obra_input}).fetchone()

        if result:
            risco = float(result[0]) if result[0] is not None else 0.0
            status = "🟢 OK" if risco <= 7 else "🟡 ALERTA" if risco <= 10 else "🔴 CRÍTICO"
            
            await update.message.reply_text(f"📊 Processando dados para {id_obra_input}...")
            
            graf = gerar_grafico(risco, id_obra_input)
            pdf = gerar_pdf(id_obra_input, risco, status, graf)
            
            graf.seek(0)
            await update.message.reply_photo(photo=graf, caption=f"Status: {status}")
            
            pdf.seek(0)
            await update.message.reply_document(
                document=InputFile(pdf, filename=f"Relatorio_{id_obra_input}.pdf"),
                caption=f"Relatório de {id_obra_input} finalizado."
            )
        else:
            await update.message.reply_text(f"❌ A obra `{id_obra_input}` não foi encontrada.")

    except Exception as e:
        logger.error(f"💥 ERRO: {str(e)}")
        await update.message.reply_text(f"⚠️ Erro técnico no banco. Verifique os logs.")

# 5. FastAPI e Ciclo de Vida do Bot
app = FastAPI()
ptb = Application.builder().token(TOKEN).build()
ptb.add_handler(CommandHandler("start", start))
ptb.add_handler(CommandHandler("analise", analise_preditiva))

async def run_telegram_bot():
    try:
        await ptb.initialize()
        await ptb.start()
        await ptb.updater.start_polling()
        while True: await asyncio.sleep(3600)
    except Exception as e:
        logger.error(f"Erro Bot: {e}")

@app.on_event("startup")
async def on_startup():
    threading.Thread(target=lambda: asyncio.run(run_telegram_bot()), daemon=True).start()

@app.get("/")
async def health_check():
    return {"status": "online", "connection": "transaction_pooler_ipv4"}
