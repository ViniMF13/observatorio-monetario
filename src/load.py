# src/load.py
import sqlite3
import pandas as pd
import logging
from src.config import RAW_DATA_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_PATH = "data/auditoria_moeda.db"

def execute_sql_script(cursor, script_path):
    """Lê e executa um arquivo .sql completo."""
    logging.info(f"Executando script SQL: {script_path}")
    try:
        with open(script_path, 'r', encoding='utf-8') as file:
            sql_script = file.read()
        cursor.executescript(sql_script)
    except Exception as e:
        logging.error(f"Erro ao executar {script_path}: {e}")
        raise

def execute_analysis_query():
    """Cria as views analíticas no banco."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        for script in ["sql/04_queries.sql", "sql/04_view.sql"]:
            import os
            if os.path.exists(script):
                execute_sql_script(cursor, script)
        conn.commit()
    except Exception as e:
        logging.error(f"Erro ao criar views: {e}")
    finally:
        conn.close()

def run_load_and_transform():
    logging.info("Iniciando processo de Carga e Transformação (ELT)...")
    
    # Conexão com o Banco de Dados
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Executa o DDL (Criação do Esquema Normalizado)
        execute_sql_script(cursor, "sql/01_schema.sql")
        
        # Load: Carrega o CSV bruto para a tabela Staging usando Pandas
        logging.info("Carregando CSV para a tabela staging_sgs...")
        df_raw = pd.read_csv(RAW_DATA_PATH)
        
        # O Pandas cria a tabela 'staging_sgs' dinamicamente a cada nova carga.
        df_raw.to_sql('staging_sgs', conn, if_exists='replace', index=False)
        
        # Transform: Executa a normalização (Staging -> Tabelas Finais)
        execute_sql_script(cursor, "sql/03_transform.sql")
        
        # Limpeza: Dropa a staging para não gastar espaço no disco
        cursor.execute("DROP TABLE staging_sgs;")
        logging.info("Tabela staging_sgs descartada.")
        
        # Confirma as transações
        conn.commit()
        logging.info("Processo ELT finalizado com sucesso! Banco normalizado e pronto para análises.")
        
    except Exception as e:
        conn.rollback()
        logging.error(f"Falha no processo ELT. Transação desfeita (Rollback): {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run_load_and_transform()