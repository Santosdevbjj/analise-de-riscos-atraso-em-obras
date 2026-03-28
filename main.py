import os
import logging
import asyncio
import threading
import urllib.parse
from fastapi import FastAPI
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

# 2. Tratamento de Conexão com Supabase (Corrigido para pg8000)
def get_sanitized_engine(url):
    try:
        if not url: raise ValueError("DATABASE_URL ausente!")
        # Se a URL vier do Supabase (postgres://), ajustamos para o driver pg8000
        if "postgresql+pg8000" not in url:
            # Remove o prefixo antigo se existir
            url = url.replace("postgres://", "postgresql://")
            result = urllib.parse.urlparse(url)
            username = result.username
            password = urllib.parse.quote_plus(result.password) if result.password else ""
            hostname = result.hostname
            port = result.port or 5432
            database = result.path.lstrip('/')
            
            url = f"postgresql+pg8000://{username}:{password}@{hostname}:{port}/{database}"
        
        return create_engine(
            url, 
            connect_args={"ssl_context": True}, 
            pool_pre_ping=True,
            pool_recycle=300
        )
    except Exception as e:
        logger.error(f"Erro ao configurar Engine: {e}")
        # Fallback simples caso o sanitize falhe
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

# Cria a tabela se não existir
Base.metadata.create_all(bind=engine)

# 4. Funções de Dados
def buscar_analise_preditiva(id_obra: str):
    query = text('SELECT * FROM view_analise_preditiva WHERE id_obra = :id LIMIT 1')
    try:
        with engine.connect() as conn:
            result = conn.execute(query, {"id": id_obra}).fetchone()
            return result
    except Exception as e:
        logger.error(f"Erro na query: {e}")
        return None

# 5. Handlers do Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        f"Olá {update.effective_user.first_name}! 🏗️\n"
        "Sistema de Inteligência CCBJJ Conectado ao Supabase.\n\n"
        "Comandos:\n"
        "1️⃣ `/analise [ID]` - Ex: `/analise CCBJJ-100`\n"
        "2️⃣ `/obra [texto]` - Registrar nota no banco"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def analise_preditiva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Informe o ID. Ex: `/analise CCBJJ-100`")
        return

    id_obra = context.args[0].upper()
    res = buscar_analise_preditiva(id_obra)

    if res:
        # Ajuste os nomes das colunas conforme sua View no Supabase
        risco = getattr(res, 'risco_etapa', 0)
        status_cor = "🔴 CRÍTICO" if risco > 7 else "🟢 OK"
        
        relatorio = (
            f"📊 *DATA INSIGHT: {id_obra}*\n"
            f"📍 {getattr(res, 'cidade', 'N/A').title()} | Etapa: {getattr(res, 'etapa', 'N/A')}\n"
            f"----------------------------\n"
            f"🌡️ *Risco Predito:* `{risco:.1f} dias` ({status_cor})\n"
            f"💰 Orçamento: R$ {getattr(res, 'orcamento_estimado', 0):,.2f}\n"
            f"📉 Taxa Insucesso Forn: {getattr(res, 'taxa_insucesso_fornecedor', 0):.1%}"
        )
        await update.message.reply_text(relatorio, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ ID `{id_obra}` não localizado no banco.")

async def registrar_nota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    desc = " ".join(context.args)
    if not desc:
        await update.message.reply_text("Digite a descrição. Ex: `/obra Material entregue`")
        return
    
    try:
        with SessionLocal() as db:
            nova_nota = RegistroObra(
                telegram_id=update.effective_user.id, 
                usuario=update.effective_user.first_name, 
                descricao=desc
            )
            db.add(nova_nota)
            db.commit()
        await update.message.reply_text("✅ Nota registrada com sucesso.")
    except Exception as e:
        await update.message.reply_text("❌ Erro ao salvar no banco.")
        logger.error(f"Erro ao salvar nota: {e}")

# 6. Configuração FastAPI e Ciclo de Vida do Bot
app = FastAPI()

# Criamos a aplicação do Bot globalmente
ptb = Application.builder().token(TOKEN).build()
ptb.add_handler(CommandHandler("start", start))
ptb.add_handler(CommandHandler("analise", analise_preditiva))
ptb.add_handler(CommandHandler("obra", registrar_nota))

async def run_telegram_polling():
    """Inicia o bot em modo polling"""
    await ptb.initialize()
    await ptb.start()
    await ptb.updater.start_polling()
    logger.info("Bot do Telegram iniciado em modo Polling.")
    
    # Mantém o loop rodando
    while True:
        await asyncio.sleep(3600)

@app.on_event("startup")
async def startup_event():
    """Executa quando o FastAPI inicia (O Render detecta a porta aqui)"""
    # Roda o Bot em uma Thread separada para não travar a porta 10000
    threading.Thread(target=lambda: asyncio.run(run_telegram_polling()), daemon=True).start()

@app.get("/")
async def health():
    return {"status": "online", "message": "Servidor Web e Bot ativos"}
