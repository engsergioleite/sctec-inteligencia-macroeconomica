# ===== Extração das séries da API SGS do Banco Central =====
import time

import pandas as pd
import requests

from src.config import DATA_FINAL, DATA_INICIAL, PASTA_RAW, SERIES

# ===== URL base da API (pública, sem chave) =====
URL_SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"


# ===== Extração de uma série =====
def extrair_serie(codigo, data_inicial=DATA_INICIAL, data_final=DATA_FINAL):
    parametros = {"formato": "json", "dataInicial": data_inicial, "dataFinal": data_final}
    resposta = requests.get(URL_SGS.format(codigo=codigo), params=parametros, timeout=30)
    resposta.raise_for_status()
    df = pd.DataFrame(resposta.json())
    df["codigo_serie"] = codigo
    return df


# ===== Extração de todas as séries e gravação em data/raw =====
def extrair_todas():
    PASTA_RAW.mkdir(parents=True, exist_ok=True)
    for codigo, nome in SERIES.items():
        df = extrair_serie(codigo)
        caminho = PASTA_RAW / f"sgs_{codigo}_{nome}.csv"
        df.to_csv(caminho, index=False)
        print(f"[extração] série {codigo} ({nome}): {len(df)} registros -> {caminho.name}")
        time.sleep(1)  # pausa para respeitar o servidor


# ===== Execução direta =====
if __name__ == "__main__":
    extrair_todas()
