import os
import logging
import asyncio
import threading
import io
import pytz
import socket
from datetime import datetime
from urllib.parse import urlparse

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
from sqlalchemy import create_engine, Column, BigInteger, String, Text, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func

# 1. Logging e Configurações
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
RAW_DB_URL = os.environ.get("DATABASE_URL")
BR_TIMEZONE = pytz.timezone('America/Sao_Paulo')

# 2. Conexão Blindada (Forçando IPv4 para Render/Supabase)
def get_modern_engine(url):
    try:
        if not url:
            raise ValueError("DATABASE_URL não encontrada nas variáveis de ambiente!")
        
        # Ajuste do dialeto para Psycopg 3
        if url.startswith("postgres://"):
            new_url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://"):
            new_url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        else:
            new_url = url

        # Extração do host para forçar resolução IPv4
        parsed = urlparse(url)
        try:
            ipv4_address = socket.gethostbyname(parsed.hostname)
            logger.info(f"🌐 Host {parsed.hostname} resolvido para IPv4: {ipv4_address}")
        except Exception as e:
            ipv4_address = None
            logger.warning(f"⚠️ Não foi possível resolver o IP manualmente: {e}")

        logger.info("🔌 Conectando ao banco com Psycopg 3 (Modo IPv4 Forced)...")
        
        return create_engine(
            new_url,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                "prepare_threshold": None,
                "gssencmode": "disable",
                "connect_timeout": 20,
                # Força o hostaddr para o IP resolvido se disponível para evitar IPv6
                "hostaddr": ipv4_address if ipv4_address else None
            }
        )
    except Exception as e:
        logger.error(f"💥 Erro crítico ao configurar o Engine: {e}")
        raise e

engine = get_modern_engine(RAW_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. Modelo de Log (Auditoria)
class RegistroObra(Base):
    __tablename__ = "registros_obras"
    id = Column(BigInteger, primary_key=True, index=True)
    telegram_id = Column(BigInteger)
    usuario = Column(String(255))
    descricao = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# 4. Geradores de Mídia
def gerar_grafico(risco_valor, id_obra):
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Lógica de cores baseada nos níveis de risco
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

# 5. Handlers do Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏗️ **CCBJJ Intelligence Ativa**\n\nSistema de monitoramento preditivo online.\nUse `/analise [ID]` para consultar sua obra.")

async def analise_preditiva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Informe o ID da obra. Ex: `/analise CCBJJ-101`")
        return
    
    # PADRONIZAÇÃO: Tudo para Maiúsculo no input do usuário
    id_obra_input = context.args[0].upper()
    logger.info(f"🔍 Iniciando busca padronizada para: {id_obra_input}")

    try:
        # SQL com UPPER no banco para garantir compatibilidade total
        query = text('SELECT risco_etapa FROM view_analise_preditiva WHERE UPPER(id_obra) = :id LIMIT 1')
        
        with engine.connect() as conn:
            result = conn.execute(query, {"id": id_obra_input}).fetchone()
            logger.info(f"✅ Resultado da consulta: {result}")

        if result:
            risco = float(result[0]) if result[0] is not None else 0.0
            status = "🟢 OK" if risco <= 7 else "🟡 ALERTA" if risco <= 10 else "🔴 CRÍTICO"
            
            await update.message.reply_text(f"📊 Processando relatório de IA para {id_obra_input}...")
            
            # Gerar mídias em memória
            graf = gerar_grafico(risco, id_obra_input)
            pdf = gerar_pdf(id_obra_input, risco, status, graf)
            
            # Enviar Foto/Gráfico
            graf.seek(0)
            await update.message.reply_photo(photo=graf, caption=f"Status: {status}")
            
            # Enviar Arquivo PDF
            pdf.seek(0)
            await update.message.reply_document(
                document=InputFile(pdf, filename=f"Relatorio_{id_obra_input}.pdf"),
                caption=f"Segue anexo o Relatório Técnico de {id_obra_input}."
            )
        else:
            logger.warning(f"❓ Obra {id_obra_input} não localizada.")
            await update.message.reply_text(f"❌ A obra `{id_obra_input}` não consta na nossa base de dados preditiva.")

    except Exception as e:
        logger.error(f"💥 Erro na execução da análise: {str(e)}")
        # Envia uma mensagem técnica simplificada para o usuário para ajudar no debug
        erro_limpo = str(e).split(']')[1] if ']' in str(e) else str(e)[:100]
        await update.message.reply_text(f"⚠️ Erro de Conexão:\n`{erro_limpo[:100]}`")

# 6. Inicialização e FastAPI
app = FastAPI()
ptb = Application.builder().token(TOKEN).build()
ptb.add_handler(CommandHandler("start", start))
ptb.add_handler(CommandHandler("analise", analise_preditiva))

async def run_telegram_bot():
    try:
        # Tenta criar tabelas de log se não existirem
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("📂 Banco de dados sincronizado.")
        except Exception as e_db:
            logger.warning(f"Aviso na inicialização do DB: {e_db}")
            
        await ptb.initialize()
        await ptb.start()
        await ptb.updater.start_polling()
        while True: await asyncio.sleep(3600)
    except Exception as e:
        logger.error(f"❌ Falha fatal no Bot: {e}")

@app.on_event("startup")
async def on_startup():
    # Rodar o bot em uma thread separada para não travar a FastAPI
    threading.Thread(target=lambda: asyncio.run(run_telegram_bot()), daemon=True).start()

@app.get("/")
async def health_check():
    return {
        "status": "online", 
        "engine": "SQLAlchemy 2.0.48",
        "ipv4_forced": True,
        "search_mode": "UPPER_CASE_ONLY"
    }
