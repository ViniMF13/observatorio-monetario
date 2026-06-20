-- sql/03_transform.sql

-- ==============================================================================
-- PASSO 1: POPULAR AS DIMENSÕES MANUAIS (Categorias e Unidades)
-- ==============================================================================
-- Como o Banco Central não nos dá as "categorias", nós as criamos para nosso modelo.
-- O "INSERT OR IGNORE" garante que se rodarmos o script 10 vezes, não teremos dados duplicados.

INSERT OR IGNORE INTO Categoria (id_categoria, nome_categoria, descricao_categoria) VALUES
(1, 'Meio de Pagamento', 'Os meios de pagamentos amplos são indicadores antecedentes da demanda por moeda, constituindo-se em medida mais fidedigna da liquidez macroeconômica em relação aos agregados monetários restritos, que somente incluem o papel moeda em poder do público e os depósitos à vista.'),
(2, 'Inflação Oficial', 'Índices oficiais de inflação reportados pelo governo'),
(3, 'Commodities', 'Ativos e reservas de valor de aceitação internacional'),
(4, 'Renda', 'Métricas de remuneração básica da população'),
(5, 'Câmbio', 'Métricas de cotação de moedas estrangeiras'),
(6, 'Investimento', 'Passivos que remuneram detentores de títulos públicos'),
(7, 'Produção', 'Índices de produtividade e atividade econômica');


-- ==============================================================================
-- PASSO 2: POPULAR INDICADORES
-- ==============================================================================
-- Popula os Indicadores (Extraindo apenas os valores únicos da Staging)
-- Usamos INSERT IGNORE (ou ON CONFLICT DO NOTHING) para garantir idempotência.

INSERT OR IGNORE INTO Indicador (codigo_sgs, nome_indicador, unidade_medida, descricao_indicador, fk_id_categoria)
SELECT DISTINCT codigo_sgs, nome_indicador, unidade_medida, descricao_indicador, id_categoria
FROM staging_sgs;

-- ==============================================================================
-- PASSO 3: POPULAR A TABELA DE FATOS (REGISTRO)
-- ==============================================================================
-- Insere os dados da staging direto na tabela final, apenas ajustando o formato 
-- da data para o padrão de banco de dados (YYYY-MM-DD) para garantir a ordenação.

INSERT OR IGNORE INTO Registro (data_registro, valor_registro, fk_cod_sgs)
SELECT 
    -- Transforma '01/07/1994' em '1994-07-01'
    substr(data, 7, 4) || '-' || substr(data, 4, 2) || '-' || substr(data, 1, 2) AS data_registro,
    
    -- Garante que o valor seja tratado como número decimal e não como texto
    CAST(valor AS REAL) AS valor_registro,
    
    -- Mapeia a chave estrangeira
    codigo_sgs AS fk_cod_sgs
FROM staging_sgs
WHERE valor IS NOT NULL;

