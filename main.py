import os
import logging
from fastapi import FastAPI, Request, Response, status
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from scripts.telegram_bot import processar_analise

# LOGS
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ENV
TOKEN = os.getenv("TELEGRAM_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN não definido")

if not RENDER_URL:
    raise RuntimeError("❌ RENDER_EXTERNAL_URL não definido")

app = FastAPI(title="CCBJJ-IA-Gateway")

# BOT
tg_app = Application.builder().token(TOKEN).build()

# HANDLERS
async def start(update: Update, context):
    await update.message.reply_markdown(
        "🏗️ *CCBJJ Bot Online (v2026)*\n"
        "Sistema de Inteligência Preditiva em Operação.\n\n"
        "Envie o ID da obra para análise (ex: `CCBJJ-100`)."
    )

async def handle_message(update: Update, context):
    if not update.message or not update.message.text:
        return
    
    id_obra = update.message.text.strip().upper()
    await processar_analise(update, context, id_obra)

# REGISTRO
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# HEALTH CHECK
@app.api_route("/", methods=["GET", "HEAD"])
async def health():
    return {"status": "online"}

# WEBHOOK
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        update = Update.de_json(data, tg_app.bot)
        await tg_app.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return Response(status_code=500)

# STARTUP
@app.on_event("startup")
async def startup():
    await tg_app.initialize()
    await tg_app.start()

    webhook_url = f"{RENDER_URL}/webhook"
    await tg_app.bot.set_webhook(webhook_url, drop_pending_updates=True)

    logger.info(f"🚀 Webhook ativo: {webhook_url}")

# SHUTDOWN
@app.on_event("shutdown")
async def shutdown():
    await tg_app.stop()
    await tg_app.shutdown()
