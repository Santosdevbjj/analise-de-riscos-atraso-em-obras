import os
import logging
from fastapi import FastAPI, Request, Response, status
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from scripts.telegram_bot import processar_analise

# -------------------------------
# LOGGING
# -------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# -------------------------------
# ENV
# -------------------------------
TOKEN = os.getenv("TELEGRAM_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise RuntimeError("❌ TELEGRAM_TOKEN não definido")

if not RENDER_URL:
    raise RuntimeError("❌ RENDER_EXTERNAL_URL não definido")

# -------------------------------
# APP
# -------------------------------
app = FastAPI(title="CCBJJ-IA-Gateway", version="2026.2")

# -------------------------------
# TELEGRAM BOT
# -------------------------------
tg_app = Application.builder().token(TOKEN).build()

# -------------------------------
# HANDLERS
# -------------------------------
async def start(update: Update, context):
    try:
        await update.message.reply_text(
            "🏗️ *CCBJJ Bot Online (v2026)*\n"
            "Sistema de Inteligência Preditiva em Operação.\n\n"
            "Envie o ID da obra para análise (ex: `CCBJJ-100`).",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Erro no comando /start: {e}")


async def handle_message(update: Update, context):
    try:
        if not update.message or not update.message.text:
            return

        id_obra = update.message.text.strip().upper()

        logger.info(f"📩 Nova mensagem recebida: {id_obra}")

        await processar_analise(update, context, id_obra)

    except Exception as e:
        logger.error(f"Erro no handler de mensagem: {e}", exc_info=True)


# -------------------------------
# REGISTRO
# -------------------------------
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


# -------------------------------
# HEALTH CHECK (Render)
# -------------------------------
@app.api_route("/", methods=["GET", "HEAD"])
async def health():
    return {
        "status": "online",
        "service": "telegram-bot",
        "version": "2026.2"
    }


# -------------------------------
# WEBHOOK
# -------------------------------
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()

        logger.debug(f"📦 Payload recebido: {data}")

        update = Update.de_json(data, tg_app.bot)
        await tg_app.process_update(update)

        return Response(status_code=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"❌ Webhook error: {e}", exc_info=True)
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -------------------------------
# STARTUP
# -------------------------------
@app.on_event("startup")
async def startup():
    try:
        logger.info("🚀 Inicializando bot...")

        await tg_app.initialize()
        await tg_app.start()

        webhook_url = f"{RENDER_URL}/webhook"

        await tg_app.bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )

        logger.info(f"✅ Webhook ativo: {webhook_url}")

    except Exception as e:
        logger.error(f"❌ Erro no startup: {e}", exc_info=True)
        raise


# -------------------------------
# SHUTDOWN
# -------------------------------
@app.on_event("shutdown")
async def shutdown():
    try:
        logger.info("🛑 Encerrando bot...")

        await tg_app.stop()
        await tg_app.shutdown()

        logger.info("✅ Bot encerrado com sucesso")

    except Exception as e:
        logger.error(f"Erro no shutdown: {e}", exc_info=True)
