# src/extract.py
import pandas as pd
import httpx
import logging
from src.config import SERIES_BCB, SERIES_COMPOSTAS, BCB_API_BASE_URL, RAW_DATA_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def _fetch_raw(serie_id: int) -> pd.DataFrame | None:
    """Busca o JSON bruto de uma série BCB e retorna apenas data + valor."""
    url = BCB_API_BASE_URL.format(id=serie_id)
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            return pd.DataFrame(response.json())   # colunas: data, valor
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP {e.response.status_code} ao buscar série {serie_id}: {e}")
    except Exception as e:
        logging.error(f"Erro inesperado ao buscar série {serie_id}: {e}")
    return None


def fetch_serie(serie_id: int) -> pd.DataFrame | None:
    """Busca uma série simples do BCB e adiciona seus metadados."""
    meta = SERIES_BCB[serie_id]
    logging.info(f"Extraindo {meta[0]} (SGS {serie_id})")

    df = _fetch_raw(serie_id)
    if df is None or df.empty:
        return None

    df['codigo_sgs']         = serie_id
    df['nome_indicador']     = meta[0]
    df['unidade_medida']     = meta[1]
    df['descricao_indicador'] = meta[2]
    df['id_categoria']       = meta[3]
    return df


def fetch_serie_composta(id_sintetico: int) -> pd.DataFrame | None:
    """
    Une duas ou mais séries BCB que cobrem o mesmo indicador em períodos
    distintos em um único DataFrame contínuo.

    Estratégia de sobreposição: para datas em que mais de uma série tem dado,
    mantém o valor da série mais recente (última na lista 'series_bcb').
    Isso respeita a hierarquia de revisão do BCB — a série nova é a canônica.
    """
    cfg = SERIES_COMPOSTAS[id_sintetico]
    logging.info(f"Compondo {cfg['nome_indicador']} (ID sintético {id_sintetico}) "
                 f"a partir das séries {cfg['series_bcb']}")

    frames = []
    for priority, sid in enumerate(cfg['series_bcb']):
        df = _fetch_raw(sid)
        if df is None or df.empty:
            logging.warning(f"  Série {sid} vazia ou inacessível — ignorada na composição.")
            continue
        df['_priority'] = priority   # maior = mais recente = preferido
        frames.append(df)

    if not frames:
        logging.error(f"Nenhuma série componente disponível para ID sintético {id_sintetico}.")
        return None

    combined = pd.concat(frames, ignore_index=True)

    # Para cada data, mantém apenas a linha de maior prioridade (série mais nova)
    combined = (
        combined
        .sort_values('_priority')
        .drop_duplicates(subset='data', keep='last')
        .drop(columns=['_priority'])
        .sort_values('data')
        .reset_index(drop=True)
    )

    combined['codigo_sgs']          = id_sintetico
    combined['nome_indicador']      = cfg['nome_indicador']
    combined['unidade_medida']      = cfg['unidade_medida']
    combined['descricao_indicador'] = cfg['descricao_indicador']
    combined['id_categoria']        = cfg['id_categoria']

    logging.info(f"  {cfg['nome_indicador']}: {len(combined)} observações "
                 f"({combined['data'].iloc[0]} → {combined['data'].iloc[-1]})")
    return combined


def run_extraction() -> list[pd.DataFrame]:
    """
    Orquestra a extração de séries simples e compostas do BCB.
    Retorna a lista de DataFrames para ser combinada pelo orquestrador em main.py.
    """
    all_data = []

    for serie_id in SERIES_BCB:
        df = fetch_serie(serie_id)
        if df is not None and not df.empty:
            all_data.append(df)

    for id_sintetico in SERIES_COMPOSTAS:
        df = fetch_serie_composta(id_sintetico)
        if df is not None and not df.empty:
            all_data.append(df)

    return all_data


if __name__ == "__main__":
    frames = run_extraction()
    if frames:
        pd.concat(frames, ignore_index=True).to_csv(RAW_DATA_PATH, index=False)
        logging.info(f"BCB: dados salvos em {RAW_DATA_PATH}")
