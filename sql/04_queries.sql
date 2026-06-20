-- ==============================================================================
-- VIEW 1 — v_expansao_monetaria
-- "A Causa: emissão sem lastro"
--
-- Hipótese: A base monetária e os agregados M1–M4 cresceram de forma
-- exponencial e desproporcionalmente ao PIB real desde o Plano Real.
--
-- O GAP entre as curvas dos agregados monetários e a do PIB nominal
-- é a medida exata da diluição: dinheiro criado do nada que não representa
-- nenhuma riqueza nova — apenas redistribui poder de compra de quem já tinha
-- moeda para quem a recebeu primeiro.
--
-- Todos os indicadores reindexados para Base 100 em Jul/1994 para que a
-- comparação de crescimento relativo seja direta.
-- ==============================================================================
CREATE VIEW IF NOT EXISTS v_expansao_monetaria AS
WITH base AS (
    SELECT
        fk_cod_sgs,
        FIRST_VALUE(valor_registro) OVER (
            PARTITION BY fk_cod_sgs ORDER BY data_registro ASC
        ) AS valor_inicial
    FROM Registro
    WHERE data_registro >= '1994-07-01'
      AND fk_cod_sgs IN (1785, 90001, 90002, 90003, 90004, 4380)
    GROUP BY fk_cod_sgs, valor_registro, data_registro
),
primeiros AS (
    SELECT fk_cod_sgs, MIN(valor_inicial) AS valor_inicial
    FROM base
    GROUP BY fk_cod_sgs
),
indexado AS (
    SELECT
        r.data_registro,
        r.fk_cod_sgs,
        ROUND((r.valor_registro / p.valor_inicial) * 100, 2) AS indice_base100
    FROM Registro r
    JOIN primeiros p ON r.fk_cod_sgs = p.fk_cod_sgs
    WHERE r.data_registro >= '1994-07-01'
)
SELECT
    data_registro,
    MAX(CASE WHEN fk_cod_sgs = 1785  THEN indice_base100 END) AS base_monetaria_idx,
    MAX(CASE WHEN fk_cod_sgs = 90001 THEN indice_base100 END) AS m1_idx,
    MAX(CASE WHEN fk_cod_sgs = 90002 THEN indice_base100 END) AS m2_idx,
    MAX(CASE WHEN fk_cod_sgs = 90003 THEN indice_base100 END) AS m3_idx,
    MAX(CASE WHEN fk_cod_sgs = 90004 THEN indice_base100 END) AS m4_idx,
    MAX(CASE WHEN fk_cod_sgs = 4380  THEN indice_base100 END) AS pib_nominal_idx
FROM indexado
GROUP BY data_registro
ORDER BY data_registro;


-- ==============================================================================
-- VIEW 2 — v_aumento_precos
-- "O Efeito: preços sobem, produção também — mas os preços sobem mais"
--
-- Hipótese: os preços de bens e serviços se multiplicaram dezenas de vezes
-- desde 1994, mesmo com os enormes ganhos de produtividade e produção real.
-- Se a moeda fosse estável, o aumento de produção deveria baratear os bens.
-- O fato de os preços subirem apesar da produção crescer é a evidência de que
-- a expansão monetária anulou o ganho tecnológico da população.
--
-- Índices de preços: variação % mensal → índice acumulado via produto composto.
-- Índices de produção: reindexados para Base 100 em Jul/1994.
-- ==============================================================================
CREATE VIEW IF NOT EXISTS v_aumento_precos AS
WITH -- ── Acumula índices de inflação (% mensal → índice multiplicativo) ──────
precos_acum AS (
    SELECT
        data_registro,
        fk_cod_sgs,
        ROUND(
            EXP(SUM(LN(1.0 + valor_registro / 100.0)) OVER (
                PARTITION BY fk_cod_sgs ORDER BY data_registro ASC
            )) * 100,
        2) AS indice_acumulado
    FROM Registro
    WHERE data_registro >= '1994-07-01'
      AND fk_cod_sgs IN (1635, 1636, 1637, 1638, 1641, 10844,
                          7448, 7456, 7169, 192)
),
-- ── Reindexação da produção para Base 100 ───────────────────────────────────
prod_base AS (
    SELECT
        fk_cod_sgs,
        FIRST_VALUE(valor_registro) OVER (
            PARTITION BY fk_cod_sgs ORDER BY data_registro ASC
        ) AS valor_inicial
    FROM Registro
    WHERE data_registro >= '1994-07-01'
      AND fk_cod_sgs IN (1374, 1391, 7357, 91003, 91004)
    GROUP BY fk_cod_sgs, valor_registro, data_registro
),
prod_primeiro AS (
    SELECT fk_cod_sgs, MIN(valor_inicial) AS valor_inicial FROM prod_base GROUP BY fk_cod_sgs
),
prod_idx AS (
    SELECT
        r.data_registro,
        r.fk_cod_sgs,
        ROUND((r.valor_registro / p.valor_inicial) * 100, 2) AS indice_base100
    FROM Registro r
    JOIN prod_primeiro p ON r.fk_cod_sgs = p.fk_cod_sgs
    WHERE r.data_registro >= '1994-07-01'
)
SELECT
    COALESCE(pr.data_registro, pd.data_registro) AS data_registro,
    -- Inflação: índice acumulado (Jul/1994 = 100)
    MAX(CASE WHEN pr.fk_cod_sgs = 1635  THEN pr.indice_acumulado END) AS ipca_alimentacao_idx,
    MAX(CASE WHEN pr.fk_cod_sgs = 1636  THEN pr.indice_acumulado END) AS ipca_habitacao_idx,
    MAX(CASE WHEN pr.fk_cod_sgs = 1637  THEN pr.indice_acumulado END) AS ipca_residencia_idx,
    MAX(CASE WHEN pr.fk_cod_sgs = 1638  THEN pr.indice_acumulado END) AS ipca_vestuario_idx,
    MAX(CASE WHEN pr.fk_cod_sgs = 1641  THEN pr.indice_acumulado END) AS ipca_saude_idx,
    MAX(CASE WHEN pr.fk_cod_sgs = 10844 THEN pr.indice_acumulado END) AS ipca_servicos_idx,
    MAX(CASE WHEN pr.fk_cod_sgs = 7448  THEN pr.indice_acumulado END) AS igpm_idx,
    MAX(CASE WHEN pr.fk_cod_sgs = 7169  THEN pr.indice_acumulado END) AS inpc_idx,
    -- Produção: Base 100 em Jul/1994
    MAX(CASE WHEN pd.fk_cod_sgs = 1374  THEN pd.indice_base100 END) AS producao_automoveis_idx,
    MAX(CASE WHEN pd.fk_cod_sgs = 1391  THEN pd.indice_base100 END) AS producao_petroleo_idx,
    MAX(CASE WHEN pd.fk_cod_sgs = 7357  THEN pd.indice_base100 END) AS producao_aco_idx,
    MAX(CASE WHEN pd.fk_cod_sgs = 91003 THEN pd.indice_base100 END) AS producao_graos_idx,
    MAX(CASE WHEN pd.fk_cod_sgs = 91004 THEN pd.indice_base100 END) AS producao_energia_idx
FROM precos_acum pr
FULL OUTER JOIN prod_idx pd ON pr.data_registro = pd.data_registro
GROUP BY COALESCE(pr.data_registro, pd.data_registro)
ORDER BY data_registro;


-- ==============================================================================
-- VIEW 3 — v_efeito_cantillon
-- "A Injustiça: capital financeiro vs. trabalho"
--
-- Hipótese: quem detém capital financeiro (títulos públicos remunerados pela
-- Selic, ações na Bolsa) multiplica sua riqueza exponencialmente; quem vende
-- trabalho (salário real) praticamente fica no mesmo lugar.
--
-- Esse é o Efeito Cantillon: a moeda nova não chega a todos ao mesmo tempo.
-- Os primeiros a recebê-la (sistema bancário, governo, grandes tomadores de
-- crédito) compram ativos antes dos preços subirem. Os últimos a recebê-la
-- (trabalhadores, via salário) encontram preços já inflados.
--
-- Selic, CDI e Ibovespa: variação % mensal → índice acumulado.
-- Salário Real e Salário Mínimo: reindexados para Base 100 em Jul/1994.
-- ==============================================================================
CREATE VIEW IF NOT EXISTS v_efeito_cantillon AS
WITH -- ── Acumula ativos financeiros ───────────────────────────────────────────
financeiro AS (
    SELECT
        data_registro,
        fk_cod_sgs,
        ROUND(
            EXP(SUM(LN(1.0 + valor_registro / 100.0)) OVER (
                PARTITION BY fk_cod_sgs ORDER BY data_registro ASC
            )) * 100,
        2) AS indice_acumulado
    FROM Registro
    WHERE data_registro >= '1994-07-01'
      AND fk_cod_sgs IN (4390, 4391, 91002)   -- Selic, CDI, Ibovespa
),
-- ── Reindexação do salário para Base 100 ────────────────────────────────────
salario_base AS (
    SELECT
        fk_cod_sgs,
        FIRST_VALUE(valor_registro) OVER (
            PARTITION BY fk_cod_sgs ORDER BY data_registro ASC
        ) AS valor_inicial
    FROM Registro
    WHERE data_registro >= '1994-07-01'
      AND fk_cod_sgs IN (7351, 1619)
    GROUP BY fk_cod_sgs, valor_registro, data_registro
),
salario_primeiro AS (
    SELECT fk_cod_sgs, MIN(valor_inicial) AS valor_inicial FROM salario_base GROUP BY fk_cod_sgs
),
salario_idx AS (
    SELECT
        r.data_registro,
        r.fk_cod_sgs,
        ROUND((r.valor_registro / s.valor_inicial) * 100, 2) AS indice_base100
    FROM Registro r
    JOIN salario_primeiro s ON r.fk_cod_sgs = s.fk_cod_sgs
    WHERE r.data_registro >= '1994-07-01'
)
SELECT
    COALESCE(f.data_registro, s.data_registro) AS data_registro,
    -- Capital financeiro (índice acumulado)
    MAX(CASE WHEN f.fk_cod_sgs = 4390  THEN f.indice_acumulado END) AS selic_idx,
    MAX(CASE WHEN f.fk_cod_sgs = 4391  THEN f.indice_acumulado END) AS cdi_idx,
    MAX(CASE WHEN f.fk_cod_sgs = 91002 THEN f.indice_acumulado END) AS ibovespa_idx,
    -- Trabalho (Base 100)
    MAX(CASE WHEN s.fk_cod_sgs = 7351  THEN s.indice_base100 END)   AS salario_real_idx,
    MAX(CASE WHEN s.fk_cod_sgs = 1619  THEN s.indice_base100 END)   AS salario_minimo_idx
FROM financeiro f
FULL OUTER JOIN salario_idx s ON f.data_registro = s.data_registro
GROUP BY COALESCE(f.data_registro, s.data_registro)
ORDER BY data_registro;
