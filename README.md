# Observatório Monetário

**Análise empírica da diluição do poder de compra do Real desde o Plano Real (1994–2025)**

Projeto acadêmico desenvolvido para a disciplina de **Introdução a Banco de Dados — UFMG 2026/1**.

A tese central é a do **imposto inflacionário** sob a ótica da Escola Austríaca de Economia: a expansão da base monetária sem contrapartida em produção real é a causa primária da inflação, e seus efeitos redistributivos beneficiam desproporcionalmente os detentores de capital financeiro em detrimento dos trabalhadores assalariados — o **Efeito Cantillon**.

---

## Estrutura do Projeto

```
observatorio-monetario/
├── main.py                   # Orquestrador do pipeline ELT
├── app.py                    # Aplicação de apresentação (Streamlit)
├── sqlab.py                  # Laboratório SQL interativo (Streamlit)
├── Relatorio.ipynb           # Relatório acadêmico (Jupyter)
├── src/
│   ├── config.py             # Configuração das séries (BCB + Ipeadata)
│   ├── extract.py            # Extração BCB/SGS (incluindo séries compostas)
│   ├── extract_ipeadata.py   # Extração Ipeadata (OData 4)
│   └── load.py               # Carga, transformação e criação de views
├── sql/
│   ├── 01_schema.sql         # DDL: 5 tabelas normalizadas
│   ├── 02_staging.sql        # Tabela de staging temporária
│   ├── 03_transform.sql      # População das dimensões e tabela de fatos
│   └── 04_queries.sql        # Views analíticas (v_expansao_monetaria, v_aumento_precos, v_efeito_cantillon)
└── data/
    └── raw/                  # CSV consolidado (saída da extração)
```

---

## Pipeline ELT

```
BCB/SGS API ──┐
               ├──► sgs_data_bruto.csv ──► SQLite (staging) ──► Transform ──► Views
Ipeadata API ──┘
```

1. **Extract** — `src/extract.py` consome a API REST do BCB para cada código SGS. Séries com descontinuidade histórica são costuradas: dados da série antiga são usados até o início da série nova; onde há sobreposição, a série canônica (mais recente) prevalece. `src/extract_ipeadata.py` consome a API OData 4 do Ipeadata e normaliza as datas para o mesmo formato.

2. **Load** — todos os DataFrames são concatenados e salvos em `data/raw/sgs_data_bruto.csv`. O Pandas carrega o CSV na tabela `staging_sgs` do SQLite via `to_sql`.

3. **Transform** — `sql/03_transform.sql` popula as dimensões (`Categoria`, `Indicador`) e a tabela de fatos (`Registro`), normaliza as datas e descarta a staging. Em seguida, `sql/04_queries.sql` cria as views analíticas.

---

## Banco de Dados

Modelo relacional com 5 tabelas:

| Tabela | Descrição |
|--------|-----------|
| `Categoria` | Natureza econômica do indicador (monetária, inflação, produção…) |
| `Indicador` | Catálogo de séries com metadados (nome, unidade, descrição) |
| `Registro` | Tabela de fatos: valor mensal por indicador (`UNIQUE(data, cod_sgs)`) |
| `Cesta` | Agrupamento analítico customizado de indicadores |
| `Item_Cesta` | Tabela associativa M:N (Cesta × Indicador) com peso percentual |

### Views analíticas

| View | Pergunta respondida |
|------|-------------------|
| `v_expansao_monetaria` | Base Monetária, M1–M4 e PIB em Base 100 desde jul/1994 |
| `v_aumento_precos` | Índices de preços acumulados × produção real (Base 100) |
| `v_efeito_cantillon` | Capital financeiro (Selic, CDI, Ibovespa) vs. salários (Base 100) |

---

## Tecnologias

| Tecnologia | Uso |
|-----------|-----|
| Python 3.10+ | Extração e orquestração do pipeline |
| SQLite | Armazenamento relacional e transformações em SQL puro |
| Pandas | Manipulação e carga de dados |
| Streamlit | Visualização interativa (apresentação e laboratório SQL) |
| Plotly | Gráficos de séries temporais |
| httpx | Requisições HTTP às APIs públicas |

---

## Como Rodar

### 1. Clone o repositório

```bash
git clone https://github.com/ViniMF13/observatorio-monetario.git
cd observatorio-monetario
```

### 2. Crie o ambiente virtual e instale as dependências

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Execute o pipeline ELT

```bash
python main.py
```

Isso extrai os dados das APIs, carrega no SQLite e cria as views analíticas.

### 4. Apresentação — app de visualização

```bash
streamlit run app.py
```

Exibe os três módulos de análise: Expansão Monetária, Preços vs. Produção e Efeito Cantillon.

### 5. Laboratório SQL (opcional)

```bash
streamlit run sqlab.py
```

Ambiente interativo para explorar o banco, testar queries e inspecionar CTEs passo a passo.

---

## Fontes de Dados

| Fonte | API | Séries |
|-------|-----|--------|
| **Banco Central do Brasil (BCB/SGS)** | `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{id}/dados?formato=json` | Agregados monetários, IPCA, Selic, CDI, PIB, salários, produção industrial |
| **Ipeadata (IPEA)** | `http://ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='{codigo}')` | Ibovespa, produção de grãos, energia elétrica |

---

*Disciplina: Introdução a Banco de Dados — UFMG 2026/1*
