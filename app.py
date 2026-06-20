import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="O Imposto Inflacionário",
    layout="wide",
    page_icon="📉",
    initial_sidebar_state="collapsed",
)

DB_PATH = "data/auditoria_moeda.db"

@st.cache_resource
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

@st.cache_data(ttl=300)
def load(_conn, sql):
    try:
        return pd.read_sql_query(sql, _conn), None
    except Exception as e:
        return None, str(e)

conn = get_conn()

# ==============================================================================
# PADRÃO DE MÓDULO
# título | descrição | toggle escala log | gráfico
# tabs: Estatísticas | SQL | Indicadores
# ==============================================================================
def render_modulo(titulo, descricao, df, x, y, cor, y_label, sql_query,
                  tabela_indicadores=None, key=""):
    st.header(titulo)
    st.markdown(descricao)

    if df is None or df.empty:
        st.warning("Sem dados disponíveis para esta view.")
        return

    log_y = st.checkbox("Escala logarítmica", key=f"log_{key}")

    fig = px.line(
        df, x=x, y=y, color=cor,
        labels={x: "Data", y: y_label, cor: "Série"},
        log_y=log_y,
    )
    fig.update_layout(
        height=500,
        margin=dict(t=20, b=10),
        legend=dict(orientation="h", y=-0.22),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    tab_stats, tab_sql, tab_ind = st.tabs(["Estatísticas", "SQL", "Indicadores"])

    with tab_stats:
        pivot = df.pivot_table(index=x, columns=cor, values=y)
        st.dataframe(pivot.describe().round(2), use_container_width=True)

    with tab_sql:
        st.code(sql_query.strip(), language="sql")

    with tab_ind:
        if tabela_indicadores:
            st.dataframe(
                pd.DataFrame(tabela_indicadores, columns=["Série", "Descrição"]),
                hide_index=True, use_container_width=True,
            )

# ==============================================================================
# CABEÇALHO
# ==============================================================================
st.title("O Imposto Inflacionário")
st.markdown(
    "Análise da diluição do poder de compra do Real desde o Plano Real (1994–2025). "
    "**Tese:** a expansão da base monetária sem lastro em produção real é a causa da inflação "
    "— e transfere riqueza dos trabalhadores para os detentores de capital financeiro."
)
st.divider()

# ==============================================================================
# MÓDULO 1 — EXPANSÃO MONETÁRIA
# ==============================================================================
SQL_M1 = "SELECT * FROM v_expansao_monetaria ORDER BY data_registro;"

COLS_M1 = {
    "base_monetaria_idx": "Base Monetária",
    "m1_idx": "M1",
    "m2_idx": "M2",
    "m3_idx": "M3",
    "m4_idx": "M4",
    "pib_nominal_idx": "PIB Nominal",
}

df_m1_raw, err = load(conn, SQL_M1)

if err:
    st.error(f"Erro módulo 1: {err}")
else:
    if df_m1_raw is not None:
        cols_disp = [c for c in COLS_M1 if c in df_m1_raw.columns]
        df_m1 = (
            df_m1_raw[["data_registro"] + cols_disp]
            .melt(id_vars="data_registro", var_name="serie", value_name="valor")
            .dropna()
        )
        df_m1["serie"] = df_m1["serie"].map(COLS_M1)

        render_modulo(
            titulo="1. A Causa — Expansão Monetária sem Lastro",
            descricao=(
                "Os agregados monetários medem a quantidade de dinheiro em circulação em diferentes "
                "níveis de liquidez. O PIB mede a riqueza real produzida. Todos reindexados para "
                "Base 100 em julho de 1994. Quando a moeda cresce muito mais rápido que o PIB, "
                "o excesso não representa nenhuma riqueza nova — apenas dilui o valor do dinheiro "
                "já existente. **O gap entre as curvas é a medida do roubo.**"
            ),
            df=df_m1,
            x="data_registro", y="valor", cor="serie",
            y_label="Índice (jul/1994 = 100)",
            sql_query=SQL_M1,
            key="m1",
            tabela_indicadores=[
                ("Base Monetária", "Emissão primária do Banco Central: papel-moeda em circulação + reservas bancárias."),
                ("M1",  "Base Monetária + depósitos à vista. Liquidez imediata — o dinheiro que você gasta hoje."),
                ("M2",  "M1 + poupança + títulos privados. Crédito que pode virar consumo rapidamente."),
                ("M3",  "M2 + cotas de fundos de investimento."),
                ("M4",  "M3 + títulos públicos federais. O agregado mais amplo — inclui a dívida do governo."),
                ("PIB Nominal", "Produto Interno Bruto nominal mensal. A riqueza real produzida pela economia."),
            ],
        )

st.divider()

# ==============================================================================
# MÓDULO 2 — AUMENTO DE PREÇOS vs. PRODUÇÃO
# ==============================================================================
SQL_M2 = "SELECT * FROM v_aumento_precos ORDER BY data_registro;"

COLS_PRECO = {
    "ipca_alimentacao_idx": "IPCA Alimentação",
    "ipca_habitacao_idx":   "IPCA Habitação",
    "ipca_residencia_idx":  "IPCA Residência",
    "ipca_vestuario_idx":   "IPCA Vestuário",
    "ipca_saude_idx":       "IPCA Saúde",
    "ipca_servicos_idx":    "IPCA Serviços",
    "igpm_idx":             "IGP-M",
    "inpc_idx":             "INPC",
}
COLS_PROD = {
    "producao_automoveis_idx": "Automóveis",
    "producao_petroleo_idx":   "Petróleo",
    "producao_aco_idx":        "Aço",
    "producao_graos_idx":      "Grãos",
    "producao_energia_idx":    "Energia Elétrica",
}

st.header("2. O Efeito — Preços Sobem, Produção Também. Mas os Preços Sobem Mais")
st.markdown(
    "Se a moeda fosse estável, o aumento da produção deveria **baratear** os bens ao longo do tempo. "
    "O fato de os preços terem subido centenas de vezes *apesar* do crescimento produtivo prova que "
    "a expansão monetária anulou e superou o ganho tecnológico da população."
)

df_ap_raw, err = load(conn, SQL_M2)

if err:
    st.error(f"Erro módulo 2: {err}")
elif df_ap_raw is not None:
    log_preco = st.checkbox("Escala logarítmica", key="log_m2")

    col_esq, col_dir = st.columns(2)

    with col_esq:
        st.subheader("Índices de Preços — Acumulado")
        st.caption("Variação % mensal transformada em índice multiplicativo (jul/1994 = 100).")
        cols_p = [c for c in COLS_PRECO if c in df_ap_raw.columns]
        df_preco = (
            df_ap_raw[["data_registro"] + cols_p]
            .melt(id_vars="data_registro", var_name="serie", value_name="valor")
            .dropna()
        )
        df_preco["serie"] = df_preco["serie"].map(COLS_PRECO)
        fig_p = px.line(df_preco, x="data_registro", y="valor", color="serie",
                        labels={"data_registro": "Data", "valor": "Índice (jul/1994=100)", "serie": "Índice"},
                        log_y=log_preco)
        fig_p.update_layout(height=440, margin=dict(t=10, b=10),
                            legend=dict(orientation="h", y=-0.32), hovermode="x unified")
        st.plotly_chart(fig_p, use_container_width=True)

    with col_dir:
        st.subheader("Produção Real — Base 100")
        st.caption("Produção física reindexada para Base 100 em jul/1994.")
        cols_pr = [c for c in COLS_PROD if c in df_ap_raw.columns]
        df_prod = (
            df_ap_raw[["data_registro"] + cols_pr]
            .melt(id_vars="data_registro", var_name="serie", value_name="valor")
            .dropna()
        )
        df_prod["serie"] = df_prod["serie"].map(COLS_PROD)
        fig_pr = px.line(df_prod, x="data_registro", y="valor", color="serie",
                         labels={"data_registro": "Data", "valor": "Índice (jul/1994=100)", "serie": "Setor"},
                         log_y=log_preco)
        fig_pr.update_layout(height=440, margin=dict(t=10, b=10),
                             legend=dict(orientation="h", y=-0.32), hovermode="x unified")
        st.plotly_chart(fig_pr, use_container_width=True)

    tab_stats_p, tab_stats_pr, tab_sql2, tab_ind2 = st.tabs(
        ["Estatísticas — Preços", "Estatísticas — Produção", "SQL", "Indicadores"]
    )
    with tab_stats_p:
        st.dataframe(df_ap_raw[cols_p].describe().round(2), use_container_width=True)
    with tab_stats_pr:
        st.dataframe(df_ap_raw[cols_pr].describe().round(2), use_container_width=True)
    with tab_sql2:
        st.code(SQL_M2.strip(), language="sql")
    with tab_ind2:
        st.dataframe(pd.DataFrame([
            ("IPCA Alimentação", "Variação % mensal dos preços de alimentos e bebidas no domicílio."),
            ("IPCA Habitação",   "Aluguel, condomínio e energia doméstica."),
            ("IPCA Residência",  "Artigos de residência: móveis, eletrodomésticos."),
            ("IPCA Vestuário",   "Roupas, calçados e acessórios."),
            ("IPCA Saúde",       "Medicamentos, planos de saúde e consultas."),
            ("IPCA Serviços",    "Educação, transporte e serviços em geral."),
            ("IGP-M",            "Índice Geral de Preços — reflete o atacado e a construção civil."),
            ("INPC",             "Índice Nacional de Preços — foco em famílias de baixa renda."),
            ("Automóveis",       "Produção mensal de automóveis e comerciais leves (unidades)."),
            ("Petróleo",         "Produção de derivados de petróleo (barris/dia, mil)."),
            ("Aço",              "Produção de aço bruto (índice base 1992=100)."),
            ("Grãos",            "Produção de grãos: soja, milho, trigo, feijão e outros (t, mil)."),
            ("Energia Elétrica", "Energia gerada para fins de eletricidade (Tep, mil)."),
        ], columns=["Série", "Descrição"]), hide_index=True, use_container_width=True)

st.divider()

# ==============================================================================
# MÓDULO 3 — EFEITO CANTILLON
# ==============================================================================
SQL_M3 = "SELECT * FROM v_efeito_cantillon ORDER BY data_registro;"

COLS_CANT = {
    "selic_idx":          "Selic (acumulada)",
    "cdi_idx":            "CDI (acumulado)",
    "ibovespa_idx":       "Ibovespa",
    "salario_real_idx":   "Salário Real",
    "salario_minimo_idx": "Salário Mínimo",
}

df_cant_raw, err = load(conn, SQL_M3)

if err:
    st.error(f"Erro módulo 3: {err}")
elif df_cant_raw is not None:
    cols_disp = [c for c in COLS_CANT if c in df_cant_raw.columns]
    df_cant = (
        df_cant_raw[["data_registro"] + cols_disp]
        .melt(id_vars="data_registro", var_name="serie", value_name="valor")
        .dropna()
    )
    df_cant["serie"] = df_cant["serie"].map(COLS_CANT)

    render_modulo(
        titulo="3. A Injustiça — Efeito Cantillon",
        descricao=(
            "**Richard Cantillon (1730):** quando nova moeda é criada, quem a recebe primeiro "
            "compra ativos antes dos preços subirem. Quem a recebe por último — o trabalhador, "
            "via salário — chega ao mercado com preços já inflados. "
            "Selic e CDI remuneram quem empresta dinheiro ao governo (títulos públicos). "
            "O Ibovespa remunera quem detém capital produtivo. "
            "Os salários remuneram quem vende trabalho. **Compare as trajetórias.**"
        ),
        df=df_cant,
        x="data_registro", y="valor", cor="serie",
        y_label="Índice (jul/1994 = 100)",
        sql_query=SQL_M3,
        key="m3",
        tabela_indicadores=[
            ("Selic (acumulada)",  "Taxa básica de juros acumulada via produto composto mensal. Remunera títulos públicos federais."),
            ("CDI (acumulado)",    "Taxa interbancária acumulada. Referência para renda fixa privada."),
            ("Ibovespa",           "Índice da Bolsa brasileira acumulado. Remunera o capital acionário."),
            ("Salário Real",       "Índice do salário real na indústria de transformação (jun/1994=100)."),
            ("Salário Mínimo",     "Valor nominal do salário mínimo reindexado para Base 100 em jul/1994."),
        ],
    )

st.divider()
st.caption("Dados: Banco Central do Brasil (SGS) · Ipeadata · Observatório Monetário — IBD 2025")
