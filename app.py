# ===== Data App: Inteligência Macroeconômica (BACEN/SGS 2019-2023) =====
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ===== Configuração da página =====
st.set_page_config(page_title="Inteligência Macroeconômica", page_icon="📈", layout="wide")

# ===== Caminho relativo do CSV de contingência =====
CAMINHO_CSV = Path(__file__).parent / "data" / "processed" / "base_macro_mensal.csv"

# ===== Constantes de interface =====
CICLOS = ["Alta", "Corte", "Estável"]
VARIAVEIS = {
    "selic_meta": "Selic Meta",
    "ipca_12m": "IPCA 12M",
    "ipca_mensal": "IPCA mensal",
    "juro_real_ex_post": "Juro real",
    "dolar_ptax": "Dólar PTAX",
    "ibc_br": "IBC-Br",
}
PADRAO = {"periodo": (2019, 2023), "ciclos": CICLOS, "variaveis": list(VARIAVEIS.keys())}
COR_SELIC, COR_IPCA, COR_JURO, COR_DOLAR = "#1f4e79", "#c0392b", "#7f8c8d", "#2e7d32"


# ===== Carga dos dados com cache e contingência =====
@st.cache_data(ttl=3600, show_spinner="Carregando dados...")
def carregar_dados():
    try:
        conn = st.connection("postgresql", type="sql")
        df = conn.query("SELECT * FROM base_macro_mensal ORDER BY data_ref", ttl=3600)
        origem = "Supabase (PostgreSQL na nuvem)"
    except Exception:
        df = pd.read_csv(CAMINHO_CSV)
        origem = "CSV local (contingência)"
    df["data_ref"] = pd.to_datetime(df["data_ref"])
    df["ano"] = df["data_ref"].dt.year
    return df, origem


# ===== Matriz de correlação com cache =====
@st.cache_data(ttl=3600)
def calcular_correlacao(df, colunas):
    return df[colunas].corr(method="pearson").round(2)


# ===== Blocos contínuos de cada ciclo (para sombrear gráficos) =====
def blocos_ciclo(df, ciclo):
    marcado = (df["ciclo_selic"] == ciclo).astype(int)
    grupos = (marcado.diff() != 0).cumsum()
    blocos = []
    for _, bloco in df[marcado == 1].groupby(grupos[marcado == 1]):
        blocos.append((bloco["data_ref"].min(), bloco["data_ref"].max() + pd.offsets.MonthEnd(0)))
    return blocos


# ===== Formatação numérica no padrão brasileiro =====
def br(valor, casas=2):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# ===== Layout padrão dos gráficos =====
def layout_padrao(fig, titulo, eixo_y):
    fig.update_layout(title=titulo, yaxis_title=eixo_y, xaxis_title="", separators=",.",
                      legend=dict(orientation="h", y=-0.2), hovermode="x unified",
                      margin=dict(t=60, b=40))
    return fig


# ===== Dados =====
dados, origem = carregar_dados()

# ===== Estado inicial dos filtros =====
for chave, valor in PADRAO.items():
    st.session_state.setdefault(chave, valor)


# ===== Função do botão Resetar =====
def resetar_filtros():
    for chave, valor in PADRAO.items():
        st.session_state[chave] = valor


# ===== Sidebar: filtros =====
st.sidebar.header("Filtros")
st.sidebar.slider("Período (anos)", 2019, 2023, key="periodo")
st.sidebar.multiselect("Ciclo da Selic", CICLOS, key="ciclos",
                       help="Alta, Corte ou Estável em relação ao mês anterior")
st.sidebar.multiselect("Variáveis da correlação", list(VARIAVEIS.keys()), key="variaveis",
                       format_func=lambda c: VARIAVEIS[c])
st.sidebar.button("Resetar filtros", on_click=resetar_filtros, width="stretch")
st.sidebar.divider()
st.sidebar.caption(f"Fonte: API SGS do Banco Central  \nOrigem dos dados: **{origem}**")

# ===== Aplicação dos filtros =====
ano_ini, ano_fim = st.session_state["periodo"]
filtrado = dados[dados["ano"].between(ano_ini, ano_fim)]
filtrado_ciclo = filtrado[filtrado["ciclo_selic"].isin(st.session_state["ciclos"])]

# ===== Cabeçalho =====
st.title("Inteligência Macroeconômica do Brasil")
st.markdown(f"Selic, inflação, câmbio e atividade econômica de **{ano_ini} a {ano_fim}**, "
            "com dados oficiais do Banco Central (SGS).")

if filtrado.empty:
    st.warning("Nenhum dado para os filtros escolhidos. Use **Resetar filtros**.")
    st.stop()

# ===== KPIs: último mês do período vs. 12 meses antes (ou início do período) =====
atual = filtrado.iloc[-1]
base_comp = filtrado.iloc[-13] if len(filtrado) >= 13 else filtrado.iloc[0]
rotulo = "vs. 12 meses antes" if len(filtrado) >= 13 else "vs. início do período"
mes_ref = atual["data_ref"].strftime("%m/%Y")

st.subheader(f"Indicadores em {mes_ref}")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Selic Meta vigente", f"{br(atual['selic_meta'])}% a.a.",
          f"{br(atual['selic_meta'] - base_comp['selic_meta'])} p.p. {rotulo}", delta_color="off")
k2.metric("IPCA 12M acumulado", f"{br(atual['ipca_12m'])}%",
          f"{br(atual['ipca_12m'] - base_comp['ipca_12m'])} p.p. {rotulo}", delta_color="inverse")
k3.metric("Juro real ex-post", f"{br(atual['juro_real_ex_post'])}% a.a.",
          f"{br(atual['juro_real_ex_post'] - base_comp['juro_real_ex_post'])} p.p. {rotulo}",
          delta_color="off")
k4.metric("Dólar PTAX (média do mês)", f"R$ {br(atual['dolar_ptax'], 4)}",
          f"R$ {br(atual['dolar_ptax'] - base_comp['dolar_ptax'], 4)} {rotulo}", delta_color="inverse")
st.caption(f"Dólar médio no período filtrado: R$ {br(filtrado['dolar_ptax'].mean(), 4)}")

# ===== Abas =====
aba1, aba2, aba3, aba4, aba5 = st.tabs(
    ["Política monetária", "Câmbio e inflação", "Atividade econômica", "Correlações", "Dados"])

# ===== Aba 1: Selic, IPCA 12M e juro real =====
with aba1:
    pico = filtrado.loc[filtrado["juro_real_ex_post"].idxmax()]
    st.markdown(f"**Insight:** o maior juro real do período foi **{br(pico['juro_real_ex_post'])}% a.a.** "
                f"em {pico['data_ref'].strftime('%m/%Y')}, com Selic em {br(pico['selic_meta'])}% "
                f"e IPCA 12M em {br(pico['ipca_12m'])}%.")
    fig1 = go.Figure()
    fig1.add_bar(x=filtrado["data_ref"], y=filtrado["juro_real_ex_post"], name="Juro real ex-post",
                 marker_color=COR_JURO, opacity=0.6)
    fig1.add_scatter(x=filtrado["data_ref"], y=filtrado["selic_meta"], name="Selic Meta",
                     mode="lines", line=dict(color=COR_SELIC, width=3))
    fig1.add_scatter(x=filtrado["data_ref"], y=filtrado["ipca_12m"], name="IPCA 12M",
                     mode="lines", line=dict(color=COR_IPCA, width=3))
    fig1.add_hline(y=0, line_color="black", line_width=1)
    st.plotly_chart(layout_padrao(fig1, "Política monetária: Selic, inflação e juro real", "% a.a."),
                    width="stretch")
    st.caption("**Ação:** juro real positivo e alto encarece o crédito; empresas endividadas "
               "a taxa pós-fixada devem avaliar trocar parte da dívida por taxa prefixada.")

# ===== Aba 2: dólar com média e dispersão dólar x IPCA =====
with aba2:
    media_dolar = dados["dolar_ptax"].mean()
    meses_acima = int(filtrado["dolar_acima_media"].sum())
    st.markdown(f"**Insight:** o dólar ficou acima da média do quinquênio (R$ {br(media_dolar, 2)}) "
                f"em **{meses_acima} de {len(filtrado)} meses** do período filtrado.")
    fig2 = px.line(filtrado, x="data_ref", y="dolar_ptax", labels={"dolar_ptax": "Reais por Dolar"},
                   color_discrete_sequence=[COR_DOLAR])
    fig2.add_hline(y=media_dolar, line_dash="dash", line_color="gray",
                   annotation_text=f"Média 2019-2023: R$ {br(media_dolar, 2)}")
    st.plotly_chart(layout_padrao(fig2, "Dólar PTAX (média mensal) e média do quinquênio", "Reais por Dolar"),
                    width="stretch")

    fig3 = px.scatter(filtrado_ciclo, x="dolar_ptax", y="ipca_12m", color=filtrado_ciclo["ano"].astype(str),
                      size="selic_meta", hover_data={"data_ref": "|%m/%Y"},
                      labels={"dolar_ptax": "Dólar PTAX (Reais por Dolar)", "ipca_12m": "IPCA 12M (%)",
                              "color": "Ano", "selic_meta": "Selic (% a.a.)"})
    fig3.update_layout(xaxis_title="Dólar PTAX (Reais por Dolar)")
    st.plotly_chart(layout_padrao(fig3, "Dólar vs. IPCA 12M (tamanho = Selic)", "IPCA 12M (%)"),
                    width="stretch")
    st.caption("Filtrado também pelo ciclo da Selic. A proximidade dos pontos indica associação, "
               "não prova que o câmbio causou a inflação.")

# ===== Aba 3: IBC-Br com ciclos de alta da Selic =====
with aba3:
    variacao_ibc = (filtrado["ibc_br"].iloc[-1] / filtrado["ibc_br"].iloc[0] - 1) * 100
    st.markdown(f"**Insight:** entre {filtrado['data_ref'].iloc[0].strftime('%m/%Y')} e {mes_ref} "
                f"o IBC-Br variou **{br(variacao_ibc, 1)}%**. As faixas vermelhas marcam meses de alta da Selic "
                "e as verdes, meses de corte.")
    fig4 = px.line(filtrado, x="data_ref", y="ibc_br", color_discrete_sequence=[COR_SELIC])
    for inicio, fim in blocos_ciclo(filtrado, "Alta"):
        fig4.add_vrect(x0=inicio, x1=fim, fillcolor=COR_IPCA, opacity=0.12, line_width=0)
    for inicio, fim in blocos_ciclo(filtrado, "Corte"):
        fig4.add_vrect(x0=inicio, x1=fim, fillcolor=COR_DOLAR, opacity=0.12, line_width=0)
    st.plotly_chart(layout_padrao(fig4, "Atividade econômica (IBC-Br dessazonalizado)", "Índice"),
                    width="stretch")
    st.caption("O IBC-Br é revisado pelo Banco Central; valores recentes podem mudar.")

# ===== Aba 4: heatmap de correlação de Pearson =====
with aba4:
    colunas = st.session_state["variaveis"]
    if len(colunas) < 2:
        st.info("Escolha ao menos 2 variáveis na barra lateral.")
    else:
        corr = calcular_correlacao(filtrado, colunas).rename(index=VARIAVEIS, columns=VARIAVEIS)
        empilhado = corr.stack()
        empilhado = empilhado[[a < b for a, b in empilhado.index]]
        par_top = empilhado.abs().idxmax()
        st.markdown(f"**Insight:** o par mais correlacionado é **{par_top[0]} × {par_top[1]}** "
                    f"(r = {br(empilhado[par_top])}).")
        fig5 = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                         aspect="auto")
        fig5.update_layout(title="Correlação de Pearson entre as variáveis", separators=",.")
        st.plotly_chart(fig5, width="stretch")
    st.warning("Correlação não implica causalidade. São no máximo 60 observações mensais, "
               "e o choque da pandemia pesa no resultado.")

# ===== Aba 5: tabela e exportação =====
with aba5:
    st.dataframe(filtrado_ciclo, width="stretch", hide_index=True)
    st.download_button("Baixar dados filtrados (CSV)",
                       filtrado_ciclo.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
                       file_name=f"macro_{ano_ini}_{ano_fim}.csv", mime="text/csv")
