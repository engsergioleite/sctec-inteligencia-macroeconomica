# Inteligência Macroeconômica do Brasil (2019–2023)

> Data App em Streamlit que analisa Selic, inflação, câmbio e atividade econômica com dados oficiais do Banco Central.

**🔗 App:** [LINK_DO_STREAMLIT] · **🎥 Vídeo:** [LINK_DO_VIDEO] · **📋 Trello:** [LINK_DO_TRELLO]

---

## 1. Resumo executivo

Painel interativo que analisa como a política de juros do Banco Central se relacionou com inflação, câmbio e atividade econômica entre 2019 e 2023. O Brasil passou 20 meses com juro real negativo entre 2020 e 2022, e em 2023 o juro real chegou a 10,27% a.a., o maior do período.

## 2. Contexto de negócio e pergunta orientadora

Entre 2019 e 2023 o Brasil passou por Selic mínima histórica, choque cambial na pandemia, o ciclo de alta mais forte em décadas e o início da desinflação. Para um diretor financeiro, entender esse ciclo ajuda a decidir sobre custo de dívida, proteção cambial e planejamento de demanda.

**Pergunta orientadora:** como o ciclo de juros de 2019 a 2023 se relacionou com o custo real do dinheiro, o câmbio, a inflação e a atividade econômica?

Perguntas de negócio respondidas pelo app:

1. Como a Selic Meta evoluiu e quando o juro real ex-post foi mais alto?
2. Qual foi a trajetória do dólar PTAX e em que janelas ficou acima da média do quinquênio?
3. Há correlação visual e estatística entre alta do dólar e avanço do IPCA?
4. Como o IBC-Br se comportou nos períodos de alta e de corte da Selic?
5. Quais pares de variáveis têm as maiores correlações de Pearson?

## 3. Fonte de dados e licença

| Código SGS | Série                   | Frequência           | Unidade  |
| ----------- | ------------------------ | --------------------- | -------- |
| 432         | Meta Selic               | Diária               | % a.a.   |
| 433         | IPCA mensal              | Mensal                | %        |
| 13522       | IPCA acumulado 12 meses  | Mensal                | %        |
| 1           | Dólar comercial (venda) | Diária (dias úteis) | R$/US$ |
| 24364       | IBC-Br dessazonalizado   | Mensal                | Índice  |

- **Fonte:** API pública do Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil.
- **Período:** 01/01/2019 a 31/12/2023.
- **Extração:** `requests` na URL `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados`, com data inicial e final, uma chamada por série e pausa de 1 s entre chamadas.
- **Licença:** dados abertos do BCB, Open Data Commons Open Database License (ODbL).

## 4. Pipeline de engenharia de dados

```
API SGS ──► data/raw (5 CSVs brutos) ──► limpeza e tipagem ──► agregação mensal ──► indicadores ──► data/processed/base_macro_mensal.csv ──► Supabase (PostgreSQL)
```

1. **Extração** (`src/extracao.py`): baixa as 5 séries e grava cada uma em `data/raw`.
2. **Limpeza** (`src/transformacao.py`): converte datas `dd/mm/aaaa` para `datetime`, valores de texto para `float`, remove nulos e duplicados por data e registra tudo em `data/processed/relatorio_qualidade.csv`.
3. **Padronização mensal:** Selic = último valor do mês; dólar = média do mês; demais séries já são mensais.
4. **Validação:** a base precisa ter exatamente 60 meses e nenhum valor nulo nas 5 séries.
5. **Indicadores:** juro real ex-post, variação do dólar em 12 meses, flag de dólar acima da média e ciclo da Selic.
6. **Carga** (`src/carga.py`): envia a tabela `base_macro_mensal` ao Supabase via SQLAlchemy.

**Fórmula do juro real ex-post:** `((1 + Selic/100) / (1 + IPCA12M/100) − 1) × 100`

**Relatório de qualidade:**

## 5. Dicionário de dados

| Coluna            | Tipo     | Significado                                     | Regra de cálculo                                              |
| ----------------- | -------- | ----------------------------------------------- | -------------------------------------------------------------- |
| data_ref          | datetime | Primeiro dia do mês de referência             | Mês das séries (AAAA-MM-01)                                  |
| ano               | int      | Ano de referência                              | Extraído de `data_ref`                                      |
| selic_meta        | float    | Meta Selic vigente no fim do mês (% a.a.)      | Série 432, último valor do mês                              |
| ipca_mensal       | float    | Inflação do mês (%)                          | Série 433                                                     |
| ipca_12m          | float    | Inflação acumulada em 12 meses (%)            | Série 13522                                                   |
| dolar_ptax        | float    | Dólar médio do mês (R$/US$)                | Série 1, média mensal                                        |
| ibc_br            | float    | Índice de atividade econômica dessazonalizado | Série 24364                                                   |
| juro_real_ex_post | float    | Juro real efetivo (% a.a.)                      | Fórmula acima                                                 |
| dolar_var_12m     | float    | Variação do dólar em 12 meses (%)            | Variação contra 12 meses antes; nulo em 2019 por definição |
| dolar_acima_media | bool     | Dólar acima da média 2019–2023               | `dolar_ptax` > média do quinquênio                         |
| ciclo_selic       | str      | Alta, Corte ou Estável                         | Variação da Selic contra o mês anterior                     |

## 6. Tecnologias e bibliotecas

| Ferramenta                     | Uso                              | Por quê                                     |
| ------------------------------ | -------------------------------- | -------------------------------------------- |
| Python 3.11+                   | Linguagem do projeto             | Padrão de mercado em dados                  |
| requests                       | Chamadas à API do BCB           | Simples e com controle de timeout            |
| pandas / numpy                 | Limpeza, agregação e cálculos | Séries temporais com `resample`           |
| SQLAlchemy + psycopg2          | Carga no PostgreSQL              | Integração direta com `DataFrame.to_sql` |
| Supabase                       | PostgreSQL na nuvem              | Plano gratuito e acesso via pooler IPv4      |
| Streamlit                      | Data App                         | Interface interativa só com Python          |
| Plotly Express / Graph Objects | Gráficos                        | Interatividade (hover, zoom)                 |
| Streamlit Community Cloud      | Deploy                           | Publicação gratuita integrada ao GitHub    |
| Trello / Git / GitHub          | Gestão e versionamento          | Kanban e GitFlow exigidos no projeto         |

## 7. Principais resultados

[Para cada pergunta: 1 frase com número real + print do gráfico. Ex.: "O juro real atingiu X% a.a. em MM/AAAA, o maior do período."]

1. **Política monetária: a SELIC doi de 2% a 13,75%, o juro real ficou negativo de meados de 2020 ao inicio de 2022 (20 meses. com mínimo de -4,35% em 2021), e em 2023 chegou a 10,27%.
2. **Câmbio:** …
3. **Câmbio × inflação:** …
4. **Atividade:** …
5. **Correlações:** …

## 8. Discussão e limitações

- São apenas 60 observações mensais; correlações nessa amostra são instáveis.
- **Correlação não implica causalidade.** O app mostra associações, não efeitos causais.
- O choque da pandemia (2020) distorce médias e correlações do período.
- Juro real ex-post usa a inflação passada; não representa o juro real esperado.
- O IBC-Br é revisado periodicamente pelo BCB.
- O dólar mensal é uma média; picos diários não aparecem.

## 9. Aplicação profissional

- **CFO / tesouraria:** avaliar o custo real da dívida pós-fixada e o momento de trocar por prefixada.
- **Compras e importação:** identificar janelas de dólar acima da média para planejar hedge.
- **Planejamento comercial:** acompanhar o IBC-Br como termômetro de demanda em ciclos de juros altos.

## 10. Demonstração do Data App

**Link:** [LINK_DO_STREAMLIT]

![Visão geral](docs/img/app_visao_geral.png)

**Guia de navegação:**

- **Barra lateral:** período, ciclo da Selic, variáveis da correlação e botão *Resetar filtros*. O rodapé mostra a origem dos dados (Supabase ou CSV de contingência).
- **KPIs:** Selic, IPCA 12M, juro real e dólar no último mês do período, com variação contra 12 meses antes.
- **Abas:** Política monetária · Câmbio e inflação · Atividade econômica · Correlações · Dados (com download CSV).

## 11. Como executar localmente

```bash
git clone https://github.com/engsergioleite/sctec-inteligencia-macroeconomica.git
cd sctec-inteligencia-macroeconomica
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt

# Credenciais do Supabase (opcional: sem elas o app usa o CSV)
copy .streamlit\secrets.toml.example .streamlit\secrets.toml

# ETL completo (use --sem-carga para não enviar ao Supabase)
python pipeline.py

streamlit run app.py
```

## 12. Estrutura de pastas

```
├── .streamlit/        # tema (config.toml) e modelo de credenciais
├── data/raw/          # séries brutas da API SGS
├── data/processed/    # base mensal consolidada (também é o fallback do app)
├── docs/img/          # prints do app e do Trello
├── notebooks/         # análise exploratória
├── src/               # módulos de ETL: config, extração, transformação, carga
├── app.py             # Data App em Streamlit
├── pipeline.py        # executa o ETL de ponta a ponta
└── requirements.txt
```

## 13. Gestão ágil e links do projeto

- **Trello (Kanban):** [LINK_DO_TRELLO]
- **App em produção:** [LINK_DO_STREAMLIT]
- **Vídeo de apresentação:** [LINK_DO_VIDEO]

![Quadro do Trello](docs/img/trello.png)

Versionamento em GitFlow: `main` (estável), `develop` (integração) e uma `feature/*` por funcionalidade, com commits semânticos no imperativo.

## 14. Autoria e créditos

**Sérgio Fonseca Leite Junior** · [LinkedIn](LINK_LINKEDIN) · [GitHub](https://github.com/engsergioleite)

Projeto Avaliativo Final – Visualização de Dados e Business Intelligence – SCTEC / SENAI-SC.

**Referências**

- Banco Central do Brasil – Dados Abertos / API SGS: https://dadosabertos.bcb.gov.br
- Documentação do Streamlit: https://docs.streamlit.io
- Documentação do Plotly: https://plotly.com/python
- Documentação do Supabase: https://supabase.com/docs

**Uso de Inteligência Artificial no desenvolvimento**

[Descrever com honestidade: quais partes tiveram apoio de IA (ex.: estrutura do código, revisão, texto do README), o que você revisou, testou e adaptou, e o que aprendeu.]
