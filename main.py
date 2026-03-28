import os
import logging
import asyncio
import threading
import io
import pytz
from datetime import datetime

# --- CONFIGURAÇÃO GRÁFICA PARA SERVIDOR ---
import matplotlib
matplotlib.use("Agg") # Impede erro de interface gráfica no Render
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

# 2. Conexão com Psycopg 3 e SQLAlchemy 2.0
def get_modern_engine(url):
    try:
        if not url:
            raise ValueError("DATABASE_URL não configurada nas variáveis de ambiente!")
        
        # Ajuste para Psycopg 3 (Dialeto: postgresql+psycopg://)
        # O SQLAlchemy 2.0 usa 'psycopg' para se referir à versão 3 do driver
        if url.startswith("postgres://"):
            new_url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            new_url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        else:
            new_url = url

        logger.info("Conectando ao banco com Psycopg 3...")
        return create_engine(
            new_url,
            pool_pre_ping=True,
            echo=False
        )
    except Exception as e:
        logger.error(f"Erro crítico ao configurar Engine: {e}")
        raise e

engine = get_modern_engine(RAW_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. Modelo de Log (SQLAlchemy 2.0 Style)
class RegistroObra(Base):
    __tablename__ = "registros_obras"
    id = Column(BigInteger, primary_key=True, index=True)
    telegram_id = Column(BigInteger)
    usuario = Column(String(255))
    descricao = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Garantir criação das tabelas
Base.metadata.create_all(bind=engine)

# 4. Geradores de Mídia
def gerar_grafico(risco_valor, id_obra):
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Lógica de cores baseada no risco
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
    
    # Inserir Gráfico no PDF
    graf_buf.seek(0)
    img = ImageReader(graf_buf)
    c.drawImage(img, 2*cm, height - 15*cm, width=17*cm, preserveAspectRatio=True)
    
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width/2, 2*cm, "Documento gerado automaticamente pelo Sistema de Inteligência CCBJJ.")
    
    c.showPage()
    c.save()
    pdf_buf.seek(0)
    return pdf_buf

# 5. Handlers do Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏗️ **CCBJJ Intelligence Ativo (v2026)**\n\n"
        "Conectado com Psycopg 3 e SQLAlchemy 2.0.\n"
        "Use `/analise [ID]` para gerar o relatório executivo."
    )

async def analise_preditiva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Por favor, informe o ID. Ex: `/analise CCBJJ-100`")
        return

    id_obra = context.args[0].upper()
    
    try:
        # Consulta usando SQLAlchemy 2.0 (text + bindparams)
        query = text('SELECT * FROM view_analise_preditiva WHERE id_obra = :id LIMIT 1')
        
        with engine.connect() as conn:
            result = conn.execute(query, {"id": id_obra}).fetchone()

        if result:
            # Pegando dados de forma segura
            risco = getattr(result, 'risco_etapa', 0)
            status = "🟢 OK" if risco <= 7 else "🟡 ALERTA" if risco <= 10 else "🔴 CRÍTICO"
            
            await update.message.reply_text(f"📊 Processando dados da obra {id_obra}...")
            
            # 1. Gráfico
            graf = gerar_grafico(risco, id_obra)
            
            # 2. PDF (Usa o mesmo buffer do gráfico para eficiência)
            pdf = gerar_pdf(id_obra, risco, status, graf)
            
            # Enviar Foto
            graf.seek(0)
            await update.message.reply_photo(photo=graf, caption=f"Resumo Visual: {status}")
            
            # Enviar PDF
            pdf.seek(0)
            await update.message.reply_document(
                document=InputFile(pdf, filename=f"Relatorio_{id_obra}.pdf"),
                caption="Relatório Executivo Completo (PDF)."
            )
        else:
            await update.message.reply_text(f"❌ ID `{id_obra}` não localizado no banco de dados.")

    except Exception as e:
        logger.error(f"Erro na análise: {e}")
        await update.message.reply_text("⚠️ Erro interno ao processar a análise.")

# 6. FastAPI e Inicialização do Bot
app = FastAPI()

# Inicialização assíncrona do Bot para não travar o Render
ptb = Application.builder().token(TOKEN).build()
ptb.add_handler(CommandHandler("start", start))
ptb.add_handler(CommandHandler("analise", analise_preditiva))

async def run_telegram_bot():
    try:
        await ptb.initialize()
        await ptb.start()
        await ptb.updater.start_polling()
        logger.info("🤖 Bot do Telegram iniciado em modo Polling.")
        while True:
            await asyncio.sleep(3600)
    except Exception as e:
        logger.error(f"Falha ao iniciar o Bot: {e}")

@app.on_event("startup")
async def on_startup():
    # Roda o bot em uma thread separada para o FastAPI liberar a porta $PORT imediatamente
    threading.Thread(target=lambda: asyncio.run(run_telegram_bot()), daemon=True).start()

@app.get("/")
async def health_check():
    return {
        "status": "online",
        "engine": "SQLAlchemy 2.0.48",
        "driver": "Psycopg 3.3.3",
        "timezone": "America/Sao_Paulo"
    }
