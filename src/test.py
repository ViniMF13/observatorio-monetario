# src/test_queries.py
import sqlite3
import pandas as pd

DB_PATH = "data/auditoria_moeda.db"

def testar_banco():
    print("Iniciando testes no banco de dados...\n")
    conn = sqlite3.connect(DB_PATH)
    
  
    
    conn.close()

if __name__ == "__main__":
    testar_banco()