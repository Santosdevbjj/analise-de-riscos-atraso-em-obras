import os
import logging
import urllib.parse
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from sqlalchemy import create_engine, Column, BigInteger, String, Text, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import func

# 1. Logging e Configurações
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
RAW_DB_URL = os.environ.get("DATABASE_URL")

# 2. Tratamento Robusto de Conexão (Segurança do Arquivo Antigo)
def get_sanitized_engine(url):
    try:
        if not url: raise ValueError("DATABASE_URL ausente!")
        if "postgresql+pg8000" not in url:
            result = urllib.parse.urlparse(url)
            password = urllib.parse.quote_plus(result.password) if result.password else ""
            url = f"postgresql+pg8000://{result.username}:{password}@{result.hostname}:{result.port}{result.path}"
        
        return create_engine(url, connect_args={"ssl_context": True, "timeout": 30}, pool_pre_ping=True)
    except Exception as e:
        logger.error(f"Erro no Engine: {e}")
        return create_engine(url.replace("postgres://", "postgresql://"))

engine = get_sanitized_engine(RAW_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. Modelo de Log (Mantendo o histórico de uso do Bot)
class RegistroObra(Base):
    __tablename__ = "registros_obras"
    id = Column(BigInteger, primary_key=True)
    telegram_id = Column(BigInteger)
    usuario = Column(String(255))
    descricao = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

Base.metadata.create_all(bind=engine)

# 4. Funções de Inteligência de Dados
def buscar_analise_preditiva(id_obra: str):
    query = text('SELECT * FROM view_analise_preditiva WHERE id_obra = :id LIMIT 1')
    with engine.connect() as conn:
        return conn.execute(query, {"id": id_obra}).fetchone()

# 5. Handlers do Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        f"Olá {update.effective_user.first_name}! 🏗️\n"
        "Sistema de Inteligência CCBJJ (300k registros) Ativo.\n\n"
        "Comandos:\n"
        "1️⃣ `/analise [ID]` - Ex: `/analise CCBJJ-100` (Predição de risco)\n"
        "2️⃣ `/obra [txt]` - Registrar nota rápida no banco"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def analise_preditiva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Informe o ID. Ex: `/analise CCBJJ-100`")
        return

    id_obra = context.args[0].upper()
    res = buscar_analise_preditiva(id_obra)

    if res:
        status_cor = "🔴 CRÍTICO" if res.risco_etapa > 7 else "🟢 OK"
        relatorio = (
            f"📊 *DATA INSIGHT: {res.id_obra}*\n"
            f"📍 {res.cidade.title()} | Etapa: {res.etapa}\n"
            f"----------------------------\n"
            f"🌡️ *Risco Predito:* `{res.risco_etapa:.1f} dias` ({status_cor})\n"
            f"💰 Orçamento: R$ {res.orcamento_estimado:,.2f}\n"
            f"👷 Equipe: {res.qtd_engenheiros} Eng / {res.qtd_pedreiros} Ped\n"
            f"📉 Taxa Insucesso Forn: {res.taxa_insucesso_fornecedor:.1%}"
        )
        await update.message.reply_text(relatorio, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ ID `{id_obra}` não localizado.")

async def registrar_nota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = " ".join(context.args)
    if not desc:
        await update.message.reply_text("Digite a descrição. Ex: `/obra Verificar cimento`")
        return
    
    with SessionLocal() as db:
        db.add(RegistroObra(telegram_id=update.effective_user.id, usuario=update.effective_user.first_name, descricao=desc))
        db.commit()
    await update.message.reply_text("✅ Nota registrada nos logs do sistema.")

# 6. FastAPI Webhook Setup
app = FastAPI()
ptb = Application.builder().token(TOKEN).build()
ptb.add_handler(CommandHandler("start", start))
ptb.add_handler(CommandHandler("analise", analise_preditiva))
ptb.add_handler(CommandHandler("obra", registrar_nota))

@app.post("/webhook")
async def handle_webhook(request: Request):
    data = await request.json()
    async with ptb:
        update = Update.de_json(data, ptb.bot)
        await ptb.process_update(update)
    return {"status": "ok"}

@app.get("/")
async def health():
    return {"status": "online", "engine": "hybrid_active"}
