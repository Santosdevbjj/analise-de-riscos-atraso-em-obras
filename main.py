import os
import logging
from fastapi import FastAPI, Request, Response, status
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from scripts.telegram_bot import processar_analise

# Configuração de Logs Profissional
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configurações de Ambiente
TOKEN = os.getenv("TELEGRAM_TOKEN")
RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "https://analiseriscosatrasoobras.onrender.com")

app = FastAPI(title="CCBJJ-IA-Gateway")

# Instância Global do Bot (NÃO iniciamos aqui, apenas configuramos o builder)
tg_app = Application.builder().token(TOKEN).build()

# Handlers do Bot
async def start(update: Update, context):
    welcome_text = (
        "🏗️ *CCBJJ Bot Online (v2026)*\n"
        "Sistema de Inteligência Preditiva em Operação.\n\n"
        "Envie o ID da obra para análise (ex: `CCBJJ-100`)."
    )
    await update.message.reply_markdown(welcome_text)

async def handle_message(update: Update, context):
    id_obra = update.message.text.strip()
    if id_obra:
        await processar_analise(update, context, id_obra)

# Registro de Handlers
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- ROTAS API ---

@app.api_route("/", methods=["GET", "HEAD"])
async def health_check(request: Request):
    """
    Health check robusto que aceita GET e HEAD.
    Evita o erro 405 disparado pelo monitoramento do Render.
    """
    return {"status": "online", "version": "2026.1", "mode": "webhook"}

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Ponto de entrada único para mensagens do Telegram.
    Processamento assíncrono puro, sem threads externas.
    """
    try:
        data = await request.json()
        update = Update.de_json(data, tg_app.bot)
        # Enfileira o update no processamento interno do PTB
        await tg_app.process_update(update)
        return Response(status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Falha crítica no processamento do Webhook: {e}")
        return Response(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- CICLO DE VIDA ---

@app.on_event("startup")
async def on_startup():
    """
    Configuração de inicialização seguindo o padrão Cloud-Native.
    """
    await tg_app.initialize()
    await tg_app.start()
    
    webhook_url = f"{RENDER_URL}/webhook"
    # drop_pending_updates=True evita o 'flood' de mensagens acumuladas durante o deploy
    await tg_app.bot.set_webhook(url=webhook_url, drop_pending_updates=True)
    
    logger.info(f"🚀 Bot inicializado com sucesso. Webhook ativo em: {webhook_url}")

@app.on_event("shutdown")
async def on_shutdown():
    """
    Graceful shutdown para evitar corrupção de memória ou conexões pendentes.
    """
    logger.info("Encerrando serviços...")
    await tg_app.stop()
    await tg_app.shutdown()
