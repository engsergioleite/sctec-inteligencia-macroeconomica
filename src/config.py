# ===== Configurações do projeto =====
from pathlib import Path

# ===== Caminhos relativos à raiz do projeto =====
RAIZ = Path(__file__).resolve().parent.parent
PASTA_RAW = RAIZ / "data" / "raw"
PASTA_PROCESSED = RAIZ / "data" / "processed"
ARQUIVO_BASE = PASTA_PROCESSED / "base_macro_mensal.csv"
ARQUIVO_QUALIDADE = PASTA_PROCESSED / "relatorio_qualidade.csv"
ARQUIVO_SECRETS = RAIZ / ".streamlit" / "secrets.toml"

# ===== Período obrigatório da Linha 3 =====
DATA_INICIAL = "01/01/2019"
DATA_FINAL = "31/12/2023"

# ===== Séries oficiais do SGS (código: nome da coluna) =====
SERIES = {
    432: "selic_meta",      # Meta Selic (% a.a.) - diária
    433: "ipca_mensal",     # IPCA mensal (%) - mensal
    13522: "ipca_12m",      # IPCA acumulado 12 meses (%) - mensal
    1: "dolar_ptax",        # Dólar venda (R$/US$) - diária
    24364: "ibc_br",        # IBC-Br dessazonalizado (índice) - mensal
}

# ===== Regra de agregação mensal das séries diárias =====
AGREGACAO_MENSAL = {
    "selic_meta": "last",   # meta vigente no fim do mês
    "dolar_ptax": "mean",   # média do mês
}

# ===== Nome da tabela no banco =====
TABELA = "base_macro_mensal"
