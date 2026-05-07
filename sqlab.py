# app_estudo.py
import streamlit as st
import sqlite3
import pandas as pd

# Configuração da página para focar na leitura de dados
st.set_page_config(page_title="Laboratório SQL - Modelagem", layout="wide")

DB_PATH = "data/auditoria_moeda.db"

def get_connection():
    """Cria conexão com o banco de dados"""
    return sqlite3.connect(DB_PATH)

def get_tables(conn):
    """Busca todas as tabelas criadas no banco (Catálogo do Sistema)"""
    query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    return pd.read_sql_query(query, conn)['name'].tolist()

def get_table_schema(conn, table_name):
    """Usa o comando PRAGMA para extrair os metadados da tabela"""
    query = f"PRAGMA table_info({table_name});"
    df_schema = pd.read_sql_query(query, conn)
    # PRAGMA retorna: cid, name, type, notnull, dflt_value, pk
    return df_schema[['name', 'type', 'pk', 'notnull']]

st.title("Laboratório de Modelagem e Consultas SQL")
st.markdown("Ambiente para explorar a estrutura do banco relacional e testar consultas analíticas.")

# --- NAVEGAÇÃO LATERAL ---
menu = st.sidebar.radio(
    "Explorar Banco de Dados:",
    ["O Esquema", "Explorador de Fatos", "Laboratório SQL (Queries)"]
)

conn = get_connection()
tabelas = get_tables(conn)

# ==========================================
# MÓDULO 1: O ESQUEMA RELACIONAL
# ==========================================
if menu == "O Esquema":
    st.header("Estrutura do Banco de Dados (Metadados)")
    st.markdown("Entender os **tipos de dados** e as **Chaves Primárias (PK)** é o primeiro passo para modelar cruzamentos complexos.")
    
    cols = st.columns(len(tabelas))
    for idx, tabela in enumerate(tabelas):
        with cols[idx]:
            st.subheader(f"Tabela: `{tabela}`")
            df_schema = get_table_schema(conn, tabela)
            
            # Formatação visual para destacar a PK
            df_schema['pk'] = df_schema['pk'].apply(lambda x: '🔑 Sim' if x > 0 else 'Não')
            df_schema['notnull'] = df_schema['notnull'].apply(lambda x: 'Obrigatório' if x == 1 else 'Opcional')
            
            st.dataframe(df_schema, hide_index=True)

# ==========================================
# MÓDULO 2: EXPLORADOR DE ENTIDADES
# ==========================================
elif menu == "Explorador de Fatos":
    st.header("Inspeção de Tuplas no Banco de Dados")
    st.markdown("Visualize o que exatamente está armazenado em cada entidade.")
    
    tabela_selecionada = st.selectbox("Selecione a Tabela para inspecionar:", tabelas)
    
    col1, col2 = st.columns([1, 3])
    with col1:
        limite = st.number_input("Limite de linhas", min_value=5, max_value=10000, value=100)
    
    with col2:
        query_explorador = f"SELECT * FROM {tabela_selecionada} LIMIT {limite}"
        df_dados = pd.read_sql_query(query_explorador, conn)
        st.dataframe(df_dados, use_container_width=True)
        
        st.caption(f"Exibindo {len(df_dados)} registro(s) da tabela '{tabela_selecionada}'.")

# ==========================================
# MÓDULO 3: LABORATÓRIO SQL
# ==========================================
elif menu == "Laboratório SQL (Queries)":
    st.header("3. Sandbox SQL")
    st.markdown("Escreva e teste suas consultas livremente. Erros de sintaxe serão capturados e exibidos para facilitar o debug.")
    
    

    # Sugestão de query para começar
    query_padrao = """-- Digite sua query aqui. Exemplo:
    SELECT i.nome, v.data_ref, v.valor 
    FROM valor_serie v
    JOIN indicador i ON v.fk_cod_sgs = i.cod_sgs
    LIMIT 10;"""

    query_usuario = st.text_area("Comando SQL:", value=query_padrao, height=200)
    
    if st.button("▶️ Executar Consulta"):
        try:
            # Executa a query digitada pelo usuário
            df_resultado = pd.read_sql_query(query_usuario, conn)
            
            st.success("Query executada com sucesso!")
            st.write(f"**Linhas retornadas:** {len(df_resultado)}")
            st.dataframe(df_resultado, use_container_width=True)
            
        except Exception as e:
            # Tratamento de erro crucial para aprendizado
            st.error("Erro de Sintaxe ou Lógica SQL:")
            st.code(e, language="text")

conn.close()