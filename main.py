import os
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application
from supabase import create_client, Client

# Configurações do Ambiente Render 2026
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
WEBHOOK_URL = "https://analiseriscosatrasoobras.onrender.com"

app = FastAPI()
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
ptb_app = Application.builder().token(TOKEN).build()

@app.on_event("startup")
async def setup_webhook():
    # Garante que o Telegram sabe para onde enviar as mensagens
    await ptb_app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")

@app.post("/webhook")
async def handle_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, ptb_app.bot)

    if update.message and update.message.text:
        text = update.message.text
        user_id = update.message.from_user.id
        user_name = update.message.from_user.first_name

        # Lógica: Se a mensagem começar com /obra, salvamos no Supabase
        if text.startswith("/obra"):
            descricao_obra = text.replace("/obra", "").strip()
            
            # Salvando no Supabase (Tabela: registros_obras)
            try:
                supabase.table("registros_obras").insert({
                    "telegram_id": user_id,
                    "usuario": user_name,
                    "descricao": descricao_obra,
                    "status_analise": "Pendente"
                }).execute()
                
                await update.message.reply_text(
                    f"✅ Obra registrada, {user_name}!\n"
                    "Nossa IA está analisando os riscos de atraso agora."
                )
            except Exception as e:
                await update.message.reply_text("❌ Erro ao salvar no banco de dados.")

        elif text == "/start":
            await update.message.reply_text(
                "🏗️ **Bem-vindo ao Analisador de Riscos de Obras 2026**\n\n"
                "Use `/obra [nome ou descrição]` para registrar um novo projeto para análise."
            )

    return {"status": "processed"}

# Rota de Health Check para o Render
@app.get("/")
def home():
    return {"status": "Online", "service": "Analisador de Obras"}
