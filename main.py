import os
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from supabase import create_client, Client

# Configurações
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Inicialização
app = FastAPI()
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
# Em 2026, usamos a Application do python-telegram-bot de forma assíncrona
ptb_app = Application.builder().token(TOKEN).build()

@app.on_event("startup")
async def on_startup():
    # Configura o Webhook no Telegram assim que o Render sobe o app
    webhook_url = os.environ.get("WEBHOOK_URL")
    await ptb_app.bot.set_webhook(url=f"{webhook_url}/webhook")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Rota que recebe as mensagens do Telegram"""
    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)
    
    # Processa o comando /start
    if update.message and update.message.text == "/start":
        user = update.message.from_user
        
        # 2026 Style: Salva o novo usuário no Supabase automaticamente
        supabase.table("users").upsert({
            "id": user.id, 
            "username": user.username,
            "last_seen": "now()"
        }).execute()

        await update.message.reply_text(f"Olá {user.first_name}! Seu perfil foi atualizado no Supabase e estou rodando no Render 2026.")
    
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "alive"}
