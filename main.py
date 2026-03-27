import os
import logging
import urllib.parse
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application
from sqlalchemy import create_engine, Column, BigInteger, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Configurações de Log para o Render
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 2. Variáveis de Ambiente
TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
RAW_DB_URL = os.environ.get("DATABASE_URL")

# 3. TRATAMENTO AUTOMÁTICO DA URL E SENHA
def get_sanitized_engine(url):
    try:
        # Separa os componentes da URL para tratar a senha isoladamente
        result = urllib.parse.urlparse(url)
        username = result.username
        password = urllib.parse.quote_plus(result.password) if result.password else ""
        hostname = result.hostname
        port = result.port
        database = result.path.lstrip('/')
        
        # Reconstrói a URL de forma segura para o SQLAlchemy
        safe_url = f"postgresql+pg8000://{username}:{password}@{hostname}:{port}/{database}"
        
        # Cria o engine com suporte a SSL (obrigatório Supabase) e timeout
        return create_engine(
            safe_url,
            connect_args={
                "ssl_context": True,
                "timeout": 30
            },
            pool_pre_ping=True # Testa a conexão antes de usar
        )
    except Exception as e:
        logger.error(f"Erro ao processar DATABASE_URL: {e}")
        return create_engine(url) # Fallback para a URL original

engine = get_sanitized_engine(RAW_DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 4. Modelo do Banco de Dados
class RegistroObra(Base):
    __tablename__ = "registros_obras"
    id = Column(BigInteger, primary_key=True, index=True)
    telegram_id = Column(BigInteger)
    usuario = Column(String(255))
    descricao = Column(Text)
    status = Column(String(50), default="Pendente")

# Cria a tabela se ela não existir
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Tabelas verificadas/criadas com sucesso no Supabase.")
except Exception as e:
    logger.error(f"Erro ao criar tabelas: {e}")

# 5. Inicialização do FastAPI e Bot
app = FastAPI()
ptb_app = Application.builder().token(TOKEN).build()

@app.on_event("startup")
async def setup_webhook():
    if WEBHOOK_URL:
        # Garante que a URL do webhook esteja correta
        url = f"{WEBHOOK_URL.rstrip('/')}/webhook"
        await ptb_app.bot.set_webhook(url=url)
        logger.info(f"Webhook configurado para: {url}")
    else:
        logger.warning("WEBHOOK_URL não configurada no painel do Render.")

@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, ptb_app.bot)

        if update.message and update.message.text:
            text = update.message.text
            user = update.message.from_user

            if text == "/start":
                await update.message.reply_text(
                    f"Olá {user.first_name}! 🏗️\nEstou pronto para analisar riscos de atraso.\n\n"
                    "Use o comando: `/obra [descrição da obra]`"
                )

            elif text.startswith("/obra"):
                desc = text.replace("/obra", "").strip()
                if desc:
                    # Persistência no Banco de Dados
                    with SessionLocal() as db:
                        nova_obra = RegistroObra(
                            telegram_id=user.id,
                            usuario=user.first_name,
                            descricao=desc
                        )
                        db.add(nova_obra)
                        db.commit()
                    await update.message.reply_text("✅ Obra registrada no banco do Supabase para análise!")
                else:
                    await update.message.reply_text("⚠️ Por favor, informe a descrição da obra após o comando.")

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erro no processamento do webhook: {e}")
        return {"status": "error"}

@app.get("/")
def health():
    return {"status": "online", "database": "connected"}
