# src/extract.py
import pandas as pd
import httpx
import logging
from src.config import SERIES_BCB, BCB_API_BASE_URL, RAW_DATA_PATH

# Configuração básica de logging para monitorar a saúde da extração
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_serie(serie_id):
    """
    Busca uma série específica na API do BCB com tratamento de exceções.
    """
    url = BCB_API_BASE_URL.format(id=serie_id)
    logging.info(f"Iniciando extração da série {SERIES_BCB[serie_id][0]} (ID: {serie_id})")
    
    try:
        # Uso do httpx com timeout definido para evitar que o sistema trave
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status() # Levanta erro se o status não for 200
            
            data = response.json()
            df = pd.DataFrame(data)
            
            # Adição de metadados necessários para a normalização posterior
            df['codigo_sgs'] = serie_id
            df['nome_indicador'] = SERIES_BCB[serie_id][0] 
            df['unidade_medida'] = SERIES_BCB[serie_id][1] 
            df['descricao_indicador'] = SERIES_BCB[serie_id][2] 
            df['id_categoria'] = SERIES_BCB[serie_id][3]
            
            
            return df
            
    except httpx.HTTPStatusError as e:
        logging.error(f"Erro de status HTTP ao buscar {SERIES_BCB[serie_id][0]}: {e}") 
        
    except Exception as e:
        logging.error(f"Erro inesperado ao buscar {SERIES_BCB[serie_id][0]}: {e}")
    
    return None

def run_extraction():
    """
    Orquestra a extração de todas as séries definidas no config.
    """
    all_data = []
    
    for sid in SERIES_BCB.items():
        df = fetch_serie(sid[0]) 
        if df is not None and not df.empty:
            all_data.append(df)
    
    if all_data:
        # União de todos os DataFrames (Append vertical)
        full_df = pd.concat(all_data, ignore_index=True)
        
        # Persistência em disco (Camada de Staging/Raw)
        full_df.to_csv(RAW_DATA_PATH, index=False)
        logging.info(f"Extração concluída com sucesso. Dados salvos em {RAW_DATA_PATH}")
    else:
        logging.warning("Nenhum dado foi extraído.")

if __name__ == "__main__":
    run_extraction()