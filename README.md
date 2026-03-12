# 🏗️ Predição de Risco de Atraso em Obras

### CCbjj Engenharia & Inteligência de Riscos — Plataforma de Análise Operacional

 
[![Streamlit App](https://img.shields.io/badge/Simulador-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://xsczxui9hscbsfpucq38yu.streamlit.app)

[![Telegram Bot](https://img.shields.io/badge/Bot-Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/CCbjj_risk_bot)


> *Disciplina, estratégia e dados aplicados à engenharia civil.*

---

## 1. Problema de Negócio

Empresas de construção civil perdem receita de forma silenciosa. Cada obra entregue fora do prazo gera multas contratuais, replanejamento forçado e desgaste com clientes — e o pior: a maioria desses atrasos era previsível.

O problema não era falta de dados. Era **falta de uso analítico dos dados existentes.** Históricos de obras, avaliações de fornecedores, dados climáticos e tipo de solo estavam registrados, mas ninguém os usava para antecipar risco. As decisões eram tomadas de forma reativa — apenas depois que o atraso já havia ocorrido.

**A pergunta central deste projeto é:**
> *Quais obras apresentam maior risco de atraso e onde devemos agir antes que o impacto financeiro se materialize?*

---

## 2. Contexto

A operação de obras civis envolve variáveis interdependentes que, combinadas, determinam se uma entrega vai ocorrer no prazo ou não:

- **Condições climáticas** da região da obra (nível de chuva acumulado)
- **Tipo e qualidade do solo** (argiloso, arenoso, rochoso, siltoso)
- **Rating histórico de fornecedores** — o fator com maior impacto isolado no modelo
- **Etapa construtiva** (fundação, estrutura, acabamento) e sua sensibilidade a cada variável
- **Orçamento e complexidade** da obra

O projeto foi desenvolvido com **dados sintéticos gerados com distribuições realistas do setor**, simulando 200 obras em 10 cidades brasileiras ao longo de 24 meses de histórico operacional — aplicando metodologia e stack equivalentes a ambientes produtivos reais.

A entrega não é apenas um modelo. É uma **plataforma de dados em produção**: um bot no Telegram que qualquer gestor de obra consulta pelo celular, e um simulador Streamlit para análises executivas em tempo real.

---

## 3. Premissas da Análise

- O dataset é **sintético**, gerado com regras de negócio do setor de construção civil (`scripts/gerar_dados.py`), com seed fixo (`numpy.random.seed(42)`) para garantir reprodutibilidade total.
- A **variável-alvo** é `dias_atraso` — problema de regressão contínua, não classificação binária.
- Fornecedores com `rating_confiabilidade < 2.5` foram tratados como **alto risco**, com penalidade de +6 dias no atraso base na geração dos dados.
- Obras de fundação em solo argiloso recebem penalidade adicional de +5.5 dias — regra derivada de hipótese de engenharia civil validada na EDA.
- Registros com `dias_atraso > 3 desvios padrão` foram removidos como outliers extremos antes do treinamento.
- O período simulado cobre 24 meses de operação; sazonalidades de longo prazo não foram modeladas nesta versão.

---

## 4. Estratégia da Solução

O projeto seguiu o framework completo de Ciência de Dados, do problema ao produto em produção:

| Etapa | Descrição |
|---|---|
| **1. Problema de negócio** | Definição do custo real de cada dia de atraso e do critério de sucesso do modelo |
| **2. Geração e arquitetura de dados** | Dataset sintético com regras de engenharia; organização em camadas: `raw → analytics → products` |
| **3. Limpeza e tratamento** | Imputação por mediana em variáveis climáticas; remoção de outliers extremos em `dias_atraso` |
| **4. EDA orientada a hipóteses** | Validação de 4 hipóteses de negócio sobre causas de atraso |
| **5. Engenharia de atributos** | Criação de índice de risco composto: `rating_fornecedor × condição_climática` |
| **6. Preparação para ML** | One-Hot Encoding para variáveis categóricas; StandardScaler para variáveis numéricas contínuas |
| **7. Treinamento e avaliação** | RandomForestRegressor com validação cruzada; comparação contra baseline de média histórica |
| **8. Business Performance** | Conversão do MAE técnico em impacto financeiro estimado em R$ |
| **9. Deploy** | Bot Telegram (Render) + Simulador Streamlit + banco de dados em camadas (Supabase) |

---

## 5. Limpeza e Preparação dos Dados

- **Imputação pela mediana** em variáveis climáticas com valores ausentes — escolhida sobre a média por ser robusta a outliers de chuva extrema.
- **Remoção de outliers** em `dias_atraso` acima de 3 desvios padrão — eventos atípicos que distorceriam o aprendizado do modelo sem representar o padrão operacional real.
- **One-Hot Encoding** aplicado às variáveis categóricas: `tipo_solo`, `etapa`, `cidade` e `material`.
- **StandardScaler** aplicado às variáveis numéricas contínuas: `orcamento_estimado`, `complexidade_obra`, `nivel_chuva`, `rating_confiabilidade` e `taxa_insucesso_fornecedor`.
- **Feature composta criada:** `indice_risco = rating_fornecedor × nivel_chuva` — captura o efeito amplificador do clima sobre fornecedores já problemáticos.

---

## 6. Análise Exploratória — Validação de Hipóteses

A EDA foi orientada à **validação de hipóteses de negócio**, não apenas à visualização. Cada hipótese foi testada antes de ser inserida como feature no modelo:

| Hipótese | Resultado | Impacto no Modelo |
|---|---|---|
| Clima é a principal causa de atraso? | ❌ Falsa — rating do fornecedor tem impacto ~3x maior em etapas de acabamento | Clima mantido como feature, mas com peso relativo menor que fornecedor |
| Fornecedores com baixo rating atrasam mesmo em bom clima? | ✅ Confirmada | `rating_confiabilidade` tornou-se a feature mais importante do modelo |
| Obras de maior orçamento têm mais risco? | ✅ Obras acima de R$ 2M apresentam maior sensibilidade a atrasos acumulados | `orcamento_estimado` e `complexidade_obra` incluídos como features |
| Clima é causa raiz isolada? | ❌ Atua como fator agravante, raramente como causa principal | Criação do índice composto `rating × clima` |

**Ação recomendada pelo modelo:**
> Priorizar renegociação ou substituição de fornecedores com rating abaixo de 3.0 **antes** de qualquer intervenção relacionada a clima ou logística.

---

## 7. Treinamento e Performance do Modelo

**Algoritmo escolhido:** `RandomForestRegressor` — scikit-learn

**Por que Random Forest e não XGBoost?**
O Random Forest foi escolhido por oferecer melhor interpretabilidade via `feature_importances_` — essencial para apresentar o modelo a stakeholders não técnicos de obras. O XGBoost foi avaliado e apresentou ganho marginal de ~2% no MAE com custo significativo de explicabilidade.

| Métrica | Baseline (média histórica) | Modelo Treinado | Variação |
|---|---|---|---|
| MAE | 12,0 dias | **4,97 dias** | **-59%** |
| RMSE | — | 6,3 dias | — |
| R² | — | 0,41 | — |

**Sobre o R² = 0,41:**
Em cenários de construção civil, variáveis externas não controladas — decisões humanas, cadeia de fornecedores, eventos climáticos extremos — são inerentes ao problema. R² acima de 0,4 é resultado sólido nesse contexto. A métrica de negócio relevante é o **MAE inferior a 5 dias**, que foi atingida.

---

## 8. Impacto Financeiro (Business Performance)

> Cada dia de atraso representa aproximadamente **R$ 1.380** em multas contratuais (custo médio estimado para o porte das obras simuladas).

| Indicador | Resultado |
|---|---|
| Redução de incerteza na previsão | **~60%** |
| Risco financeiro residual por obra (MAE × custo/dia) | **≈ R$ 6.860** |
| Economia potencial estimada (portfólio anual) | **≈ R$ 248.400/ano** |
| Tipo de decisão gerada | **Preventiva** — antes do impacto ocorrer |

O foco do projeto não é apenas prever atrasos. É permitir que a empresa **aja antes que o custo se materialize** — convertendo um problema reativo em uma vantagem operacional.

---

## 9. Produto em Produção

### 🤖 Bot do Telegram
Qualquer gestor de obra consulta o risco da sua obra diretamente pelo celular, sem perfil técnico e sem login em sistema:

1. Inicie com `/start`
2. Selecione idioma (**Português** ou **English**)
3. Selecione a fonte de dados (**CSV local** ou **Supabase Cloud**)
4. Digite o ID da obra (ex: `CCBJJ-100`)
5. Receba instantaneamente: **status de risco + gráfico explicativo + relatório PDF corporativo**

### 📊 Simulador Streamlit
Interface executiva para análise de sensibilidade em tempo real:

- Ajuste de parâmetros via painel lateral (cidade, etapa, tipo de solo, insumo crítico, nível de chuva, rating do fornecedor)
- Visualização do **atraso estimado** com classificação de risco (🟢 Estável / 🟡 Alerta / 🔴 Crítico)
- Gráfico de **simulação de chuva vs. atraso** (curva contínua)
- Gráfico de **impacto por geologia** (barras comparativas por tipo de solo)
- Estimativa de **custo de oportunidade** calculada em tempo real

### 🏛️ Arquitetura de Dados (Supabase)

```
Supabase (banco em camadas)
├── raw
│   ├── atividades_obra          # Histórico de atividades por etapa
│   ├── fornecedores             # Cadastro e ratings
│   └── clima                   # Nível de chuva acumulado por obra
├── analytics
│   └── dashboard_obras          # Tabela fato consolidada para análise
└── products
    └── base_consulta_bot        # Camada de consumo desacoplada (Bot + Streamlit)
```

**Benefícios da arquitetura em camadas:** governança e rastreabilidade dos dados, consumo desacoplado da origem, escalabilidade para novos produtos de dados sem impactar o pipeline de ingestão.

---

## 10. Decisões Técnicas

| Decisão | Escolha | Alternativa Avaliada | Motivo |
|---|---|---|---|
| Algoritmo | Random Forest | XGBoost | Melhor interpretabilidade via `feature_importances_` para stakeholders não técnicos |
| Banco de dados | Supabase | PostgreSQL local | Deploy gratuito com API REST nativa e arquitetura em camadas |
| Entrega ao usuário | Telegram Bot + Streamlit | Dashboard BI | Acessibilidade sem login para gestores de campo, via celular |
| Cloud | Render | AWS Lambda | Custo zero para o escopo do projeto; `Procfile` nativo |
| Dados | Sintéticos com regras de domínio | Dataset público | Permite controlar as correlações e validar hipóteses de negócio com precisão |

**Trade-off aceito:** dados sintéticos garantem controle analítico mas limitam a generalização para ambientes produtivos reais. A arquitetura foi projetada para substituição simples pela fonte de dados real — sem refatoração do pipeline.

---

## 11. Tecnologias Utilizadas

**Dados e Machine Learning**

`Python 3.13` | `Pandas` | `NumPy` | `Scikit-learn` | `SciPy` | `Matplotlib` | `Seaborn` | `Plotly` | `Faker`

**Infraestrutura e Deploy**

`Supabase` | `Render` | `Docker` | `FastAPI` | `Uvicorn` | `SQLAlchemy` | `Alembic`

**Entrega ao Usuário**

`Streamlit` | `Telegram Bot API (python-telegram-bot 21.0)` | `ReportLab` (PDF)

**Utilitários**

`python-dotenv` | `joblib` | `pytz` | `pg8000`

---

## 12. Como Executar o Projeto

**Pré-requisitos:** Python 3.10+, Git, conta no Telegram (para o bot)

```bash
# 1. Clone o repositório
git clone https://github.com/Santosdevbjj/analiseRiscosAtrasoObras
cd analiseRiscosAtrasoObras

# 2. Instale as dependências
pip install -r requirements.txt          # Streamlit + ML
pip install -r requirements_api.txt      # FastAPI + Bot + Banco

# 3. Configure as variáveis de ambiente
# Crie um arquivo .env na raiz com:
# DATABASE_URL=sua_url_supabase_aqui
# TELEGRAM_TOKEN=seu_token_aqui

# 4. Gere os dados sintéticos
python scripts/gerar_dados.py

# 5. Execute o Bot do Telegram
python scripts/telegram_bot.py

# 6. Execute o Simulador Streamlit
streamlit run app.py
```

> **Modo offline (sem Supabase):** O projeto roda integralmente com CSV local. Selecione "📂 Modo CSV Local" ao iniciar o bot ou configure `USE_CSV=true` no `.env`.

---

## 13. Aprendizados

O maior desafio foi **traduzir o MAE técnico em impacto financeiro defensável para uma diretoria.** Não é trivial conectar "erro médio de 4,97 dias" com "economia potencial de R$ 248k/ano" de forma que um gestor não técnico confie no número — e isso exigiu tanto rigor nos cálculos quanto clareza na narrativa.

Comecei pelo dado antes de definir o problema de negócio com precisão — e precisei voltar, o que custou tempo e retrabalho. Hoje estruturaria o problema, o critério de sucesso e o custo unitário do atraso **antes** de abrir qualquer notebook.

A entrega mais valorizada não foi o modelo. Foi o **bot e o simulador** — porque tornaram o resultado acessível para quem toma a decisão, sem depender de perfil técnico. Um modelo que só um cientista de dados consegue consultar não gera valor operacional.

---

## 14. Próximos Passos

- [ ] **Integração com API climática real** (OpenWeatherMap) para substituir dados simulados por dados reais de chuva por CEP da obra
- [ ] **Monitoramento de data drift** com Evidently AI — detectar quando a distribuição dos dados de produção se afasta do treino
- [ ] **Logging de predições** para histórico de consultas e retreinamento contínuo do modelo
- [ ] **Modelo de classificação de risco** (Alto / Médio / Baixo) como complemento à regressão — para alertas mais simples no bot
- [ ] **Expansão do cálculo de impacto financeiro** por tipo de contrato (preço fixo vs. administração) e por região

---

## Estrutura do Repositório

```
analiseRiscosAtrasoObras/
├── data/
│   ├── raw/
│   │   ├── climaccbjj.csv                    # Dados climáticos por obra
│   │   ├── atividadesccbjj.csv               # Atividades e status por etapa
│   │   ├── fornecedoresccbjj.csv             # Cadastro e ratings
│   │   ├── obrasccbjj.csv                    # Dados das obras
│   │   └── base_consulta_botccbjj.csv        # Base consolidada para Bot e App
│   └── processed/
│       └── df_mestre_consolidado.csv.gz      # Dataset tratado e comprimido
├── models/
│   ├── pipeline_random_forest.pkl            # Modelo treinado serializado
│   └── features_metadata.joblib             # Ordem de features para inferência
├── scripts/
│   ├── app.py                               # Simulador Streamlit (interface executiva)
│   ├── gerar_dados.py                       # Geração do dataset sintético
│   ├── telegram_bot.py                      # Bot do Telegram (deploy no Render)
│   ├── handlers.py                          # Handlers dos comandos do bot
│   ├── database.py                          # Abstração Postgres/SQLite (Supabase)
│   └── i18n.py                              # Internacionalização PT/EN
├── notebooks/                               # Análise exploratória e treinamento
├── requirements.txt                         # Streamlit + ML
├── requirements_api.txt                     # FastAPI + Bot + Banco
├── requirements_streamlit.txt               # Deploy Streamlit Cloud
├── runtime.txt                              # python-3.13.4
├── Procfile                                 # web: python scripts/telegram_bot.py
└── README.md
```

---

**Autor:** Sérgio Santos — Cientista de Dados | Ambientes Críticos e Governança de Dados

[![Portfólio Sérgio Santos](https://img.shields.io/badge/Portfólio-Sérgio_Santos-111827?style=for-the-badge&logo=githubpages&logoColor=00eaff)](https://portfoliosantossergio.vercel.app)
[![LinkedIn Sérgio Santos](https://img.shields.io/badge/LinkedIn-Sérgio_Santos-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/santossergioluiz)
