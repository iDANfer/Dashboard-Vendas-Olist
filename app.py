import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Olist | Dashboard de Vendas", page_icon="📦", layout="wide")


#  dados
@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_parquet("data/processed/items.parquet")


def brl(v: float, casas: int = 0) -> str:
    """Formata em reais no padrão brasileiro: R$ 1.234,56"""
    txt = f"{v:,.{casas}f}"
    return "R$ " + txt.replace(",", "X").replace(".", ",").replace("X", ".")


def milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


df_all = load_data()

# filtros
st.sidebar.header("Filtros")
dmin, dmax = df_all["purchase_date"].min().date(), df_all["purchase_date"].max().date()
# 2016 tem pouquíssimos pedidos; por padrão começamos em jan/2017.
inicio_padrao = max(dmin, pd.Timestamp("2017-01-01").date())
periodo = st.sidebar.date_input("Período", (inicio_padrao, dmax), min_value=dmin, max_value=dmax)
estados = st.sidebar.multiselect("Estado", sorted(df_all["customer_state"].dropna().unique()))
categorias = st.sidebar.multiselect("Categoria", sorted(df_all["category"].dropna().unique()))

if not (isinstance(periodo, (tuple, list)) and len(periodo) == 2):
    st.info("Selecione a data final do período para atualizar o dashboard.")
    st.stop()

df = df_all[(df_all["purchase_date"] >= pd.Timestamp(periodo[0]))
            & (df_all["purchase_date"] <= pd.Timestamp(periodo[1]))]
if estados:
    df = df[df["customer_state"].isin(estados)]
if categorias:
    df = df[df["category"].isin(categorias)]

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()

# nível pedido (um registro por pedido) para métricas de entrega e avaliação
orders = df.drop_duplicates("order_id")

# KPIs
st.title("📦 Dashboard de Vendas — Olist")
st.caption("Pedidos entregues de um marketplace brasileiro (2016–2018). "
           "Por padrão o período começa em jan/2017, pois 2016 tem poucos pedidos.")

n_pedidos = orders["order_id"].nunique()
receita = df["revenue"].sum()
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Receita", brl(receita))
c2.metric("Pedidos", milhar(n_pedidos))
c3.metric("Ticket médio", brl(receita / n_pedidos, 2))
c4.metric("Nota média", f"{orders['review_score'].mean():.2f}".replace(".", ",") + " ⭐")
c5.metric("Entregas atrasadas", f"{orders['is_late'].mean():.1%}".replace(".", ","))

tab1, tab2, tab3 = st.tabs(["📈 Visão geral", "🚚 Entrega × Satisfação", "👥 Clientes (RFM)"])

# visão geral
with tab1:
    mensal = df.groupby("year_month").agg(
        receita=("revenue", "sum"), pedidos=("order_id", "nunique")
    ).reset_index()
    mensal["mes"] = pd.to_datetime(mensal["year_month"])
    fig = px.line(mensal, x="mes", y="receita", markers=True,
                  title="Receita mensal", labels={"mes": "Mês", "receita": "Receita (R$)"})
    fig.update_xaxes(tickformat="%m/%Y")
    st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)
    top_cat = (df.groupby("category")["revenue"].sum()
               .nlargest(10).sort_values().reset_index())
    col_a.plotly_chart(
        px.bar(top_cat, x="revenue", y="category", orientation="h",
               title="Top 10 categorias por receita",
               labels={"revenue": "Receita (R$)", "category": ""}),
        use_container_width=True)

    por_estado = (df.groupby("customer_state")["revenue"].sum()
                  .sort_values(ascending=False).reset_index())
    col_b.plotly_chart(
        px.bar(por_estado.head(10), x="customer_state", y="revenue",
               title="Top 10 estados por receita",
               labels={"customer_state": "Estado", "revenue": "Receita (R$)"}),
        use_container_width=True)

# entrega x satisfação
with tab2:
    o = orders.dropna(subset=["review_score"]).copy()
    o["faixa"] = pd.cut(
        o["delay_days"],
        bins=[-999, -1, 0, 7, 999],
        labels=["Adiantada", "No prazo", "Atraso até 7 dias", "Atraso > 7 dias"],
    )
    nota_faixa = o.groupby("faixa", observed=True)["review_score"].agg(["mean", "count"]).reset_index()
    col_a, col_b = st.columns(2)
    col_a.plotly_chart(
        px.bar(nota_faixa, x="faixa", y="mean", text=nota_faixa["mean"].round(2),
               title="Nota média por situação da entrega",
               labels={"faixa": "", "mean": "Nota média"}, range_y=[0, 5]),
        use_container_width=True)

    dist = o["review_score"].value_counts(normalize=True).sort_index().reset_index()
    dist.columns = ["nota", "proporcao"]
    col_b.plotly_chart(
        px.bar(dist, x="nota", y="proporcao", title="Distribuição das notas",
               labels={"nota": "Nota", "proporcao": "% dos pedidos"}),
        use_container_width=True)

    no_prazo = o.loc[o["delay_days"] <= 0, "review_score"]
    muito_atrasado = o.loc[o["delay_days"] > 7, "review_score"]
    if len(no_prazo) and len(muito_atrasado):
        a = f"{no_prazo.mean():.2f}".replace(".", ",")
        b = f"{muito_atrasado.mean():.2f}".replace(".", ",")
        st.info(
            f"💡 **Insight:** pedidos entregues no prazo ou antes têm nota média de {a}, "
            f"enquanto pedidos com mais de 7 dias de atraso têm {b}. "
            f"O atraso está fortemente associado a avaliações ruins "
            f"(associação, não prova de causa)."
        )

# RFM
with tab3:
    ref = df["purchase_date"].max() + pd.Timedelta(days=1)
    rfm = df.groupby("customer_unique_id").agg(
        recencia=("purchase_date", lambda s: (ref - s.max()).days),
        frequencia=("order_id", "nunique"),
        valor=("revenue", "sum"),
    ).reset_index()

    def segmento(r):
        if r.frequencia > 1:
            return "Recorrente ativo" if r.recencia <= 180 else "Recorrente inativo"
        if r.recencia <= 90:
            return "Novo (até 90d)"
        return "Compra única em risco" if r.recencia <= 270 else "Compra única perdido"

    CORES_SEG = {
        "Recorrente ativo": "#2ca02c",
        "Recorrente inativo": "#ff7f0e",
        "Novo (até 90d)": "#1f77b4",
        "Compra única em risco": "#f2c200",
        "Compra única perdido": "#d62728",
    }
    rfm["segmento"] = rfm.apply(segmento, axis=1)
    seg = rfm.groupby("segmento").agg(
        clientes=("customer_unique_id", "count"), valor_medio=("valor", "mean")
    ).reset_index()

    col_a, col_b = st.columns(2)
    col_a.plotly_chart(px.pie(seg, names="segmento", values="clientes",
                              title="Clientes por segmento", hole=0.4,
                              color="segmento", color_discrete_map=CORES_SEG),
                       use_container_width=True)
    col_b.plotly_chart(px.bar(seg, x="segmento", y="valor_medio", color="segmento",
                              color_discrete_map=CORES_SEG,
                              title="Valor médio gasto por segmento",
                              labels={"segmento": "", "valor_medio": "R$ por cliente"}).update_layout(showlegend=False),
                       use_container_width=True)

    recorrentes = (rfm["frequencia"] > 1).mean()
    st.metric("Clientes que compraram mais de uma vez", f"{recorrentes:.1%}".replace(".", ","))
    st.caption("Segmentação baseada em regras simples de recência e frequência, "
               "adequada porque a maioria dos clientes da Olist compra apenas uma vez.")
