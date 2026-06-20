# src/config.py

# IDs das séries temporais no SGST do Banco Central
SERIES_BCB = { # ID: [Nome, Unidade de Medida, descrição, id da categoria]
    ### Agregados Monetário
    1785: ["BM", "milhares de u.m.c", "Dinheiro físico em circulação e reservas bancárias no Banco Central.", 1],

    ## Índices de Inflação Oficial
    1635: ["IPCA-A", "Variação % Mensal", "Indice de Preços ao Consumidor Amplo - Alimentação", 2],
    1636: ["IPCA-H", "Variação % Mensal", "Indice de Preços ao Consumidor Amplo - Habitação", 2],
    1637: ["IPCA-R", "Variação % Mensal", "Indice de Preços ao Consumidor Amplo - Artigos de Residencia", 2],
    1638: ["IPCA-V", "Variação % Mensal", "Indice de Preços ao Consumidor Amplo - Vestuario", 2],
    1641: ["IPCA-B", "Variação % Mensal", "Indice de Preços ao Consumidor Amplo - Bem estar e Saúde", 2],
    10844: ["IPCA-S", "Variação % Mensal", "Indice de Preços ao Consumidor Amplo - Serviços", 2],

    ## Câmbio
    11752: ["Câmbio", "Índice (Jun/1994=100)", "Índice da taxa de câmbio real efetiva", 5],
    11753: ["Câmbio Dólar", "Índice (Jun/1994=100)", "Índice da taxa de câmbio real. Dólar americano", 5],
    11775: ["Câmbio/Salário", "Índice (Jun/1994=100)", "Relação câmbio/salário", 5],
    7351:  ["Salário Real", "Índice (Jun/1994=100)", "Indústria de transformação. Salário Real", 5],
    3698:  ["Dólar", "u.m.c", "Cotação do Dólar Venda. Fechamento Mensal", 5],
    
    ## commodities
    7830: ["Ouro", "Variação % Mensal", "Índice de preços do ouro", 3],
           
    ## Índices de Preços
    7448: ["IGP-M", "Variação % Mensal", "Indice Geral de Preços no Atacado", 2],
    7456: ["INCC", "Variação % Mensal", "Indice de Preços na Construção Civil", 2],
    7169: ["INPC", "Variação % Mensal", "Indice de preços para o consumidor baixa Renda em Alimentação", 2],
    192:  ["ICV", "Variação % Mensal", "Índice nacional de custo da construção", 2],
    11777: ["UCL", "Índice (Jun/1994=100)", "Custo Unitário do Trabalho em US$", 2],
    206:  ["Cesta Básica", "u.m.c", "Valor nominal da Cesta Básica Nacional", 2],
    
    ## Produção 
    4380: ["PIB", "milhões de u.m.c", "PIB mensal - Valores correntes", 7],
    4385: ["PIB-U$", "milhões de Dólares", "PIB mensal em Dólares americanos", 7],
    1374: ["Automóveis", "Unidades", "Produção de automóveis e comerciais leves", 7],
    1391: ["Petróleo", "Barris/dia (mil)", "Produção de derivados de petróleo - Total", 7],
    7357: ["Aço", "Índice (1992=100)", "Produção de aço bruto", 7],
  
    ## Indicadores de Renda
    1619: ['Salário Mínimo', 'Reais', "Valor do Salário Mínimo Nacional pago no mês em questão", 4],
    
    ## investimentos
    4390: ['Selic', 'Variação % Mensal', "Taxa de juros nacional acumulada no mês", 6],
    4391: ['CDI', 'Variação % Mensal', "Taxa CDI. Fechamento Mensal", 6],

    ## Indicadores Fiscais
    2295: ['Déficit Nominal', 'Milhões de Reais', "Fluxo Mensal Nominal Consolidado. Transfer of funds from the National Treasury to states and municipalities (flows)", 6],
    4386: ['GDP', 'Milhões de Dolares', "Gross Production. Valor mensal do PIB em dólares", 7],
}

# URL base da API do BCB O endpoint completo é construído dinamicamente usando o ID da série
BCB_API_BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{id}/dados?formato=json&dataInicial=01/07/1994"

# Caminho para armazenamento do dado bruto
RAW_DATA_PATH = "data/raw/sgs_data_bruto.csv"

# ==============================================================================
# SÉRIES COMPOSTAS — BCB
# Quando um mesmo agregado é coberto por duas séries em períodos diferentes,
# definimos aqui a composição. O extractor une as duas priorizando a série
# mais nova em períodos de sobreposição e persiste sob um ID sintético.
# IDs sintéticos: 90001–90999 (fora do range real do SGS)
# ==============================================================================
SERIES_COMPOSTAS = {
    90001: {
        "nome_indicador":      "M1",
        "unidade_medida":      "Milhares de u.m.c",
        "descricao_indicador": "M1 composto: papel-moeda em poder do público e depósitos à vista. "
                               "Séries 1824 (jul/1994–dez/2000) + 27791 (jan/2001–atual).",
        "id_categoria": 1,
        "series_bcb": [1824, 27791],   # ordem: mais antiga → mais recente
    },
    90002: {
        "nome_indicador":      "M2",
        "unidade_medida":      "Milhares de u.m.c",
        "descricao_indicador": "M2 composto: M1 + poupança + títulos privados. "
                               "Séries 1837 (jul/1994–jun/2018) + 27810 (jul/2001–atual).",
        "id_categoria": 1,
        "series_bcb": [1837, 27810],
    },
    90003: {
        "nome_indicador":      "M3",
        "unidade_medida":      "Milhares de u.m.c",
        "descricao_indicador": "M3 composto: M2 + fundos de investimento + compromissadas. "
                               "Séries 1840 + 27813.",
        "id_categoria": 1,
        "series_bcb": [1840, 27813],
    },
    90004: {
        "nome_indicador":      "M4",
        "unidade_medida":      "Milhares de u.m.c",
        "descricao_indicador": "M4 composto: M3 + títulos públicos federais. "
                               "Séries 1843 + 27815.",
        "id_categoria": 1,
        "series_bcb": [1843, 27815],
    },
}

# ==============================================================================
# SÉRIES EXTERNAS — IPEADATA
# Séries do Instituto de Pesquisa Econômica Aplicada não disponíveis no BCB.
# API OData: http://ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='<cod>')
# IDs sintéticos: 91001–91999
# ==============================================================================
IPEADATA_SERIES = {
    "IFS12_OUROM12": {
        "id_sintetico":        91001,
        "nome_indicador":      "Ouro (USD/oz troy)",
        "unidade_medida":      "USD por onça troy",
        "descricao_indicador": "Cotação oficial do ouro — London Bullion Market Association (LBMA), "
                               "fixação da tarde (PM). Preço de referência global do metal.",
        "id_categoria": 3,
    },
    "GM12_IBVSP12": {
        "id_sintetico":        91002,
        "nome_indicador":      "Ibovespa)",
        "unidade_medida":      "Variação % Mensal",
        "descricao_indicador": "este caso, trata-se da variação acumulada mensal do índice calculado com seus valores de fechamento da série diária.",
        "id_categoria": 7,
    },
    "DEPAE_SAFRA": {
        "id_sintetico":        91003,
        "nome_indicador":      "Produção de grãos",
        "unidade_medida":      "Tonelada (mil)",
        "descricao_indicador": " Para grãos considera-se algodão, amendoim, arroz, aveia, canola, centeio, cevada, feijão, girassol, mamona, milho, soja, sorgo, trigo e triticale",
        "id_categoria": 5,
    },"MME_PETOT": {
        "id_sintetico":        91004,
        "nome_indicador":      "Produção de energia elétrica)",
        "unidade_medida":      "Tep (mil)",
        "descricao_indicador": "Quantidade de energia gerada para fins de geração de energia elétrica.",
        "id_categoria": 5,
    },
}
