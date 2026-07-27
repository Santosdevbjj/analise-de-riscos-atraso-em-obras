# 🏗️ Construction Delay Risk Prediction

<p align="center">
  <img src="assets/CCbjj-predicao-riscos.png" alt="Construction Delay Risk Prediction" width="600"/>
</p>

### CCbjj Engineering & Risk Intelligence — Operational Analytics Platform

[![Streamlit App](https://img.shields.io/badge/Simulator-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://predicaoriscos.streamlit.app)
[![Telegram Bot](https://img.shields.io/badge/Bot-Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/CCbjj_risk_bot)

> *Discipline, strategy, and data applied to civil engineering.*

---

## 1. Business Problem

Construction companies quietly lose revenue. Every project delivered behind schedule generates contractual penalties, forced re-planning, and client frustration — and the worst part: most of these delays were predictable.

The problem wasn't a lack of data. It was **a lack of analytical use of existing data.** Project histories, supplier ratings, weather data, and soil type were all recorded, but no one used them to anticipate risk. Decisions were made reactively — only after the delay had already happened.

**The central question of this project is:**
> *Which projects carry the highest risk of delay, and where should we act before the financial impact materializes?*

---

## 2. Context

Civil construction operations involve interdependent variables that, combined, determine whether a delivery will happen on time or not:

- **Weather conditions** at the project site (accumulated rainfall level)
- **Soil type and quality** (clay, sandy, rocky, silty)
- **Historical supplier rating** — the factor with the greatest isolated impact on the model
- **Construction stage** (foundation, structure, finishing) and its sensitivity to each variable
- **Budget and project complexity**

The project was developed using **synthetic data generated with realistic industry distributions**, simulating 200 projects across 10 Brazilian cities over 24 months of operational history — applying methodology and a tech stack equivalent to real production environments.

The deliverable is not just a model. It's a **data platform in production**: a Telegram bot that any project manager can consult from their phone, and a Streamlit simulator for real-time executive analysis.

---

## 3. Analysis Assumptions

- The dataset is **synthetic**, generated with construction-industry business rules (`scripts/gerar_dados.py`), with a fixed seed (`numpy.random.seed(42)`) to guarantee full reproducibility.
- The **target variable** is `dias_atraso` (days delayed) — a continuous regression problem, not binary classification.
- Suppliers with `rating_confiabilidade < 2.5` (reliability rating) were treated as **high risk**, with a penalty of +6 days added to the base delay during data generation.
- Foundation work on clay soil receives an additional penalty of +5.5 days — a rule derived from a civil engineering hypothesis validated during EDA.
- Records with `dias_atraso > 3 standard deviations` were removed as extreme outliers before training.
- The simulated period covers 24 months of operation; long-term seasonality was not modeled in this version.

---

## 4. Solution Strategy

The project followed the full Data Science framework, from problem to production product:

| Stage | Description |
|---|---|
| **1. Business problem** | Defining the real cost of each day of delay and the model's success criteria |
| **2. Data generation and architecture** | Synthetic dataset with engineering rules; organized in layers: `raw → analytics → products` |
| **3. Cleaning and processing** | Median imputation for weather variables; removal of extreme outliers in `dias_atraso` |
| **4. Hypothesis-driven EDA** | Validation of 4 business hypotheses about delay causes |
| **5. Feature engineering** | Creation of a composite risk index: `supplier_rating × weather_condition` |
| **6. ML preparation** | One-Hot Encoding for categorical variables; StandardScaler for continuous numerical variables |
| **7. Training and evaluation** | RandomForestRegressor with cross-validation; comparison against a historical-average baseline |
| **8. Business Performance** | Converting the technical MAE into estimated financial impact in R$ |
| **9. Deploy** | Telegram bot (Render) + Streamlit simulator + layered database (Supabase) |

---

## 5. Data Cleaning and Preparation

- **Median imputation** for weather variables with missing values — chosen over the mean for its robustness to extreme rainfall outliers.
- **Outlier removal** in `dias_atraso` above 3 standard deviations — atypical events that would distort the model's learning without representing the real operational pattern.
- **One-Hot Encoding** applied to categorical variables: `tipo_solo` (soil type), `etapa` (stage), `cidade` (city), and `material`.
- **StandardScaler** applied to continuous numerical variables: `orcamento_estimado` (estimated budget), `complexidade_obra` (project complexity), `nivel_chuva` (rainfall level), `rating_confiabilidade` (reliability rating), and `taxa_insucesso_fornecedor` (supplier failure rate).
- **Composite feature created:** `indice_risco = rating_fornecedor × nivel_chuva` — captures the amplifying effect of weather on already-problematic suppliers.

---

## 6. Exploratory Analysis — Hypothesis Validation

The EDA was driven by **business hypothesis validation**, not just visualization. Each hypothesis was tested before being inserted as a feature into the model:

| Hypothesis | Result | Impact on the Model |
|---|---|---|
| Is weather the main cause of delay? | ❌ False — supplier rating has ~3x greater impact during finishing stages | Weather kept as a feature, but with lower relative weight than supplier rating |
| Do low-rated suppliers delay projects even in good weather? | ✅ Confirmed | `rating_confiabilidade` became the model's most important feature |
| Do higher-budget projects carry more risk? | ✅ Projects above R$ 2M show greater sensitivity to accumulated delays | `orcamento_estimado` and `complexidade_obra` included as features |
| Is weather an isolated root cause? | ❌ It acts as an aggravating factor, rarely as the main cause | Creation of the composite index `rating × weather` |

**Model-recommended action:**
> Prioritize renegotiating or replacing suppliers with a rating below 3.0 **before** any intervention related to weather or logistics.

---

## 7. Model Training and Performance

**Algorithm chosen:** `RandomForestRegressor` — scikit-learn

**Why Random Forest instead of XGBoost?**
Random Forest was chosen for its better interpretability via `feature_importances_` — essential for presenting the model to non-technical construction stakeholders. XGBoost was evaluated and showed a marginal ~2% gain in MAE at a significant cost to explainability.

| Metric | Baseline (historical average) | Trained Model | Change |
|---|---|---|---|
| MAE | 12.0 days | **4.97 days** | **-59%** |
| RMSE | — | 6.3 days | — |
| R² | — | 0.41 | — |

**On R² = 0.41:**
In civil construction scenarios, uncontrolled external variables — human decisions, supply chains, extreme weather events — are inherent to the problem. An R² above 0.4 is a solid result in this context. The relevant business metric is the **MAE below 5 days**, which was achieved.

---

## 8. Financial Impact (Business Performance)

> Each day of delay represents approximately **R$ 1,380** in contractual penalties (average estimated cost for the size of the simulated projects).

| Indicator | Result |
|---|---|
| Reduction in forecast uncertainty | **~60%** |
| Residual financial risk per project (MAE × cost/day) | **≈ R$ 6,860** |
| Estimated potential savings (annual portfolio) | **≈ R$ 248,400/year** |
| Type of decision generated | **Preventive** — before the impact occurs |

The project's focus isn't just predicting delays. It's enabling the company to **act before the cost materializes** — turning a reactive problem into an operational advantage.

---

## 9. Product in Production

### 🤖 Telegram Bot
Any project manager can check their project's risk directly from their phone, with no technical background and no system login required:

1. Start with `/start`
2. Select language (**Portuguese** or **English**)
3. Select the data source (**local CSV** or **Supabase Cloud**)
4. Enter the project ID (e.g., `CCBJJ-100`)
5. Instantly receive: **risk status + explanatory chart + corporate PDF report**

### 📊 Streamlit Simulator
Executive interface for real-time sensitivity analysis:

- Parameter adjustment via side panel (city, stage, soil type, critical material, rainfall level, supplier rating)
- Visualization of **estimated delay** with risk classification (🟢 Stable / 🟡 Alert / 🔴 Critical)
- **Rainfall vs. delay simulation** chart (continuous curve)
- **Impact by geology** chart (comparative bars by soil type)
- Real-time **opportunity cost** estimate

# 🏗️ Construction Delay Risk Analysis

[![Telegram Bot](https://img.shields.io/badge/Bot-Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white)](https://t.me/CCbjj_risk_bot)
[![Streamlit App](https://img.shields.io/badge/Simulator-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://xsczxui9hscbsfpucq38yu.streamlit.app)

### 🏛️ Data Architecture (Supabase)

```
Supabase (layered database)
├── raw
│   ├── atividades_obra          # Activity history by stage
│   ├── fornecedores             # Supplier registry and ratings
│   └── clima                   # Accumulated rainfall level per project
├── analytics
│   └── dashboard_obras          # Consolidated fact table for analysis
└── products
    └── base_consulta_bot        # Decoupled consumption layer (Bot + Streamlit)
```

**Benefits of the layered architecture:** data governance and traceability, consumption decoupled from the source, scalability for new data products without impacting the ingestion pipeline.

---

## 10. Technical Decisions

| Decision | Choice | Alternative Evaluated | Reason |
|---|---|---|---|
| Algorithm | Random Forest | XGBoost | Better interpretability via `feature_importances_` for non-technical stakeholders |
| Database | Supabase | Local PostgreSQL | Free deploy with a native REST API and layered architecture |
| User delivery | Telegram Bot + Streamlit | BI Dashboard | No-login accessibility for field managers, via mobile phone |
| Cloud | Render | AWS Lambda | Zero cost for the project's scope; native `Procfile` |
| Data | Synthetic with domain rules | Public dataset | Allows precise control of correlations and validation of business hypotheses |

**Trade-off accepted:** synthetic data ensures analytical control but limits generalization to real production environments. The architecture was designed for straightforward replacement with a real data source — without pipeline refactoring.

---

## 11. Technologies Used

**Data and Machine Learning**

`Python 3.13` | `Pandas` | `NumPy` | `Scikit-learn` | `SciPy` | `Matplotlib` | `Seaborn` | `Plotly` | `Faker`

**Infrastructure and Deploy**

`Supabase` | `Render` | `Docker` | `FastAPI` | `Uvicorn` | `SQLAlchemy` | `Alembic`

**User Delivery**

`Streamlit` | `Telegram Bot API (python-telegram-bot 21.0)` | `ReportLab` (PDF)

**Utilities**

`python-dotenv` | `joblib` | `pytz` | `pg8000`

---

## 12. How to Run the Project

**Prerequisites:** Python 3.10+, Git, a Telegram account (for the bot)

```bash
# 1. Clone the repository
git clone https://github.com/Santosdevbjj/analiseRiscosAtrasoObras
cd analiseRiscosAtrasoObras

# 2. Install dependencies
pip install -r requirements.txt          # Streamlit + ML
pip install -r requirements_api.txt      # FastAPI + Bot + Database

# 3. Configure environment variables
# Create a .env file at the project root with:
# DATABASE_URL=your_supabase_url_here
# TELEGRAM_TOKEN=your_token_here

# 4. Generate the synthetic data
python scripts/gerar_dados.py

# 5. Run the Telegram Bot
python scripts/telegram_bot.py

# 6. Run the Streamlit Simulator
streamlit run app.py
```

> **Offline mode (without Supabase):** The project runs fully with a local CSV. Select "📂 Local CSV Mode" when starting the bot, or set `USE_CSV=true` in the `.env` file.

---

## 13. Lessons Learned

The biggest challenge was **translating the technical MAE into a financial impact that a board could defend.** It's not trivial to connect "an average error of 4.97 days" with "a potential savings of R$ 248k/year" in a way a non-technical manager trusts the number — and that required both calculation rigor and narrative clarity.

I started with the data before precisely defining the business problem — and had to backtrack, which cost time and rework. Today I would structure the problem, the success criterion, and the unit cost of delay **before** opening any notebook.

The most valued deliverable wasn't the model. It was the **bot and the simulator** — because they made the result accessible to whoever makes the decision, without depending on a technical background. A model only a data scientist can query generates no operational value.

---

## 14. Next Steps

- [ ] **Integration with a real weather API** (OpenWeatherMap) to replace simulated data with real rainfall data by project ZIP code
- [ ] **Data drift monitoring** with Evidently AI — detect when production data distribution diverges from training data
- [ ] **Prediction logging** for query history and continuous model retraining
- [ ] **Risk classification model** (High / Medium / Low) as a complement to the regression — for simpler alerts in the bot
- [ ] **Expansion of the financial impact calculation** by contract type (fixed price vs. cost-plus) and by region

---

## Repository Structure

```
analiseRiscosAtrasoObras/
├── data/
│   ├── raw/
│   │   ├── climaccbjj.csv                    # Weather data by project
│   │   ├── atividadesccbjj.csv               # Activities and status by stage
│   │   ├── fornecedoresccbjj.csv             # Supplier registry and ratings
│   │   ├── obrasccbjj.csv                    # Project data
│   │   └── base_consulta_botccbjj.csv        # Consolidated base for Bot and App
│   └── processed/
│       └── df_mestre_consolidado.csv.gz      # Cleaned and compressed dataset
├── models/
│   ├── pipeline_random_forest.pkl            # Serialized trained model
│   └── features_metadata.joblib             # Feature order for inference
├── scripts/
│   ├── app.py                               # Streamlit simulator (executive interface)
│   ├── gerar_dados.py                       # Synthetic dataset generation
│   ├── telegram_bot.py                      # Telegram bot (deployed on Render)
│   ├── handlers.py                          # Bot command handlers
│   ├── database.py                          # Postgres/SQLite abstraction (Supabase)
│   └── i18n.py                              # PT/EN internationalization
├── notebooks/                               # Exploratory analysis and training
├── requirements.txt                         # Streamlit + ML
├── requirements_api.txt                     # FastAPI + Bot + Database
├── requirements_streamlit.txt               # Streamlit Cloud deploy
├── runtime.txt                              # python-3.13.4
├── Procfile                                 # web: python scripts/telegram_bot.py
└── README.md
```

---

**Author:** Sérgio Santos — Data Scientist | Mission-Critical Environments and Data Governance

[![Sérgio Santos Portfolio](https://img.shields.io/badge/Portfolio-Sérgio_Santos-111827?style=for-the-badge&logo=githubpages&logoColor=00eaff)](https://portfoliosantossergio.vercel.app)
[![Sérgio Santos LinkedIn](https://img.shields.io/badge/LinkedIn-Sérgio_Santos-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/santossergioluiz)
