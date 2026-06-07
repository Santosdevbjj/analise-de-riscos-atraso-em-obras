import os
import joblib
import pandas as pd
import logging
from pathlib import Path
from sqlalchemy import create_engine, text
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

# Integração com os módulos do projeto
import database
from i18n import get_text

# Base do projeto
BASE_DIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)

class MLResources:
    _instance = None

    def __init__(self):
        self.pipeline = None
        self.features = None
        self.engine = None

    @classmethod
    def get_all(cls):
        if cls._instance is None:
            cls._instance = cls()

            # -------------------------------
            # BANCO DE DADOS (SUPABASE)
            # -------------------------------
            db_url = os.getenv("DATABASE_URL")

            if db_url:
                # Se a URL começar com postgresql://, ajustamos o dialeto
                if db_url.startswith("postgresql://"):
                    # Como o Render instalou psycopg2-binary, o correto para o SQLAlchemy é 'postgresql+psycopg2://'
                    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")
                
                # Configuração segura de conexões contra timeouts
                cls._instance.engine = create_engine(
                    db_url,
                    pool_pre_ping=True,
                    pool_recycle=300
                )
                logger.info("🔌 Conexão com a Engine de Banco de Dados configurada.")
            else:
                logger.error("❌ A variável de ambiente DATABASE_URL não foi encontrada.")

            # -------------------------------
            # CARREGAMENTO DOS MODELOS DE IA
            # -------------------------------
            try:
                model_path = BASE_DIR / "models" / "pipeline_random_forest.pkl"
                meta_path = BASE_DIR / "models" / "features_metadata.joblib"

                if model_path.exists() and meta_path.exists():
                    cls._instance.pipeline = joblib.load(model_path)
                    cls._instance.features = joblib.load(meta_path)
                    logger.info("🧠 Modelos de Machine Learning carregados com sucesso.")
                else:
                    logger.error(f"❌ Arquivos de modelo não encontrados em: {BASE_DIR}/models/")

            except Exception as e:
                logger.error(f"❌ Erro crítico ao carregar modelos: {e}", exc_info=True)

        return cls._instance


# -------------------------------
# FUNÇÃO PRINCIPAL DE ANÁLISE
# -------------------------------
async def processar_analise(update: Update, context: ContextTypes.DEFAULT_TYPE, id_obra: str):
    res = MLResources.get_all()
    user_id = update.effective_user.id
    
    # Identifica o idioma salvo para o usuário (Padrão: pt)
    lang = database.get_language(user_id) if hasattr(database, 'get_language') else "pt"
    # Identifica o modo atual (Supabase/CSV)
    modo_atual = database.get_infra_mode(user_id) if hasattr(database, 'get_infra_mode') else "Supabase"

    if res.pipeline is None:
        await update.message.reply_text("⚠️ IA indisponível no momento. Certifique-se de que os arquivos .pkl/.joblib estão na pasta 'models'.")
        return

    # Mensagem inicial de processamento obtida do i18n
    status_msg = await update.message.reply_text(
        get_text(lang, "processing"), 
        parse_mode=ParseMode.MARKDOWN
    )

    try:
        # Busca padronizada na View do Banco de Dados
        query = text("""
            SELECT * 
            FROM view_analise_preditiva 
            WHERE UPPER(id_obra) = :val 
            LIMIT 1
        """)

        if res.engine is None:
            raise ValueError("Engine do banco de dados não inicializada. Verifique sua DATABASE_URL.")

        with res.engine.connect() as conn:
            df = pd.read_sql(query, conn, params={"val": id_obra.upper()})

        if df.empty:
            # Mensagem de Não Localizado usando o i18n adaptável
            msg_not_found = get_text(lang, "not_found", id_obra=id_obra.upper(), modo=modo_atual)
            await status_msg.edit_text(msg_not_found, parse_mode=ParseMode.MARKDOWN)
            return

        # -------------------------------
        # TRATAMENTO DE VARIÁVEIS (X)
        # -------------------------------
        # Alinha as colunas vindas do banco rigorosamente com o que o modelo espera
        X = df.reindex(columns=res.features, fill_value=0)

        # Conversão forçada e segura para tipos numéricos
        X = X.apply(pd.to_numeric, errors="coerce")
        X = X.fillna(0)

        logger.info(f"Dados estruturados enviados para predição da obra {id_obra}: {X.values.tolist()}")

        # -------------------------------
        # EXECUÇÃO DA PREDIÇÃO
        # -------------------------------
        prediction = res.pipeline.predict(X)
        risco_val = float(prediction[0])

        # -------------------------------
        # SISTEMA DE CORES DO RISCO (KPI)
        # -------------------------------
        if risco_val <= 7:
            status_cor, emoji = "NORMAL", "🟢"
        elif risco_val <= 12:
            status_cor, emoji = "ALERTA", "🟡"
        else:
            status_cor, emoji = "CRÍTICO", "🔴"

        # Montagem do relatório elegante integrado ao padrão visual do i18n
        header = get_text(lang, "report_header")
        impacto = get_text(lang, "report_impact", risco=risco_val)
        status_str = f"{emoji} *{status_cor}*"
        risco_rotulo = get_text(lang, "report_status", status=status_str)
        parecer = get_text(lang, "report_note", status=status_str)

        resultado = (
            f"{header}\n\n"
            f"📍 **ID da Obra:** `{id_obra.upper()}`\n"
            f"{risco_rotulo}\n"
            f"{impacto}\n\n"
            f"{parecer}"
        )

        await status_msg.edit_text(resultado, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Erro completo detectado na análise da obra {id_obra}: {e}", exc_info=True)
        # Fallback de erro amigável caso ocorra falha de infraestrutura
        await status_msg.edit_text("⚠️ **Erro Interno:** Não foi possível processar a consulta ao Supabase. Verifique a estrutura da tabela ou os logs do servidor.")
