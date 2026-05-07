from src.extract import run_extraction
from src.load import run_load_and_transform
from src.test import testar_banco



if __name__ == "__main__":

    # Extração dos dados do BCB
     run_extraction()
    
    # Carga e Transformação (ELT)
     run_load_and_transform()

    # testes de queries no database 
    # testar_banco() 
