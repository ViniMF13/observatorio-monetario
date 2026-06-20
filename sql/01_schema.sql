-- sql/01_schema.sql

-- ==============================================================================
-- 1. ENTIDADES DE METADADOS (Dimensões)
-- ==============================================================================

-- Tabela 1: CATEGORIA_ATIVO (Classifica a natureza econômica do dado)
CREATE TABLE IF NOT EXISTS Categoria (
    id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_categoria TEXT NOT NULL UNIQUE,
    descricao_categoria TEXT
);

-- Tabela 2: INDICADOR (O catálogo das séries do BCB)
CREATE TABLE IF NOT EXISTS Indicador (
    codigo_sgs INTEGER PRIMARY KEY,
    nome_indicador TEXT NOT NULL,
    unidade_medida TEXT NOT NULL,
    descricao_indicador TEXT,
    fk_id_categoria INTEGER,
    FOREIGN KEY (fk_id_categoria) REFERENCES categoria_ativo(id_categoria)
);

-- ==============================================================================
-- 2. ENTIDADE DE FATOS (Onde os valores históricos residem)
-- ==============================================================================

-- Tabela 3: VALOR_MENSAL (A série temporal normalizada via downsampling)
CREATE TABLE IF NOT EXISTS Registro (
    id_registro INTEGER PRIMARY KEY AUTOINCREMENT,
    data_registro TEXT NOT NULL,     -- Formato: YYYY-MM (ex: '1994-07')
    valor_registro REAL NOT NULL,
    fk_cod_sgs INTEGER NOT NULL,
    FOREIGN KEY (fk_cod_sgs) REFERENCES Indicador(codigo_sgs),
    
    -- Restrição de Integridade: Impede que o mesmo indicador tenha dois registros no mesmo mês
    UNIQUE(data_registro, fk_cod_sgs)
);

-- ==============================================================================
-- 3. ENTIDADES DE ANÁLISE CUSTOMIZADA (O Relacionamento M:N)
-- ==============================================================================

-- Tabela 4: CESTA_ANALITICA (Permite criar índices próprios, ex: "Hedge Proteção")
CREATE TABLE IF NOT EXISTS Cesta (
    id_cesta INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_cesta TEXT NOT NULL UNIQUE,
    descricao_cesta TEXT
);

-- Tabela 5: ITEM_CESTA (Tabela Associativa M:N entre Cesta e Indicador)
CREATE TABLE IF NOT EXISTS Item_Cesta (
    fk_id_cesta INTEGER NOT NULL,
    fk_cod_sgs INTEGER NOT NULL,
    peso_percentual REAL NOT NULL, -- Qual o peso desse indicador na cesta (0 a 100)
    
    PRIMARY KEY (fk_id_cesta, fk_cod_sgs),
    FOREIGN KEY (fk_id_cesta) REFERENCES Cesta(id_cesta) ON DELETE CASCADE,
    FOREIGN KEY (fk_cod_sgs) REFERENCES Indicador(codigo_sgs) ON DELETE CASCADE
);