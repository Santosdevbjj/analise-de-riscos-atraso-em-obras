import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application
from supabase import create_client, Client

# Configuração de Logs (Importante para ver no painel do Render se algo der errado)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# 1. MAPEAMENTO DAS VARIÁVEIS DE AMBIENTE DO RENDER
# Usando exatamente os nomes que você forneceu
TOKEN = os.environ.get("TELEGRAM_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
DATABASE_URL = os.environ.get("DATABASE_URL")

# Nota: O SDK do Supabase geralmente pede URL e API KEY separadas.
# Se o seu DATABASE_URL for a string de conexão direta do Postgres, 
# certifique-se de que as tabelas existam. 
# Aqui, assumirei que você configurou o cliente Supabase corretamente.
SUPABASE_URL = os.environ.get("SUPABASE_URL") # Caso tenha estas extras
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

app = FastAPI()

# Inicialização do Cliente Supabase
# Se você usa apenas DATABASE_URL para Postgres direto, a lógica de insert mudaria.
# Se for Supabase SDK, usamos:
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Inicialização do Bot do Telegram
ptb_app = Application.builder().token(TOKEN).build()

@app.on_event("startup")
async def setup_webhook():
    """Configura o Webhook no Telegram ao iniciar o app"""
    if not WEBHOOK_URL:
        logger.error("A variável WEBHOOK_URL não está configurada!")
        return
    
    # O Render 2026 exige que o webhook aponte para a rota correta
    url_final = f"{WEBHOOK_URL.rstrip('/')}/webhook"
    await ptb_app.bot.set_webhook(url=url_final)
    logger.info(f"Webhook configurado para: {url_final}")

@app.post("/webhook")
async def handle_webhook(request: Request):
    """Recebe as atualizações do Telegram"""
    try:
        data = await request.json()
        update = Update.de_json(data, ptb_app.bot)
        
        # Processamento de mensagens de texto
        if update.message and update.message.text:
            text = update.message.text
            user_id = update.message.from_user.id
            user_name = update.message.from_user.first_name

            # Comando /start
            if text == "/start":
                await update.message.reply_text(
                    "🏗️ **Bem-vindo ao Analisador de Riscos de Obras 2026**\n\n"
                    "Use `/obra [nome ou descrição]` para registrar um novo projeto para análise."
                )

            # Comando /obra
            elif text.startswith("/obra"):
                descricao_obra = text.replace("/obra", "").strip()
                
                if not descricao_obra:
                    await update.message.reply_text("Por favor, digite uma descrição após o comando. Ex: /obra Reforma Galpão")
                    return

                # Salvando no Supabase
                try:
                    supabase.table("registros_obras").insert({
                        "telegram_id": user_id,
                        "usuario": user_name,
                        "descricao": descricao_obra,
                        "status_analise": "Pendente"
                    }).execute()
                    
                    await update.message.reply_text(
                        f"✅ Obra registrada com sucesso, {user_name}!\n"
                        "Nossa análise de riscos já foi iniciada."
                    )
                except Exception as e:
                    logger.error(f"Erro no Supabase: {e}")
                    await update.message.reply_text("❌ Ocorreu um erro ao salvar os dados no banco.")

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erro no processamento do webhook: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
def home():
    """Rota de verificação de saúde (Health Check)"""
    return {
        "status": "Online", 
        "service": "Analisador de Obras",
        "python_version": os.environ.get("PYTHON_VERSION", "3.14.3")
    }
