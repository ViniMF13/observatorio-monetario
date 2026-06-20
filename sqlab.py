import re
import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="SQLab — Observatório Monetário", layout="wide", page_icon="🔬")

DB_PATH = "data/auditoria_moeda.db"

# ==============================================================================
# HELPERS
# ==============================================================================

@st.cache_resource
def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def run_query(conn, sql: str) -> tuple:
    try:
        df = pd.read_sql_query(sql, conn)
        return df, None
    except Exception as e:
        return None, str(e)

def get_catalog(conn) -> dict:
    sql = "SELECT name, type FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%' ORDER BY type, name;"
    rows = conn.execute(sql).fetchall()
    return {r["name"]: r["type"] for r in rows}

def get_schema(conn, name: str) -> pd.DataFrame:
    df = pd.read_sql_query(f"PRAGMA table_info({name});", conn)
    return df[["name", "type", "pk", "notnull"]]

def get_row_count(conn, name: str) -> int:
    return conn.execute(f'SELECT COUNT(*) FROM "{name}";').fetchone()[0]

def get_indicadores(conn) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT codigo_sgs, nome_indicador, unidade_medida FROM Indicador ORDER BY nome_indicador;",
        conn
    )

def extract_ctes(sql: str) -> list[str]:
    """Extrai os nomes das CTEs de um bloco WITH ... AS."""
    return re.findall(r'\b(\w+)\s+AS\s*\(', sql, re.IGNORECASE)

def build_cte_query(full_sql: str, cte_name: str, limit: int = 200) -> str:
    """
    Dado um SQL com CTEs, monta uma query que executa todas as CTEs
    necessárias até cte_name e faz SELECT * nela.
    """
    # Encontra onde começa o WITH
    with_match = re.search(r'\bWITH\b', full_sql, re.IGNORECASE)
    if not with_match:
        return f"SELECT * FROM ({full_sql}) LIMIT {limit};"

    # Encontra onde começa o SELECT final (após todas as CTEs)
    # Estratégia: localiza o SELECT que não está dentro de parênteses
    ctes_text = full_sql[with_match.start():]

    # Conta parênteses para encontrar o SELECT final
    depth = 0
    final_select_pos = None
    i = 0
    in_with = False
    after_first_cte = False

    for i, ch in enumerate(ctes_text):
        if ch == '(':
            depth += 1
            after_first_cte = True
        elif ch == ')':
            depth -= 1
        elif depth == 0 and after_first_cte:
            # Procura SELECT no nível 0 após as CTEs
            remainder = ctes_text[i:]
            sel_match = re.match(r'\s*,?\s*(SELECT\b)', remainder, re.IGNORECASE)
            if sel_match and ctes_text[i-1:i] not in ('(', ','):
                # Verifica se é uma nova CTE (precedida de vírgula) ou o SELECT final
                prefix = ctes_text[max(0, i-20):i].strip()
                if prefix.endswith(')'):
                    final_select_pos = i
                    break

    if final_select_pos is not None:
        with_block = ctes_text[:final_select_pos].rstrip().rstrip(',')
    else:
        with_block = ctes_text

    return f"{with_block}\nSELECT * FROM {cte_name} LIMIT {limit};"


# ==============================================================================
# QUERIES DE EXEMPLO
# ==============================================================================

QUERIES_EXEMPLO = {
    "-- selecione --": "",
    "Série temporal: Salário Mínimo": """\
SELECT i.nome_indicador, r.data_registro, r.valor_registro
FROM Registro r
JOIN Indicador i ON r.fk_cod_sgs = i.codigo_sgs
WHERE r.fk_cod_sgs = 1619
  AND r.data_registro >= '1994-07-01'
ORDER BY r.data_registro;""",

    "Cobertura das séries por indicador": """\
SELECT i.nome_indicador, i.unidade_medida,
       COUNT(*)                AS total_meses,
       MIN(r.data_registro)    AS inicio,
       MAX(r.data_registro)    AS fim
FROM Registro r
JOIN Indicador i ON r.fk_cod_sgs = i.codigo_sgs
GROUP BY i.nome_indicador, i.unidade_medida
ORDER BY total_meses DESC;""",

    "View: Expansão Monetária": "SELECT * FROM v_expansao_monetaria;",
    "View: Perda de Poder de Compra": "SELECT * FROM v_perda_poder_de_compra;",
    "View: Efeito Cantillon": "SELECT * FROM v_efeito_cantillon;",
    "View: Déficit e Emissão": "SELECT * FROM v_deficit_e_emissao;",
    "View: Cesta vs Salário": "SELECT * FROM v_cesta_vs_salario;",
    "View: XAU/BRL (ouro em Reais)": "SELECT * FROM v_xau_brl;",
    "View: Poder de Compra em Ouro": "SELECT * FROM v_poder_compra_ouro;",

    "CTE exemplo — Base 100 manual": """\
WITH valores_base AS (
    SELECT
        fk_cod_sgs,
        FIRST_VALUE(valor_registro) OVER (
            PARTITION BY fk_cod_sgs ORDER BY data_registro ASC
        ) AS valor_inicial
    FROM Registro
    WHERE data_registro >= '1994-07-01'
      AND fk_cod_sgs IN (1619, 3698, 4)
),
indexado AS (
    SELECT
        r.data_registro,
        r.fk_cod_sgs,
        i.nome_indicador,
        ROUND((r.valor_registro / b.valor_inicial) * 100, 2) AS indice_base100
    FROM Registro r
    JOIN valores_base b   ON r.fk_cod_sgs = b.fk_cod_sgs
    JOIN Indicador    i   ON r.fk_cod_sgs = i.codigo_sgs
    WHERE r.data_registro >= '1994-07-01'
)
SELECT * FROM indexado
ORDER BY data_registro, fk_cod_sgs;""",
}

# ==============================================================================
# LAYOUT GLOBAL
# ==============================================================================

conn = get_connection()
catalog = get_catalog(conn)

st.sidebar.title("🔬 SQLab")
st.sidebar.caption("Observatório Monetário")

menu = st.sidebar.radio(
    "Módulo",
    ["Catálogo", "Inspetor de Dados", "Laboratório SQL", "Visualizador de Séries"],
    label_visibility="collapsed"
)

st.sidebar.divider()
tables = [n for n, t in catalog.items() if t == "table"]
views  = [n for n, t in catalog.items() if t == "view"]
st.sidebar.markdown(f"**Tabelas:** {len(tables)}  |  **Views:** {len(views)}")

# ==============================================================================
# MÓDULO 1 — CATÁLOGO
# ==============================================================================
if menu == "Catálogo":
    st.header("Catálogo do Banco de Dados")
    tab_t, tab_v = st.tabs(["Tabelas", "Views"])

    with tab_t:
        for name in tables:
            with st.expander(f"`{name}`  —  {get_row_count(conn, name):,} linhas"):
                schema = get_schema(conn, name).copy()
                schema["pk"]      = schema["pk"].apply(lambda x: "🔑" if x > 0 else "")
                schema["notnull"] = schema["notnull"].apply(lambda x: "✓" if x else "")
                schema.columns    = ["Coluna", "Tipo", "PK", "NOT NULL"]
                st.dataframe(schema, hide_index=True, use_container_width=True)
                ddl = conn.execute(f"SELECT sql FROM sqlite_master WHERE name = '{name}';").fetchone()["sql"]
                st.code(ddl, language="sql")

    with tab_v:
        if not views:
            st.info("Nenhuma view encontrada. Execute `sql/04_queries.sql` para criar as views analíticas.")
        for name in views:
            with st.expander(f"`{name}`"):
                ddl = conn.execute(f"SELECT sql FROM sqlite_master WHERE name = '{name}';").fetchone()["sql"]
                st.code(ddl, language="sql")

# ==============================================================================
# MÓDULO 2 — INSPETOR DE DADOS
# ==============================================================================
elif menu == "Inspetor de Dados":
    st.header("Inspetor de Dados")

    all_objects = tables + views
    selected = st.selectbox("Tabela ou View:", all_objects)

    col_limit, col_filter, col_sort = st.columns([1, 2, 2])
    with col_limit:
        limit = st.number_input("Linhas", min_value=10, max_value=50000, value=200, step=50)
    with col_filter:
        schema_cols = get_schema(conn, selected)["name"].tolist()
        filter_col  = st.selectbox("Filtrar coluna", ["(nenhum)"] + schema_cols)
    with col_sort:
        sort_col = st.selectbox("Ordenar por", ["(padrão)"] + schema_cols)

    where_clause = ""
    if filter_col != "(nenhum)":
        filter_val = st.text_input(f"Valor para `{filter_col}`:")
        if filter_val:
            where_clause = f'WHERE CAST("{filter_col}" AS TEXT) LIKE \'%{filter_val}%\''

    order_clause = "" if sort_col == "(padrão)" else f'ORDER BY "{sort_col}"'
    sql = f'SELECT * FROM "{selected}" {where_clause} {order_clause} LIMIT {limit};'

    df, err = run_query(conn, sql)
    if err:
        st.error(err)
    else:
        st.caption(f"{len(df):,} linhas  |  {len(df.columns)} colunas")
        st.dataframe(df, use_container_width=True, height=500)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇ Exportar CSV", csv, f"{selected}.csv", "text/csv")

# ==============================================================================
# MÓDULO 3 — LABORATÓRIO SQL
# ==============================================================================
elif menu == "Laboratório SQL":
    st.header("Laboratório SQL")

    # ── Referência lateral ──────────────────────────────────────────────────
    with st.sidebar.expander("Referência rápida", expanded=True):
        st.markdown("**Tabelas:** " + " · ".join(f"`{t}`" for t in tables))
        st.markdown("**Views:** " + " · ".join(f"`{v}`" for v in views))
        st.divider()
        try:
            ind_ref = get_indicadores(conn)
            st.dataframe(ind_ref, hide_index=True, height=350,
                         column_config={"codigo_sgs": "SGS", "nome_indicador": "Indicador", "unidade_medida": "Unidade"})
        except Exception:
            pass

    # ── Estado inicial ───────────────────────────────────────────────────────
    # A chave "lab_sql" é o único source-of-truth do conteúdo do editor.
    # O callback do selectbox escreve nela ANTES da renderização do text_area.
    if "lab_sql" not in st.session_state:
        st.session_state["lab_sql"] = QUERIES_EXEMPLO["CTE exemplo — Base 100 manual"]
    if "lab_result" not in st.session_state:
        st.session_state["lab_result"] = None  # DataFrame persistido entre reruns
    if "lab_error" not in st.session_state:
        st.session_state["lab_error"] = None

    # ── Seletor de exemplos (on_change atualiza o editor antes do render) ───
    def _load_example():
        sql = QUERIES_EXEMPLO.get(st.session_state["_exemplo_sel"], "")
        if sql:
            st.session_state["lab_sql"] = sql
            st.session_state["lab_result"] = None
            st.session_state["lab_error"] = None

    col_ex, col_clear = st.columns([4, 1])
    with col_ex:
        st.selectbox(
            "Carregar exemplo:",
            list(QUERIES_EXEMPLO.keys()),
            key="_exemplo_sel",
            on_change=_load_example,
        )
    with col_clear:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✕ Limpar", use_container_width=True):
            st.session_state["lab_sql"] = ""
            st.session_state["lab_result"] = None
            st.session_state["lab_error"] = None
            st.rerun()

    # ── Editor SQL ──────────────────────────────────────────────────────────
    sql_digitado = st.text_area(
        "SQL:",
        key="lab_sql",
        height=260,
        placeholder="Escreva sua query aqui...",
    )

    # ── Botões de ação ──────────────────────────────────────────────────────
    col_run, col_explain = st.columns([1, 1])
    executar = col_run.button("▶  Executar", type="primary", use_container_width=True)
    explicar = col_explain.button("🔍  EXPLAIN QUERY PLAN", use_container_width=True)

    sql_atual = st.session_state["lab_sql"].strip()

    if executar and sql_atual:
        df, err = run_query(conn, sql_atual)
        st.session_state["lab_result"] = df
        st.session_state["lab_error"]  = err

    if explicar and sql_atual:
        df_exp, err = run_query(conn, f"EXPLAIN QUERY PLAN {sql_atual}")
        if err:
            st.error(err)
        else:
            st.subheader("Plano de execução")
            st.dataframe(df_exp, use_container_width=True)

    # ── Resultado persistido ────────────────────────────────────────────────
    if st.session_state["lab_error"]:
        st.error("Erro SQL:")
        st.code(st.session_state["lab_error"], language="text")

    elif st.session_state["lab_result"] is not None:
        df = st.session_state["lab_result"]
        st.success(f"{len(df):,} linhas  ·  {len(df.columns)} colunas")

        tab_dados, tab_grafico, tab_stats = st.tabs(["Resultado", "Gráfico", "Estatísticas"])

        with tab_dados:
            st.dataframe(df, use_container_width=True, height=420)
            st.download_button(
                "⬇ CSV", df.to_csv(index=False).encode("utf-8"),
                "resultado.csv", "text/csv"
            )

        with tab_grafico:
            num_cols = df.select_dtypes("number").columns.tolist()
            all_cols = df.columns.tolist()
            if not num_cols:
                st.info("Sem colunas numéricas para plotar.")
            else:
                gc1, gc2, gc3 = st.columns(3)
                x_col     = gc1.selectbox("Eixo X", all_cols, index=0, key="g_x")
                y_cols    = gc2.multiselect("Eixo Y", num_cols,
                                             default=num_cols[:min(4, len(num_cols))], key="g_y")
                tipo      = gc3.selectbox("Tipo", ["Linha", "Área", "Barra", "Dispersão"], key="g_tipo")
                escala_log = gc3.checkbox("Escala log Y", key="g_log")

                if y_cols:
                    if tipo == "Linha":
                        fig = px.line(df, x=x_col, y=y_cols, log_y=escala_log)
                    elif tipo == "Área":
                        fig = px.area(df, x=x_col, y=y_cols, log_y=escala_log)
                    elif tipo == "Barra":
                        fig = px.bar(df, x=x_col, y=y_cols, barmode="group", log_y=escala_log)
                    else:
                        fig = px.scatter(df, x=x_col, y=y_cols[0], log_y=escala_log)
                    fig.update_layout(height=440, margin=dict(t=20, b=10))
                    st.plotly_chart(fig, use_container_width=True)

        with tab_stats:
            st.dataframe(df.describe(), use_container_width=True)

    # ── Inspetor de CTEs ────────────────────────────────────────────────────
    ctes = extract_ctes(sql_atual) if sql_atual else []
    if ctes:
        st.divider()
        st.subheader("Inspetor de CTEs")
        st.caption("Execute cada etapa da query isoladamente para verificar o resultado intermediário.")

        cols_cte = st.columns(min(len(ctes), 4))
        for idx, cte_name in enumerate(ctes):
            with cols_cte[idx % 4]:
                limit_cte = st.number_input(f"Limite `{cte_name}`", min_value=5, max_value=2000,
                                             value=50, step=50, key=f"lim_{cte_name}")
                if st.button(f"▶ {cte_name}", key=f"btn_{cte_name}", use_container_width=True):
                    cte_sql = build_cte_query(sql_atual, cte_name, limit_cte)
                    st.session_state[f"cte_result_{cte_name}"] = run_query(conn, cte_sql)
                    st.session_state[f"cte_sql_{cte_name}"] = cte_sql

        for cte_name in ctes:
            result_key = f"cte_result_{cte_name}"
            sql_key    = f"cte_sql_{cte_name}"
            if result_key in st.session_state:
                df_cte, err_cte = st.session_state[result_key]
                with st.expander(f"Resultado de `{cte_name}`", expanded=True):
                    with st.container():
                        st.code(st.session_state.get(sql_key, ""), language="sql")
                    if err_cte:
                        st.error(err_cte)
                    else:
                        st.caption(f"{len(df_cte):,} linhas  ·  {len(df_cte.columns)} colunas")
                        st.dataframe(df_cte, use_container_width=True)

# ==============================================================================
# MÓDULO 4 — VISUALIZADOR DE SÉRIES
# ==============================================================================
elif menu == "Visualizador de Séries":
    st.header("Visualizador de Séries Temporais")
    st.caption("Explore qualquer combinação de indicadores diretamente da tabela `Registro`.")

    try:
        ind_df = get_indicadores(conn)
    except Exception as e:
        st.error(f"Erro ao carregar indicadores: {e}")
        st.stop()

    opcoes = {
        f"{row['nome_indicador']}  [{row['unidade_medida']}]  (#{row['codigo_sgs']})": row["codigo_sgs"]
        for _, row in ind_df.iterrows()
    }

    selecionados = st.multiselect(
        "Indicadores:",
        list(opcoes.keys()),
        default=list(opcoes.keys())[:2] if len(opcoes) >= 2 else list(opcoes.keys()),
    )

    col_d1, col_d2, col_norm, col_log = st.columns([2, 2, 1, 1])
    data_ini   = col_d1.date_input("De",  value=pd.Timestamp("1994-07-01"))
    data_fim   = col_d2.date_input("Até", value=pd.Timestamp("today"))
    normalizar = col_norm.checkbox("Base 100", value=False)
    escala_log = col_log.checkbox("Escala log", value=False)

    if not selecionados:
        st.info("Selecione ao menos um indicador.")
        st.stop()

    ids     = [opcoes[s] for s in selecionados]
    ids_str = ", ".join(str(i) for i in ids)

    sql_series = f"""\
SELECT r.data_registro, r.valor_registro, i.nome_indicador, i.unidade_medida
FROM Registro r
JOIN Indicador i ON r.fk_cod_sgs = i.codigo_sgs
WHERE r.fk_cod_sgs IN ({ids_str})
  AND r.data_registro BETWEEN '{data_ini}' AND '{data_fim}'
ORDER BY r.data_registro;"""

    df_s, err = run_query(conn, sql_series)
    if err:
        st.error(err)
        st.stop()

    if df_s.empty:
        st.warning("Sem dados para o período e indicadores selecionados.")
        st.stop()

    if normalizar:
        def reindex(g):
            primeiro = g.loc[g["data_registro"].idxmin(), "valor_registro"]
            g = g.copy()
            g["valor_registro"] = (g["valor_registro"] / primeiro) * 100
            return g
        df_s = df_s.groupby("nome_indicador", group_keys=False).apply(reindex)

    fig = px.line(
        df_s,
        x="data_registro",
        y="valor_registro",
        color="nome_indicador",
        labels={"data_registro": "Data", "valor_registro": "Valor", "nome_indicador": "Indicador"},
        log_y=escala_log,
    )
    fig.update_layout(height=520, margin=dict(t=20, b=20), legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("Ver dados brutos"):
        st.dataframe(df_s, use_container_width=True, height=300)
        csv = df_s.to_csv(index=False).encode("utf-8")
        st.download_button("⬇ CSV", csv, "series.csv", "text/csv")
