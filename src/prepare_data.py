"""
Prepara os dados da Olist para o dashboard.

Uso:
    python src/prepare_data.py

Espera os CSVs originais do Kaggle em data/raw/ e gera
data/processed/items.parquet (uma linha por item vendido).
"""
from pathlib import Path

import pandas as pd

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)


# Nomes de categoria em português, com acentos. Categorias que não estão
# no dicionário recebem um nome gerado automaticamente.
CATEGORIAS = {
    "agro_industria_e_comercio": "Agroindústria e comércio",
    "alimentos": "Alimentos",
    "alimentos_bebidas": "Alimentos e bebidas",
    "artes": "Artes",
    "artes_e_artesanato": "Artes e artesanato",
    "artigos_de_festas": "Artigos de festas",
    "artigos_de_natal": "Artigos de Natal",
    "audio": "Áudio",
    "automotivo": "Automotivo",
    "bebes": "Bebês",
    "bebidas": "Bebidas",
    "beleza_saude": "Beleza e saúde",
    "brinquedos": "Brinquedos",
    "cama_mesa_banho": "Cama, mesa e banho",
    "casa_conforto": "Casa e conforto",
    "casa_conforto_2": "Casa e conforto 2",
    "casa_construcao": "Casa e construção",
    "cds_dvds_musicais": "CDs e DVDs musicais",
    "cine_foto": "Cine e foto",
    "climatizacao": "Climatização",
    "consoles_games": "Consoles e games",
    "construcao_ferramentas_construcao": "Construção e ferramentas",
    "construcao_ferramentas_ferramentas": "Ferramentas",
    "construcao_ferramentas_iluminacao": "Iluminação",
    "construcao_ferramentas_jardim": "Jardim (construção)",
    "construcao_ferramentas_seguranca": "Segurança (construção)",
    "cool_stuff": "Cool stuff",
    "dvds_blu_ray": "DVDs e Blu-ray",
    "eletrodomesticos": "Eletrodomésticos",
    "eletrodomesticos_2": "Eletrodomésticos 2",
    "eletronicos": "Eletrônicos",
    "eletroportateis": "Eletroportáteis",
    "esporte_lazer": "Esporte e lazer",
    "fashion_bolsas_e_acessorios": "Moda: bolsas e acessórios",
    "fashion_calcados": "Moda: calçados",
    "fashion_esporte": "Moda: esporte",
    "fashion_roupa_feminina": "Moda: feminina",
    "fashion_roupa_infanto_juvenil": "Moda: infantojuvenil",
    "fashion_roupa_masculina": "Moda: masculina",
    "fashion_underwear_e_moda_praia": "Moda: íntima e praia",
    "ferramentas_jardim": "Ferramentas e jardim",
    "flores": "Flores",
    "fraldas_higiene": "Fraldas e higiene",
    "industria_comercio_e_negocios": "Indústria, comércio e negócios",
    "informatica_acessorios": "Informática e acessórios",
    "instrumentos_musicais": "Instrumentos musicais",
    "la_cuisine": "La cuisine",
    "livros_importados": "Livros importados",
    "livros_interesse_geral": "Livros: interesse geral",
    "livros_tecnicos": "Livros técnicos",
    "malas_acessorios": "Malas e acessórios",
    "market_place": "Marketplace",
    "moveis_colchao_e_estofado": "Móveis: colchão e estofado",
    "moveis_cozinha_area_de_servico_jantar_e_jardim": "Móveis: cozinha, jantar e jardim",
    "moveis_decoracao": "Móveis e decoração",
    "moveis_escritorio": "Móveis de escritório",
    "moveis_quarto": "Móveis de quarto",
    "moveis_sala": "Móveis de sala",
    "musica": "Música",
    "papelaria": "Papelaria",
    "pc_gamer": "PC gamer",
    "pcs": "PCs",
    "perfumaria": "Perfumaria",
    "pet_shop": "Pet shop",
    "portateis_casa_forno_e_cafe": "Portáteis: forno e café",
    "portateis_cozinha_e_preparadores_de_alimentos": "Portáteis: cozinha e preparo",
    "relogios_presentes": "Relógios e presentes",
    "seguros_e_servicos": "Seguros e serviços",
    "sinalizacao_e_seguranca": "Sinalização e segurança",
    "tablets_impressao_imagem": "Tablets, impressão e imagem",
    "telefonia": "Telefonia",
    "telefonia_fixa": "Telefonia fixa",
    "utilidades_domesticas": "Utilidades domésticas",
}


def nome_categoria(raw):
    if pd.isna(raw):
        return "Sem categoria"
    if raw in CATEGORIAS:
        return CATEGORIAS[raw]
    texto = raw.replace("_", " ")
    return texto[:1].upper() + texto[1:]


def main() -> None:
    # 1. Leitura
    orders = pd.read_csv(
        RAW / "olist_orders_dataset.csv",
        parse_dates=[
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )
    items = pd.read_csv(RAW / "olist_order_items_dataset.csv")
    customers = pd.read_csv(RAW / "olist_customers_dataset.csv")
    products = pd.read_csv(RAW / "olist_products_dataset.csv")
    reviews = pd.read_csv(
        RAW / "olist_order_reviews_dataset.csv",
        parse_dates=["review_answer_timestamp"],
    )

    # 2. Limpeza
    # Mantemos apenas pedidos entregues: são os que têm receita realizada
    # e datas de entrega para calcular prazo e atraso.
    orders = orders[orders["order_status"] == "delivered"].dropna(
        subset=["order_delivered_customer_date"]
    )

    # Alguns pedidos têm mais de uma avaliação; ficamos com a mais recente.
    reviews = (
        reviews.sort_values("review_answer_timestamp")
        .drop_duplicates("order_id", keep="last")[["order_id", "review_score"]]
    )

    # Categorias em português; nulos viram "Sem categoria".
    products["category"] = products["product_category_name"].apply(nome_categoria)

    # 3. Junções 
    df = (
        items.merge(orders, on="order_id", how="inner")
        .merge(customers[["customer_id", "customer_unique_id", "customer_state"]],
               on="customer_id", how="left")
        .merge(products[["product_id", "category"]], on="product_id", how="left")
        .merge(reviews, on="order_id", how="left")
    )

    # 4. Features 
    df["purchase_date"] = df["order_purchase_timestamp"].dt.normalize()
    df["year_month"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
    df["delivery_days"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.days
    df["delay_days"] = (
        df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]
    ).dt.days
    df["is_late"] = df["delay_days"] > 0
    df["revenue"] = df["price"]

    cols = [
        "order_id", "order_item_id", "customer_unique_id", "customer_state",
        "category", "price", "freight_value", "revenue",
        "purchase_date", "year_month",
        "delivery_days", "delay_days", "is_late", "review_score",
    ]
    df = df[cols]

    df.to_parquet(OUT / "items.parquet", index=False)
    print(f"OK: {len(df):,} itens | {df['order_id'].nunique():,} pedidos "
          f"| {df['purchase_date'].min().date()} a {df['purchase_date'].max().date()}")


if __name__ == "__main__":
    main()
