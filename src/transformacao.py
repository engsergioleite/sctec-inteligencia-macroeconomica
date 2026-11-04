# ===== Tratamento, agregação mensal e cálculo dos indicadores =====
import pandas as pd

from src.config import (AGREGACAO_MENSAL, ARQUIVO_BASE, ARQUIVO_QUALIDADE,
                        PASTA_PROCESSED, PASTA_RAW, SERIES)


# ===== Leitura e limpeza de uma série bruta =====
def limpar_serie(codigo, nome):
    caminho = PASTA_RAW / f"sgs_{codigo}_{nome}.csv"
    df = pd.read_csv(caminho, dtype=str, encoding="utf-8")
    linhas_brutas = len(df)

    # Conversão de tipos: data (dd/mm/aaaa) e valor (texto -> float)
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y", errors="coerce")
    df["valor"] = pd.to_numeric(df["valor"].str.replace(",", ".", regex=False), errors="coerce")
    nulos = int(df[["data", "valor"]].isna().any(axis=1).sum())

    # Remoção de nulos e duplicados por data
    df = df.dropna(subset=["data", "valor"])
    duplicados = int(df.duplicated(subset="data").sum())
    df = df.drop_duplicates(subset="data", keep="last").sort_values("data")

    qualidade = {"codigo_serie": codigo, "coluna": nome, "linhas_brutas": linhas_brutas,
                 "nulos_removidos": nulos, "duplicados_removidos": duplicados,
                 "linhas_finais": len(df)}
    return df[["data", "valor"]].rename(columns={"valor": nome}), qualidade


# ===== Padronização para frequência mensal =====
def para_mensal(df, nome):
    df = df.set_index("data")
    regra = AGREGACAO_MENSAL.get(nome, "last")
    return df.resample("MS").agg(regra)


# ===== Indicadores derivados =====
def calcular_indicadores(base):
    # Juro real ex-post (forma exata)
    base["juro_real_ex_post"] = ((1 + base["selic_meta"] / 100) / (1 + base["ipca_12m"] / 100) - 1) * 100

    # Variação do dólar em 12 meses (12 primeiros meses ficam nulos por definição)
    base["dolar_var_12m"] = base["dolar_ptax"].pct_change(12) * 100

    # Dólar acima da média do quinquênio
    base["dolar_acima_media"] = base["dolar_ptax"] > base["dolar_ptax"].mean()

    # Ciclo da Selic comparado ao mês anterior
    variacao = base["selic_meta"].diff().fillna(0)
    base["ciclo_selic"] = "Estável"
    base.loc[variacao > 0, "ciclo_selic"] = "Alta"
    base.loc[variacao < 0, "ciclo_selic"] = "Corte"
    return base


# ===== Montagem da base consolidada =====
def transformar():
    PASTA_PROCESSED.mkdir(parents=True, exist_ok=True)
    mensais, relatorio = [], []
    for codigo, nome in SERIES.items():
        df, qualidade = limpar_serie(codigo, nome)
        mensais.append(para_mensal(df, nome))
        relatorio.append(qualidade)

    # Junção das 5 séries pelo mês de referência
    base = pd.concat(mensais, axis=1).reset_index().rename(columns={"data": "data_ref"})
    base = base[(base["data_ref"] >= "2019-01-01") & (base["data_ref"] <= "2023-12-01")]
    base.insert(1, "ano", base["data_ref"].dt.year.astype(int))

    # Validação: 60 meses e nenhuma série principal nula
    principais = list(SERIES.values())
    assert len(base) == 60, f"Esperado 60 meses, encontrado {len(base)}"
    assert base[principais].isna().sum().sum() == 0, "Há meses sem valor nas séries principais"

    base = calcular_indicadores(base)
    numericas = base.select_dtypes("number").columns
    base[numericas] = base[numericas].round(4)
    base.to_csv(ARQUIVO_BASE, index=False, encoding="utf-8")
    pd.DataFrame(relatorio).to_csv(ARQUIVO_QUALIDADE, index=False, encoding="utf-8")
    print(pd.DataFrame(relatorio).to_string(index=False))
    print(f"[transformação] base consolidada: {len(base)} linhas -> {ARQUIVO_BASE.name}")
    return base


# ===== Execução direta =====
if __name__ == "__main__":
    transformar()
