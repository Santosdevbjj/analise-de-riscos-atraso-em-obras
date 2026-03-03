# 🏗️ Predição de Risco de Atraso em Obras

Plataforma analítica que antecipa riscos operacionais em obras civis, convertendo dados históricos em alertas preventivos e reduzindo exposição a multas contratuais.

> Projeto desenvolvido com dados sintéticos gerados a partir de hipóteses realistas do setor de construção civil, aplicando metodologia e stack equivalentes a ambientes produtivos reais.

---

## 1. Problema de Negócio

Empresas de construção civil perdem receita operacional em obras entregues fora do prazo — entre multas contratuais, replanejamento forçado e desgaste com clientes.

O problema não era falta de dados. Era falta de uso analítico dos dados existentes.

**Pergunta central:**
> Quais obras apresentam maior risco de atraso e onde devemos agir antes que o impacto financeiro ocorra?

---

## 2. Contexto

A operação envolve variáveis que impactam diretamente o prazo de entrega:

- Condições climáticas da região da obra
- Tipo e qualidade do solo
- Rating histórico de fornecedores
- Cronograma e complexidade das etapas da obra

Os dados existiam, mas as decisões eram tomadas de forma reativa — apenas após o atraso já ter ocorrido.

---

## 3. Premissas da Análise

- Dados sintéticos gerados com distribuições realistas do setor de construção civil
- A variável-alvo é o número de dias de atraso (problema de regressão)
- Fornecedores com rating abaixo de 3.0 foram classificados como alto risco
- Período simulado: 24 meses de histórico operacional
- A análise foca em identificação de padrões operacionais, não em causalidade estatística

---

## 4. Estratégia da Solução

### Pipeline Analítico

| Etapa | Descrição |
|---|---|
| 1. Problema de negócio | Entendimento do custo real de cada dia de atraso |
| 2. Arquitetura de dados | Organização em camadas: raw → analytics → products |
| 3. Limpeza e tratamento | Inconsistências em clima, solo e fornecedores |
| 4. EDA | Validação de hipóteses sobre causas de atraso |
| 5. Engenharia de atributos | Criação de índice de risco composto |
| 6. Treinamento do modelo | RandomForestRegressor com validação cruzada |
| 7. Avaliação | Técnica (MAE, R²) + impacto financeiro em R$ |
| 8. Deploy | Bot no Telegram + Simulador Streamlit em produção |

### Decisões Técnicas

| Decisão | Escolha | Alternativa Avaliada | Motivo |
|---|---|---|---|
| Algoritmo | Random Forest | XGBoost | Melhor interpretabilidade para stakeholders não técnicos |
| Banco de dados | Supabase | PostgreSQL local | Deploy gratuito com API REST nativa |
| Entrega ao usuário | Telegram Bot + Streamlit | Dashboard BI | Acessibilidade sem login para gestores de obra |
| Cloud | Render | AWS Lambda | Custo zero para o escopo do projeto |

---

## 5. Limpeza e Preparação dos Dados

- Imputação pela mediana em variáveis climáticas com valores ausentes
- Remoção de outliers extremos em dias de atraso (> 3 desvios padrão)
- One-Hot Encoding para variáveis categóricas (tipo de solo, condição climática)
- StandardScaler aplicado às variáveis numéricas contínuas
- Criação de feature composta: índice de risco por fornecedor × condição climática

---

## 6. Análise Exploratória — Principais Insights

A EDA foi orientada à validação de hipóteses de negócio, não apenas à visualização de dados.

| Hipótese | Resultado |
|---|---|
| Clima é a principal causa de atraso? | ❌ Falsa. Rating do fornecedor tem impacto ~3x maior em etapas de acabamento |
| Fornecedores com baixo rating atrasam mesmo em bom clima? | ✅ Confirmada |
| Obras de maior orçamento têm mais risco? | ✅ Obras acima de R$2M apresentam maior sensibilidade a atrasos acumulados |
| Clima é causa raiz isolada? | ❌ Atua como fator agravante, raramente como causa principal |

**Ação recomendada pelo modelo:**
Priorizar renegociação ou substituição de fornecedores com rating abaixo de 3.0 antes de qualquer intervenção relacionada a clima.

---

## 7. Performance do Modelo

**Algoritmo:** `RandomForestRegressor` — scikit-learn

| Métrica | Baseline (média histórica) | Modelo | Variação |
|---|---|---|---|
| MAE | 12 dias | 4,97 dias | -59% |
| RMSE | — | 6,3 dias | — |
| R² | — | 0,41 | — |

**Sobre o R² = 0,41:**
Em cenários de engenharia civil, variáveis externas não controladas — clima, cadeia de fornecedores, decisões humanas — são inerentes ao problema. R² acima de 0,4 é resultado consistente nesse contexto. A métrica de negócio relevante é o MAE inferior a 5 dias.

---

## 8. Impacto Financeiro (Business Performance)

> Cada dia de atraso representa aproximadamente R$ 1.380 em multas contratuais (custo médio estimado para o porte simulado).

| Indicador | Resultado |
|---|---|
| Redução de incerteza na previsão | ~60% |
| Risco financeiro residual por obra (MAE × custo/dia) | ≈ R$ 6.860 |
| Economia potencial estimada | ≈ R$ 248.400/ano |
| Tipo de decisão gerada | Preventiva — antes do impacto ocorrer |

O foco do projeto não é apenas prever atrasos. É permitir que a empresa aja antes que o custo se materialize.

---

## 9. Arquitetura em Produção

```
Supabase (banco de dados em camadas)
├── raw
│   ├── atividades_obra
│   ├── fornecedores
│   └── clima
├── analytics
│   └── dashboard_obras       # tabela fato consolidada
└── products
    └── base_consulta_bot     # camada de consumo desacoplada

Bot Telegram (hospedado no Render)
    └── Consulta por ID da obra
    └── Retorna: status de risco + gráfico + relatório PDF corporativo

Streamlit (simulador executivo)
    └── Interface para análise rápida de risco
    └── Apoio à decisão gerencial sem necessidade de perfil técnico
```

**Benefícios da arquitetura em camadas:**
- Governança e rastreabilidade dos dados
- Consumo desacoplado da origem
- Escalabilidade para novos produtos de dados

---

## 10. Tecnologias Utilizadas

**Dados e Machine Learning**
`Python` | `Pandas` | `NumPy` | `Scikit-learn` | `SciPy` | `Matplotlib` | `Seaborn`

**Infraestrutura e Deploy**
`Supabase` | `Render` | `Streamlit` | `Docker`

**Entrega ao Usuário**
`Telegram Bot API` | `FPDF` (relatório PDF)

---

## 11. Como Executar o Projeto

**Pré-requisitos**
- Python 3.10+
- Conta no Telegram (para o bot)
- Supabase configurado (opcional — o projeto também roda com CSV local)

**Instalação**
```bash
git clone https://github.com/Santosdevbjj/analiseRiscosAtrasoObras
cd analiseRiscosAtrasoObras
pip install -r requirements.txt
```

**Execução do Bot**
```bash
python scripts/telegram_bot.py
```

**Execução do Simulador**
```bash
streamlit run app.py
```

**Exemplo de uso no Bot**
1. Inicie com `/start`
2. Selecione idioma e fonte de dados (CSV ou Supabase)
3. Digite o ID da obra (ex: `CCBJJ-100`)
4. Receba: status de risco, gráfico explicativo e relatório PDF

---

## 12. Aprendizados

**O que foi mais difícil:**
Traduzir o MAE técnico em impacto financeiro real. Não é trivial conectar "erro médio de 5 dias" com "economia de R$ 248k/ano" de forma defensável para uma diretoria.

**O que faria diferente:**
Estruturaria o problema de negócio antes de abrir qualquer notebook. Comecei pelo dado e precisei voltar ao problema — o que custou tempo e retrabalho.

**Principal aprendizado:**
A entrega mais valorizada não foi o modelo. Foi o bot e o simulador — porque tornaram o resultado acessível para quem toma a decisão, sem depender de perfil técnico.

---

## 13. Próximos Passos

- [ ] Integração com API climática real (OpenWeather)
- [ ] Monitoramento de data drift com Evidently AI
- [ ] Logging de predições para retreinamento contínuo
- [ ] Modelo de classificação de risco (alto / médio / baixo) para alertas mais simples
- [ ] Expansão do cálculo de impacto financeiro por tipo de contrato

---

## Autor

**Sergio Santos**
Cientista de Dados | Ambientes Críticos e Governança de Dados

📧 santossergiorealbjj@outlook.com
🔗 [LinkedIn](https://www.linkedin.com/in/santossergioluiz)
🌐 [Portfólio](https://portfoliosantossergio.vercel.app)
