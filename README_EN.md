Aqui está a tradução completa e precisa do seu `README.md` para o inglês, mantendo a formatação, badges, emojis, código e a estrutura original do documento:

---

# # 🏗️ Construction Delay Risk Prediction

### CCbjj Engineering & Risk Intelligence — Operational Analysis Platform

> *Discipline, strategy, and data applied to civil engineering.*

---

## 1. Business Problem

Civil construction companies suffer silent revenue losses. Every project delivered past its deadline incurs contractual fines, forced rescheduling, and customer dissatisfaction — worst of all, most of these delays were predictable.

The issue was not a lack of data, but a **lack of analytical data utilization.** Project histories, supplier ratings, weather data, and soil types were recorded, yet no one leveraged them to anticipate risk. Decisions were made reactively — only after delays had already occurred.

**The core question of this project is:**

> *Which construction projects present the highest delay risk, and where must we intervene before the financial impact materializes?*

---

## 2. Context

Civil engineering operations involve interdependent variables that, combined, determine whether a project will be delivered on time:

* **Weather conditions** in the project site area (accumulated rainfall level)
* **Soil type and quality** (clay, sand, rock, silt)
* **Historical supplier ratings** — the single most impactful factor in the model
* **Construction stage** (foundation, structure, finishing) and its sensitivity to each variable
* **Budget and complexity** of the project

This project was built using **synthetic data generated with realistic industry distributions**, simulating 200 construction projects across 10 Brazilian cities over 24 months of operational history — applying a methodology and tech stack equivalent to real production environments.

The deliverable is not just a model. It is a **production-ready data platform**: a Telegram bot that any site manager can query on their phone, and a Streamlit simulator for real-time executive decision-making.

---

## 3. Analysis Assumptions

* The dataset is **synthetic**, generated using civil construction business rules (`scripts/gerar_dados.py`), with a fixed random seed (`numpy.random.seed(42)`) to ensure full reproducibility.
* The **target variable** is `dias_atraso` (delay days) — a continuous regression problem, not binary classification.
* Suppliers with a `rating_confiabilidade < 2.5` were classified as **high risk**, incurring a baseline delay penalty of +6 days during data generation.
* Foundation stage projects on clay soil received an additional penalty of +5.5 days — a rule derived from a civil engineering hypothesis validated during EDA.
* Records with `dias_atraso > 3 standard deviations` were removed as extreme outliers prior to model training.
* The simulated period covers 24 operational months; long-term seasonalities were not modeled in this release.

---

## 4. Solution Strategy

The project followed the complete Data Science framework, from problem definition to production deployment:

| Step | Description |
| --- | --- |
| **1. Business Problem** | Definition of the financial cost per delay day and model success criteria |
| **2. Data Generation & Architecture** | Synthetic dataset built with engineering rules; structured in layered architecture: `raw → analytics → products` |
| **3. Data Cleaning & Preprocessing** | Median imputation for weather variables; removal of extreme outliers in `dias_atraso` |
| **4. Hypothesis-Driven EDA** | Validation of 4 business hypotheses regarding delay root causes |
| **5. Feature Engineering** | Creation of a composite risk index: `supplier_rating × weather_condition` |
| **6. Machine Learning Preparation** | One-Hot Encoding for categorical variables; StandardScaler for continuous numerical features |
| **7. Training & Evaluation** | RandomForestRegressor with cross-validation; benchmarked against a historical mean baseline |
| **8. Business Performance** | Translation of technical MAE into estimated monetary financial impact (R$) |
| **9. Deployment** | Telegram Bot (Render) + Streamlit Simulator + Layered Database Architecture (Supabase) |

---

## 5. Data Cleaning and Preparation

* **Median Imputation** applied to missing values in weather variables — selected over the mean due to its robustness against extreme rainfall outliers.
* **Outlier Removal** in `dias_atraso` for values exceeding 3 standard deviations — atypical events that would distort model training without representing standard operations.
* **One-Hot Encoding** applied to categorical features: `tipo_solo` (soil type), `etapa` (stage), `cidade` (city), and `material`.
* **StandardScaler** applied to continuous numeric features: `orcamento_estimado` (estimated budget), `complexidade_obra` (complexity), `nivel_chuva` (rainfall level), `rating_confiabilidade` (reliability rating), and `taxa_insucesso_fornecedor` (supplier failure rate).
* **Composite Feature Creation:** `indice_risco = rating_fornecedor × nivel_chuva` — captures the amplifying impact of weather conditions on already underperforming suppliers.

---

## 6. Exploratory Data Analysis — Hypothesis Testing

The EDA was focused on **validating business hypotheses**, rather than simple visualization. Each hypothesis was tested prior to feature integration:

| Hypothesis | Result | Model Impact |
| --- | --- | --- |
| Is weather the main cause of delays? | ❌ False — Supplier rating has ~3x higher impact during finishing stages | Weather retained as a feature, but assigned lower relative weight than suppliers |
| Do low-rated suppliers cause delays even in good weather? | ✅ Confirmed | `rating_confiabilidade` became the model's most critical feature |
| Do higher-budget projects carry higher delay risk? | ✅ Projects over R$ 2M show higher sensitivity to cumulative delays | `orcamento_estimado` and `complexidade_obra` included as features |
| Is weather an isolated root cause? | ❌ Acts as an aggravating factor, rarely as the sole cause | Led to the creation of the composite index `rating × weather` |

**Action recommended by the model:**

> Prioritize renegotiating or replacing suppliers with ratings below 3.0 **before** taking action on weather or logistics-related interventions.

---

## 7. Model Training and Performance

**Selected Algorithm:** `RandomForestRegressor` — scikit-learn

**Why Random Forest instead of XGBoost?**
Random Forest was selected due to its superior interpretability via `feature_importances_` — essential when presenting model results to non-technical construction stakeholders. XGBoost was evaluated and yielded a marginal ~2% improvement in MAE at a significant cost to explainability.

| Metric | Baseline (Historical Mean) | Trained Model | Improvement |
| --- | --- | --- | --- |
| MAE | 12.0 days | **4.97 days** | **-59%** |
| RMSE | — | 6.3 days | — |
| R² | — | 0.41 | — |

**Regarding R² = 0.41:**
In civil construction, uncontrolled external variables — human decisions, supply chain volatility, extreme weather — are inherent to the operational domain. An R² above 0.4 represents a solid outcome in this environment. The key operational metric is achieving a **MAE below 5 days**, which was successfully hit.

---

## 8. Financial Impact (Business Performance)

> Each day of delay incurs approximately **R$ 1,380** in contractual fines (estimated average cost for the scale of simulated projects).

| Metric / Indicator | Result |
| --- | --- |
| Forecast Uncertainty Reduction | **~60%** |
| Residual Financial Risk per Project (MAE × Daily Cost) | **≈ R$ 6,860** |
| Estimated Potential Savings (Annual Portfolio) | **≈ R$ 248,400/year** |
| Decision Type Generated | **Preventive** — before financial loss occurs |

The primary objective is not merely predicting delays, but empowering the business to **act before costs materialize** — transforming a reactive operational problem into a strategic advantage.

---

## 9. Product in Production

### 🤖 Telegram Bot

Field managers can query project delay risks directly from their mobile phones, with no technical skills or system logins required:

1. Start interaction with `/start`
2. Select preferred language (**Portuguese** or **English**)
3. Select data source (**Local CSV** or **Supabase Cloud**)
4. Enter the Project ID (e.g., `CCBJJ-100`)
5. Instantly receive: **Risk Status + Explanatory Chart + Executive PDF Report**

### 📊 Streamlit Simulator

Executive dashboard interface for real-time sensitivity analysis:

* Interactive parameter adjustments via sidebar (city, stage, soil type, critical input material, rainfall level, supplier rating)
* Real-time visualization of **Estimated Delay** with clear risk tiers (🟢 Stable / 🟡 Alert / 🔴 Critical)
* Interactive chart for **Rainfall vs. Delay Simulation** (continuous curve)
* Interactive chart for **Geological Impact Analysis** (bar comparisons by soil type)
* Real-time calculation of **Opportunity Costs**

# 🏗️ Construction Delay Risk Analysis

### 🏛️ Data Architecture (Supabase)

```
Supabase (Layered Database)
├── raw
│   ├── atividades_obra         # Historical activity logs per stage
│   ├── fornecedores            # Supplier registry and performance ratings
│   └── clima                   # Accumulated rainfall levels by project
├── analytics
│   └── dashboard_obras         # Consolidated fact table for analytics
└── products
    └── base_consulta_bot       # Decoupled consumption layer (Bot + Streamlit)

```

**Benefits of layered architecture:** Enhanced data governance and traceability, decoupled consumption from source data, and seamless scalability for future data products without impacting ingestion pipelines.

---

## 10. Technical Decisions

| Decision | Choice | Evaluated Alternative | Rationale |
| --- | --- | --- | --- |
| Algorithm | Random Forest | XGBoost | Superior interpretability via `feature_importances_` for non-technical domain stakeholders |
| Database | Supabase | Local PostgreSQL | Free deployment offering native REST APIs and layered storage capability |
| Delivery Channel | Telegram Bot + Streamlit | BI Dashboard | Frictionless mobile access with no login required for site managers |
| Cloud Infrastructure | Render | AWS Lambda | Zero cost for current scope; native `Procfile` support |
| Data Source | Synthetic with Business Rules | Public Dataset | Enables full control over correlations and accurate testing of industry domain hypotheses |

**Accepted Trade-off:** Synthetic data offers analytical control but limits generalization to real-world production environments. The system architecture was engineered to allow seamless substitution with real enterprise data pipelines without requiring code refactoring.

---

## 11. Technologies Used

**Data Science & Machine Learning**

`Python 3.13` | `Pandas` | `NumPy` | `Scikit-learn` | `SciPy` | `Matplotlib` | `Seaborn` | `Plotly` | `Faker`

**Infrastructure & Deployment**

`Supabase` | `Render` | `Docker` | `FastAPI` | `Uvicorn` | `SQLAlchemy` | `Alembic`

**User Application Interfaces**

`Streamlit` | `Telegram Bot API (python-telegram-bot 21.0)` | `ReportLab` (PDF Generation)

**Utilities**

`python-dotenv` | `joblib` | `pytz` | `pg8000`

---

## 12. How to Run the Project

**Prerequisites:** Python 3.10+, Git, Telegram Account (for Bot interaction)

```bash
# 1. Clone the repository
git clone https://github.com/Santosdevbjj/analiseRiscosAtrasoObras
cd analiseRiscosAtrasoObras

# 2. Install required dependencies
pip install -r requirements.txt          # Streamlit + ML
pip install -r requirements_api.txt      # FastAPI + Bot + Database

# 3. Environment Variables Setup
# Create a .env file in the root directory containing:
# DATABASE_URL=your_supabase_url_here
# TELEGRAM_TOKEN=your_telegram_bot_token_here

# 4. Generate synthetic dataset
python scripts/gerar_dados.py

# 5. Launch Telegram Bot
python scripts/telegram_bot.py

# 6. Launch Streamlit Simulator
streamlit run app.py

```

> **Offline Mode (Without Supabase):** The system fully supports execution using local CSV files. Select "📂 Local CSV Mode" upon initiating the Telegram bot or set `USE_CSV=true` in your `.env` configuration.

---

## 13. Key Learnings & Insights

The primary challenge was **translating technical MAE metrics into defensible financial metrics for executive leadership.** Connecting a "4.97-day average error" to a "potential savings of R$ 248k/year" required rigorous mathematical modeling as well as clear storytelling to build operational trust.

Starting with the data before clearly articulating the business problem initially led to rework. Moving forward, defining problem scope, success criteria, and unit delay costs **prior** to opening a notebook is essential.

The most valued deliverable was not the machine learning model itself, but the **Telegram Bot and Streamlit Simulator** — making insights actionable for field decision-makers without technical barriers. A model usable only by a data scientist delivers limited business value.

---

## 14. Next Steps & Roadmap

* [ ] **Integration with Live Weather APIs** (OpenWeatherMap) to replace simulated data with real-time precipitation metrics by postal code
* [ ] **Data Drift Monitoring Implementation** with Evidently AI to monitor production data distribution shifts relative to training sets
* [ ] **Prediction Logging & Auditing** for historical tracking and continuous model retraining pipelines
* [ ] **Risk Classification Model Development** (High / Medium / Low) alongside regression for simplified alert notifications in the bot
* [ ] **Enhanced Financial Impact Calculation** customized by contract types (Fixed Price vs. Time & Materials) and geographic regions

---

## Repository Structure

```
analiseRiscosAtrasoObras/
├── data/
│   ├── raw/
│   │   ├── climaccbjj.csv                    # Weather records per project
│   │   ├── atividadesccbjj.csv               # Activity logs and stage statuses
│   │   ├── fornecedoresccbjj.csv             # Supplier database and ratings
│   │   ├── obrasccbjj.csv                    # Project master data
│   │   └── base_consulta_botccbjj.csv        # Consolidated lookup data for Bot & App
│   └── processed/
│       └── df_mestre_consolidado.csv.gz      # Preprocessed and compressed master dataset
├── models/
│   ├── pipeline_random_forest.pkl            # Serialized trained model pipeline
│   └── features_metadata.joblib              # Feature ordering mapping for inference
├── scripts/
│   ├── app.py                                # Streamlit Simulator (Executive Interface)
│   ├── gerar_dados.py                        # Synthetic dataset generator script
│   ├── telegram_bot.py                       # Telegram Bot script (Render Deployment)
│   ├── handlers.py                           # Bot command request handlers
│   ├── database.py                           # Postgres/SQLite database abstraction layer
│   └── i18n.py                               # PT/EN Internationalization module
├── notebooks/                                # EDA & Model Training Notebooks
├── requirements.txt                          # Streamlit + ML dependencies
├── requirements_api.txt                      # FastAPI + Bot + Database dependencies
├── requirements_streamlit.txt                # Streamlit Cloud deployment requirements
├── runtime.txt                               # python-3.13.4
├── Procfile                                  # web: python scripts/telegram_bot.py
└── README.md

```

---

**Author:** Sérgio Santos — Data Scientist | Critical Environments & Data Governance
