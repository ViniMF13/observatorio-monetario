Este projeto é uma ferramenta de Engenharia de Dados desenvolvida para analisar a evolução Econômica e Monetária do Brasil desde o início do Plano Real em 1994.

O sistema utiliza a API do SGS (Banco Central do Brasil) para extrair indicadores macroeconômicos e processá-los em um banco de dados relacional SQLite seguindo a arquitetura ELT (Extract, Load, Transform).

## 🚀 Tecnologias
* **Python 3.10+**: Extração e orquestração.
* **SQLite**: Armazenamento e transformações via SQL.
* **Pandas**: Manipulação de dados.
* **Streamlit**: Visualização de dados.


## 🔧 Como Rodar

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/ViniMF13/observatorio-monetario.git](https://github.com/ViniMF13/observatorio-monetari.git)
   cd observatorio-monetario

2. **Crie um ambiente virtual e instale as dependências::**
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   pip install -r requirements.txt

3. **Execute o Pipeline de Dados no main:**
   python main.py

4. **Visualise os dados com o Streamlit:**
   streamlit run sqlab.py