## 🏗️ Predição de Risco de Atraso em Obras

**Plataforma Analítica de Inteligência Operacional — CCbjj Engenharia & Inteligência de Risco** 


*Disciplina, estratégia e dados aplicados à engenharia civil.*

> Plataforma analítica que antecipa riscos operacionais em obras civis,
convertendo dados históricos em alertas preventivos e reduzindo
exposição a multas contratuais.


---

⚠️ **Disclaimer**

> Projeto desenvolvido com dados sintéticos gerados a partir de hipóteses realistas do setor de construção civil, aplicando metodologia e stack equivalentes a ambientes produtivos.



---

1️⃣ **Identidade do Projeto**

**Objetivo:**
Antecipar riscos de atraso em obras, permitindo ações preventivas antes que impactos financeiros e operacionais ocorram.

**Público-alvo:**
Gestores de obras, PMOs, diretoria operacional e áreas de planejamento.

**Entrega:**
Modelo preditivo + Bot no Telegram + Simulador Streamlit + Relatório PDF corporativo.


---

2️⃣ **Problema de Negócio**

Atrasos em obras geram impactos diretos:

Multas contratuais

Replanejamento forçado

Aumento de custos indiretos

Perda de credibilidade com clientes e investidores


Apesar de possuir dados históricos, a empresa não conseguia antecipar riscos com antecedência suficiente para agir.

👉 **Pergunta central:**

> Quais obras apresentam maior risco de atraso e onde devemos agir primeiro?




---

3️⃣ **Contexto Atual e Baseline**

📉 Situação Anterior (Baseline)

Decisões baseadas em média histórica

Erro médio de previsão ≈ 12 dias

Atuação reativa, após o atraso ocorrer


📈 **Proposta da Solução**

Modelo preditivo orientado a risco

Redução da incerteza para menos de 5 dias

Atuação preventiva, antes do impacto financeiro


👉 O projeto supera o baseline histórico, reduzindo drasticamente a variabilidade e o risco operacional.


---

4️⃣ **Arquitetura de Dados (Visão de Analytics Engineer)**

Arquitetura organizada em camadas analíticas, simulando ambiente corporativo real:

Supabase
├── raw
│   ├── atividadesccbjj        # Etapas da obra
│   ├── fornecedoresccbjj      # Fornecedores e ratings
│   ├── climaccbjj             # Dados climáticos
│
├── analytics
│   └── dashboard_obras        # Tabela fato analítica consolidada
│
└── products
    └── base_consulta_botccbjj # Camada de consumo (Bot / Streamlit)

Benefícios:

Governança

Escalabilidade

Reutilização

Consumo desacoplado da origem



---

5️⃣ **Estratégia da Solução (Pipeline Analítico)**

1. Entendimento da dor do negócio


2. Consolidação e padronização dos dados


3. Análise exploratória (EDA)


4. Engenharia de atributos orientada a risco


5. Treinamento do modelo preditivo


6. Avaliação técnica + impacto de negócio


7. Disponibilização em produto acessível




---

6️⃣ **Principais Insights Gerenciais** 💡

A análise exploratória revelou padrões relevantes:

🔹 O Rating do Fornecedor tem impacto ~3x maior no atraso do que o Nível de Chuva em etapas de acabamento

🔹 Fornecedores com histórico de baixa confiabilidade amplificam atrasos mesmo em cenários climáticos favoráveis

🔹 Obras com orçamento elevado apresentam maior sensibilidade a atrasos acumulados

🔹 Clima atua como fator agravante, mas raramente é a causa raiz isolada


👉 Esses insights direcionam ações práticas, como renegociação, substituição ou reforço de fornecedores críticos.


---

7️⃣ **Performance do Modelo (Técnica)**

Algoritmo: RandomForestRegressor

Justificativa:

Captura relações não lineares

Robustez a ruídos operacionais

Adequado para dados heterogêneos do mundo real



📊 **Métricas**

Métrica	Valor	Interpretação

MAE	4,97 dias	Erro médio inferior a 5 dias
R²	0,41	Boa explicação em ambiente volátil


👉 Resultado consistente para um cenário real de engenharia.


---

8️⃣ **Performance de Negócio** 💰

Indicador	Resultado

Redução de incerteza	~60%
Multas evitadas (estimado)	R$ 248.400 / ano
Tomada de decisão	Preventiva


O foco não é apenas prever, mas agir antes do problema ocorrer.


---

9️⃣ **Produto Final (Em Produção)**

🖥️ **Bot no Telegram**

Seleção de idioma (PT/EN)

Escolha da fonte de dados (CSV local ou Supabase)

Consulta por ID da obra

Retorno com:

Status de risco

Gráfico explicativo

Relatório PDF corporativo



📊 **Simulador Streamlit**

Interface executiva

Análise rápida de risco

Apoio à decisão gerencial



---

▶️ **Como Executar o Projeto**

Pré-requisitos

Python 3.10+

Conta no Telegram (para o bot)

Opcional: Supabase configurado


Instalação

pip install -r requirements.txt

Execução do Bot

python scripts/telegram_bot.py

Exemplo de Uso

1. Inicie o bot no Telegram com /start


2. Selecione idioma e modo de dados (CSV ou Supabase)


3. Digite o ID da obra (ex: CCBJJ-100)


4. Receba relatório detalhado, gráfico e PDF corporativo




---

🔮 **Próximos Passos**

Integração com API climática real

Monitoramento contínuo do modelo

Alertas automáticos de risco

Expansão do impacto financeiro detalhado


---

🎤 **Como Explicar Este Projeto em Entrevista**

  Estruturei os dados em camadas analíticas, criei uma tabela fato consolidada, desenvolvi um modelo preditivo e disponibilizei os resultados em um simulador e um bot. O foco foi apoiar decisões operacionais e reduzir risco financeiro, não apenas treinar um modelo.



---

🧾 **Conclusão:**

Este projeto demonstra:

✔ Visão de Analytics Engineer

✔ Capacidade de transformar dados em decisão

✔ Entrega de produto, não apenas modelo

✔ Comunicação clara entre técnico e negócio


👉 Não é apenas um projeto de Machine Learning. É uma solução de dados aplicada ao negócio.




---


**Autor:**
Sergio Santos 

---


## 📩 Contato



[![Portfólio Sérgio Santos](https://img.shields.io/badge/Portfólio-Sérgio_Santos-111827?style=for-the-badge&logo=githubpages&logoColor=00eaff)](https://santosdevbjj.github.io/portfolio/)
[![LinkedIn Sérgio Santos](https://img.shields.io/badge/LinkedIn-Sérgio_Santos-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/santossergioluiz) 



---



