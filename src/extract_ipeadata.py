# src/extract_ipeadata.py
import pandas as pd
import httpx
import logging
from src.config import IPEADATA_SERIES

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

_BASE_URL = "http://ipeadata.gov.br/api/odata4/ValoresSerie(SERCODIGO='{codigo}')"
_DATA_INICIAL = pd.Timestamp("1994-07-01")


def fetch_ipeadata(codigo: str) -> pd.DataFrame | None:
    """
    Baixa uma série do Ipeadata via API OData e retorna um DataFrame no
    esquema padrão do pipeline (colunas: data, valor, codigo_sgs,
    nome_indicador, unidade_medida, descricao_indicador, id_categoria).

    'data' é formatada como DD/MM/YYYY para compatibilidade com o
    03_transform.sql, que espera esse formato para gerar data_registro.
    """
    cfg = IPEADATA_SERIES[codigo]
    logging.info(f"Extraindo {cfg['nome_indicador']} ({codigo}) do Ipeadata")

    url = _BASE_URL.format(codigo=codigo)
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.get(url)
            response.raise_for_status()
            payload = response.json()
    except httpx.HTTPStatusError as e:
        logging.error(f"HTTP {e.response.status_code} ao buscar {codigo}: {e}")
        return None
    except Exception as e:
        logging.error(f"Erro ao buscar {codigo}: {e}")
        return None

    registros = payload.get("value", [])
    if not registros:
        logging.warning(f"Ipeadata retornou 0 registros para {codigo}.")
        return None

    df = pd.DataFrame(registros)[["VALDATA", "VALVALOR"]].copy()
    df = df.dropna(subset=["VALVALOR"])

    # VALDATA vem como ISO-8601 com timezone, ex: "1994-07-01T00:00:00-03:00"
    df["VALDATA"] = pd.to_datetime(df["VALDATA"], utc=True).dt.tz_localize(None)

    # Filtra janela temporal e converte para formato BCB (DD/MM/YYYY)
    df = df[df["VALDATA"] >= _DATA_INICIAL].copy()
    df["data"]  = df["VALDATA"].dt.strftime("%d/%m/%Y")
    df["valor"] = pd.to_numeric(df["VALVALOR"], errors="coerce")
    df = df.dropna(subset=["valor"])

    df["codigo_sgs"]          = cfg["id_sintetico"]
    df["nome_indicador"]      = cfg["nome_indicador"]
    df["unidade_medida"]      = cfg["unidade_medida"]
    df["descricao_indicador"] = cfg["descricao_indicador"]
    df["id_categoria"]        = cfg["id_categoria"]

    df = df[["data", "valor", "codigo_sgs", "nome_indicador",
             "unidade_medida", "descricao_indicador", "id_categoria"]]

    logging.info(f"  {cfg['nome_indicador']}: {len(df)} observações "
                 f"({df['data'].iloc[0]} → {df['data'].iloc[-1]})")
    return df


def run_extraction_ipeadata() -> list[pd.DataFrame]:
    """Extrai todas as séries definidas em IPEADATA_SERIES."""
    frames = []
    for codigo in IPEADATA_SERIES:
        df = fetch_ipeadata(codigo)
        if df is not None and not df.empty:
            frames.append(df)
    return frames


if __name__ == "__main__":
    from src.config import RAW_DATA_PATH
    frames = run_extraction_ipeadata()
    if frames:
        pd.concat(frames, ignore_index=True).to_csv(RAW_DATA_PATH, index=False)
        logging.info(f"Ipeadata: dados salvos em {RAW_DATA_PATH}")
