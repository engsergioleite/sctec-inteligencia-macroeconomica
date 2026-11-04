# ===== Carga da base consolidada no Supabase (PostgreSQL) =====
import tomllib

import pandas as pd
from sqlalchemy import URL, create_engine, text

from src.config import ARQUIVO_BASE, ARQUIVO_SECRETS, TABELA


# ===== Leitura das credenciais do secrets.toml local =====
def ler_credenciais():
    with open(ARQUIVO_SECRETS, "rb") as arquivo:
        return tomllib.load(arquivo)["connections"]["postgresql"]


# ===== Conexão com o banco =====
def criar_engine():
    cfg = ler_credenciais()
    url = URL.create("postgresql+psycopg2", username=cfg["username"], password=cfg["password"],
                     host=cfg["host"], port=int(cfg["port"]), database=cfg["database"])
    return create_engine(url)


# ===== Envio da tabela e conferência =====
def carregar():
    df = pd.read_csv(ARQUIVO_BASE, parse_dates=["data_ref"])
    engine = criar_engine()
    df.to_sql(TABELA, engine, if_exists="replace", index=False)
    with engine.connect() as conn:
        total = conn.execute(text(f"SELECT COUNT(*) FROM {TABELA}")).scalar()
    print(f"[carga] tabela {TABELA} no Supabase: {total} linhas")


# ===== Execução direta =====
if __name__ == "__main__":
    carregar()
