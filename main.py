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

# Variáveis de Ambiente Críticas
TOKEN = os.getenv("TELEGRAM_TOKEN")
RENDER_URL = os.getenv("RENDER_URL") # Ex: https://seu-bot.onrender.com

# Inicialização do Bot
app = FastAPI()
tg_app = Application.builder().token(TOKEN).build()

# Handlers
async def start(update: Update, context):
    await update.message.reply_text("🏗️ Bot CCBJJ Ativo. Envie o ID da obra para análise.")

async def handle_id(update: Update, context):
    id_obra = update.message.text.strip().upper()
    await processar_analise(update, context, id_obra)

tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_id))

# Endpoint do Webhook
@app.post("/webhook")
async def webhook_handler(request: Request):
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return {"status": "ok"}

# Ciclo de Vida do Webhook no Render
@app.on_event("startup")
async def startup_event():
    await tg_app.initialize()
    await tg_app.start()
    # [span_7](start_span)Define a URL do Webhook no Telegram automaticamente[span_7](end_span)
    webhook_url = f"{RENDER_URL}/webhook"
    await tg_app.bot.set_webhook(url=webhook_url, drop_pending_updates=True)
    logger.info(f"🚀 Webhook configurado: {webhook_url}")

@app.on_event("shutdown")
async def shutdown_event():
    await tg_app.stop()
    await tg_app.shutdown()

@app.get("/health")
async def health():
    return {"status": "online", "mode": "webhook_ipv4_2026"}
