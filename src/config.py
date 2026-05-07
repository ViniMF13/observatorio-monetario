# src/config.py

# IDs das séries temporais no SGST do Banco Central
SERIES_BCB = { # ID: [Nome, Unidade de Medida, descrição, id da categoria]
    ### Agregados Monetário
    1785: ["Base Monetária", "Milhares de Unidades Monetarias", "A base monetária corresponde ao passivo monetário do Banco Central, também conhecido como emissão primária de moeda. Inclui a moeda em circulação e as reservas bancárias.", 1],
    1824: ["M1", "Milhares de Reais", "Papel-moeda em poder do público e depósitos à vista", 1], # 27788 27791 27841
    1837: ["M2", "Milhares de Reais", "M1 acrescido de Depósito de poupança e os Títulos privados emitidos pelas instituições depositárias", 1], # 27810, 27842 
    1840: ["M3", "Milhares de Reais", "M2 acrescido das as quotas de fundos de investimento depositários e as Operações compromissadas com títulos públicos e privados", 1], # 27813
    1843: ["M4", "Milhares de Reais", "M3 acrescido de títulos públicos emitidos pelo Governo Federal", 1], # 27815
    7478: ["IPCA", "Variação Percentual Mensal", "Indice de Preços ao Consumidor Amplo. Alimentação", 2],
    7448: ["IGP-M", "Variação Percentual Mensal", "Indice Geral de Preços no Atacado", 2],
    7456: ["INCC", "Variação Percentual Mensal", "Indice de Preços na Construção Civil", 2],
    7169: ["INPC", "Variação Percentual Mensal", "Indice de preços para o consumidor baixa Renda. Itens de Alimentação", 2],
    4: ['Ouro BM&F', 'Reais por grama', "Preço do Ouro em gramas no mercado BM&F", 3],
    3698: ["Dólar", "Reais", "Cotação do Dólar Venda. Fechamento Mensal", 5],
    1619: ['Salário Mínimo', 'Reais', "Valor do Salário Mínimo Nacional", 4],
    4390: ['Selic', 'Variação Percentual Mensal', "Taxa de juros nacional acumulada no mês", 6],
    4391: ['CDI', 'Variação Percentual Mensal', "Taxa CDI. Fechamento Mensal", 6],
    2295: ['Déficit Nominal', 'Milhões de Reais', "Fluxo Mensal Nominal Consolidado. Transfer of funds from the National Treasury to states and municipalities (flows)", 6],
    4386: ['GDP', 'Milhões de Dolares', "Gross Production. Valor mensal do PIB em dólares", 4],
}

# 6, 'Juros', 'Taxas de juros oficiais e de mercado'),;

# URL base da API do BCB
# BCB_API_BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{id}/dados?formato=json"
BCB_API_BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{id}/dados?formato=json&dataInicial=01/07/1994"

# Caminho para armazenamento do dado bruto
RAW_DATA_PATH = "data/raw/sgs_data_bruto.csv"