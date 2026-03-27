import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application
from sqlalchemy import create_engine, Column, BigInteger, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Configurações de Log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 2. Variáveis de Ambiente
TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
DB_URL = os.environ.get("DATABASE_URL")

# 3. Configuração do Banco de Dados (Postgres Supabase)
# O driver pg8000 é ótimo para ambientes serverless/cloud
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class RegistroObra(Base):
    __tablename__ = "registros_obras"
    id = Column(BigInteger, primary_key=True, index=True)
    telegram_id = Column(BigInteger)
    usuario = Column(String(255))
    descricao = Column(Text)
    status = Column(String(50), default="Pendente")

# Cria a tabela se ela não existir
Base.metadata.create_all(bind=engine)

# 4. Inicialização do App e Bot
app = FastAPI()
ptb_app = Application.builder().token(TOKEN).build()

@app.on_event("startup")
async def setup_webhook():
    if WEBHOOK_URL:
        url = f"{WEBHOOK_URL.rstrip('/')}/webhook"
        await ptb_app.bot.set_webhook(url=url)
        logger.info(f"BOT: Webhook configurado em {url}")

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
                    f"Olá {user.first_name}! 🏗️\nEnvie `/obra [descrição]` para registrar um risco."
                )

            elif text.startswith("/obra"):
                desc = text.replace("/obra", "").strip()
                if desc:
                    # Salvando via SQLAlchemy
                    db = SessionLocal()
                    nova_obra = RegistroObra(
                        telegram_id=user.id,
                        usuario=user.first_name,
                        descricao=desc
                    )
                    db.add(nova_obra)
                    db.commit()
                    db.close()
                    await update.message.reply_text("✅ Obra registrada no Supabase!")
                else:
                    await update.message.reply_text("Diga-me o nome da obra após o comando.")

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"ERRO: {e}")
        return {"status": "error"}

@app.get("/")
def health():
    return {"status": "online", "db": "connected"}
