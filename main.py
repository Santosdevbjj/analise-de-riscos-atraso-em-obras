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
from sqlalchemy import create_engine, Column, BigInteger, String, Text, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func

# 1. Logging e Configurações
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
RAW_DB_URL = os.environ.get("DATABASE_URL")
BR_TIMEZONE = pytz.timezone('America/Sao_Paulo')

# 2. Conexão com Psycopg 3 e SQLAlchemy 2.0 (AJUSTADO PARA RENDER/IPV4)
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

        logger.info("Conectando ao banco com Psycopg 3 (Modo Compatibilidade Render/IPv4)...")
        
        return create_engine(
            new_url,
            pool_pre_ping=True,
            echo=False,
            # Força o uso de IPv4 e desabilita modos que podem causar timeout no Render
            connect_args={
                "prepare_threshold": None,
                "gssencmode": "disable"
            }
        )
    except Exception as e:
        logger.error(f"Erro crítico no Engine: {e}")
        raise e

engine = get_modern_engine(RAW_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. Modelo de Log (Tabela de Auditoria)
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
    
    # Lógica de cores baseada na sua tabela do Supabase
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

# 5. Handlers do Telegram (Blindado com Super Logs)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏗️ **CCBJJ Intelligence Ativo**\nUse `/analise [ID]` para consultar sua obra.")

async def analise_preditiva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Informe o ID da obra. Ex: `/analise CCBJJ-100`")
        return
    
    # Padronizamos para maiúsculas para facilitar a busca
    id_obra_input = context.args[0].upper()
    logger.info(f"🔍 Buscando obra: {id_obra_input}")

    try:
        # Consulta padronizada em UPPER no banco para ignorar case sensitivity
        query = text('SELECT risco_etapa FROM view_analise_preditiva WHERE UPPER(id_obra) = :id LIMIT 1')
        
        with engine.connect() as conn:
            result = conn.execute(query, {"id": id_obra_input}).fetchone()
            logger.info(f"✅ Resposta do banco para {id_obra_input}: {result}")

        if result:
            # result[0] acessa o valor de risco_etapa
            risco = float(result[0]) if result[0] is not None else 0.0
            status = "🟢 OK" if risco <= 7 else "🟡 ALERTA" if risco <= 10 else "🔴 CRÍTICO"
            
            await update.message.reply_text(f"📊 Processando dados para {id_obra_input}...")
            
            # Gerar mídias
            graf = gerar_grafico(risco, id_obra_input)
            pdf = gerar_pdf(id_obra_input, risco, status, graf)
            
            # Enviar Foto
            graf.seek(0)
            await update.message.reply_photo(photo=graf, caption=f"Status: {status}")
            
            # Enviar PDF
            pdf.seek(0)
            await update.message.reply_document(
                document=InputFile(pdf, filename=f"Relatorio_{id_obra_input}.pdf"),
                caption=f"Segue o relatório executivo da obra {id_obra_input}."
            )
        else:
            logger.warning(f"❓ Obra {id_obra_input} não encontrada.")
            await update.message.reply_text(f"❌ A obra `{id_obra_input}` não foi encontrada no banco de dados.")

    except Exception as e:
        # LOG DETALHADO NO RENDER
        logger.error(f"💥 ERRO CRÍTICO NO BANCO: {str(e)}")
        # Resposta amigável para o usuário com o início do erro técnico
        erro_msg = str(e)[:100]
        await update.message.reply_text(f"⚠️ Erro ao acessar banco de dados:\n`{erro_msg}`")

# 6. Ciclo de Vida e FastAPI
app = FastAPI()
ptb = Application.builder().token(TOKEN).build()
ptb.add_handler(CommandHandler("start", start))
ptb.add_handler(CommandHandler("analise", analise_preditiva))

async def run_telegram_bot():
    try:
        # Garante as tabelas de log em segundo plano
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Tabelas de auditoria verificadas/criadas.")
        except Exception as e_db:
            logger.warning(f"Aviso na criação de tabelas: {e_db}")
            
        await ptb.initialize()
        await ptb.start()
        await ptb.updater.start_polling()
        while True: await asyncio.sleep(3600)
    except Exception as e:
        logger.error(f"Erro fatal no ciclo do Bot: {e}")

@app.on_event("startup")
async def on_startup():
    threading.Thread(target=lambda: asyncio.run(run_telegram_bot()), daemon=True).start()

@app.get("/")
async def health_check():
    return {
        "status": "online", 
        "engine": "SQLAlchemy 2.0.48",
        "driver": "Psycopg 3.3.3",
        "database_search": "UPPER_CASE_STANDARDIZED"
    }
