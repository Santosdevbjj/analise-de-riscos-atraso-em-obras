import os
import logging
import asyncio
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from scripts.telegram_bot import processar_analise

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis de Ambiente
TOKEN = os.getenv("TELEGRAM_TOKEN")
RENDER_URL = "https://analiseriscosatrasoobras.onrender.com"

app = FastAPI()
tg_app = Application.builder().token(TOKEN).build()

# Handlers de Comandos
async def start(update: Update, context):
    await update.message.reply_text("🏗️ *CCBJJ Bot Online*\nEnvie o ID da obra (ex: CCBJJ-123).")

async def handle_message(update: Update, context):
    id_obra = update.message.text.strip()
    if id_obra:
        await processar_analise(update, context, id_obra)

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Rota de Webhook (Recebe dados do Telegram)
@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, tg_app.bot)
        await tg_app.process_update(update)
    except Exception as e:
        logger.error(f"Erro no Webhook: {e}")
    return {"status": "ok"}

# Inicialização Automática do Webhook
@app.on_event("startup")
async def startup_event():
    await tg_app.initialize()
    await tg_app.start()
    webhook_url = f"{RENDER_URL}/webhook"
    await tg_app.bot.set_webhook(url=webhook_url, drop_pending_updates=True)
    logger.info(f"🚀 Bot em modo Webhook na URL: {webhook_url}")

@app.on_event("shutdown")
async def shutdown_event():
    await tg_app.stop()
    await tg_app.shutdown()

@app.get("/")
async def health():
    return {"status": "online", "system": "CCBJJ-IA-2026"}
