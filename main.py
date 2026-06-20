import logging
import pandas as pd

from src.extract          import run_extraction
from src.extract_ipeadata import run_extraction_ipeadata
from src.load             import run_load_and_transform, execute_analysis_query
from src.config           import RAW_DATA_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def run_pipeline():
    # ── 1. EXTRAÇÃO ──────────────────────────────────────────────────────────
    logging.info("=== ETAPA 1: EXTRAÇÃO ===")

    frames_bcb     = run_extraction()           # séries simples + compostas do BCB
    frames_ipeadata = run_extraction_ipeadata() # metais preciosos e câmbio (Ipeadata)

    all_frames = frames_bcb + frames_ipeadata

    if not all_frames:
        logging.error("Nenhum dado extraído. Pipeline interrompido.")
        return

    full_df = pd.concat(all_frames, ignore_index=True)
    full_df.to_csv(RAW_DATA_PATH, index=False)
    logging.info(f"Raw consolidado: {len(full_df):,} linhas → {RAW_DATA_PATH}")

    # ── 2. CARGA E TRANSFORMAÇÃO ─────────────────────────────────────────────
    logging.info("=== ETAPA 2: LOAD & TRANSFORM ===")
    run_load_and_transform()

    # ── 3. CRIAÇÃO DAS VIEWS ANALÍTICAS ─────────────────────────────────────
    logging.info("=== ETAPA 3: VIEWS ANALÍTICAS ===")
    execute_analysis_query()

    logging.info("=== PIPELINE CONCLUÍDO ===")


if __name__ == "__main__":
    run_pipeline()
