# 📦 Dashboard de Vendas e Satisfação — Olist E-Commerce

Dashboard interativo em Python que analisa vendas, entregas e comportamento de clientes de um marketplace brasileiro, construído com **pandas, Plotly e Streamlit**.

🔗 **Demo online:** _cole aqui o link do Streamlit Cloud_

![Dashboard](docs\clientes-por-segmento.png)
![Dashboard](docs\nota-média-por-situação-da-entrega.png)
![Dashboard](docs\receita-mensal.png)
![Dashboard](docs\top-10-categorias-por-receita.png)
![Dashboard](docs\top-10-estados-por-receita.png)
<!-- Salve um print do dashboard em docs/dashboard.png -->

## Problema de negócio

Uma operação de e-commerce precisa saber **onde está a receita, o que prejudica a experiência do cliente e quão bem consegue reter quem compra**. O dashboard responde a quatro perguntas:

1. Como evoluem receita, pedidos e ticket médio ao longo do tempo?
2. Quais categorias e estados concentram a receita?
3. O atraso na entrega afeta a avaliação do cliente?
4. Quantos clientes voltam a comprar?

## Principais insights

> Números calculados sobre o período completo da base (set/2016 a ago/2018), com 96.470 pedidos entregues e R$ 13,2 milhões em receita.

- **Atraso na entrega derruba a satisfação.** A nota média é 4,29 em entregas adiantadas e 4,03 no prazo, mas cai para 2,71 com atraso de até 7 dias e para **1,70 com atraso acima de 7 dias**. Isso é uma associação observada nos dados, não prova de causa.
- **A retenção é o maior gargalo.** Apenas **3,0% dos clientes compraram mais de uma vez**. Quem recompra gasta cerca de R$ 250 a R$ 270 no total, quase o dobro dos clientes de compra única (R$ 135 a R$ 140).
- **A receita é muito concentrada geograficamente.** São Paulo responde por cerca de R$ 5 milhões, bem acima de RJ e MG.
- **A receita cresceu ao longo de 2017**, com pico no fim do ano (possivelmente Black Friday), e se estabilizou entre R$ 0,8 e R$ 1 milhão por mês em 2018.
- **Entregas atrasadas são minoria (6,8%)**, mas têm impacto desproporcional na avaliação, o que as torna um bom alvo de melhoria.

## Funcionalidades

- Filtros por período, estado e categoria.
- KPIs: receita, pedidos, ticket médio, nota média e % de entregas atrasadas.
- **Visão geral:** receita mensal, top 10 categorias e top 10 estados.
- **Entrega × Satisfação:** nota média por situação da entrega e distribuição das notas, com insight calculado dinamicamente conforme os filtros.
- **Clientes:** segmentação por recência e frequência.

## Decisões técnicas

- **Apenas pedidos entregues:** são os que têm receita realizada e datas para calcular prazo e atraso.
- **Receita = soma do preço dos itens**, sem o frete.
- **Avaliações duplicadas:** quando um pedido tem mais de uma avaliação, mantive a mais recente.
- **Segmentação por regras, e não por quintis de RFM:** como a grande maioria dos clientes compra uma única vez, quintis de frequência não separam bem os grupos. Usei regras simples de recência e frequência (recorrente ativo/inativo, novo, compra única em risco/perdido).
- **Categorias em português**, com um dicionário de tradução com acentos e nomes mais legíveis.
- **Dados tratados em Parquet** e leitura com `@st.cache_data`, para o app abrir rápido.

## Limitações

- Em 2016 há pouquíssimos pedidos, e o último mês da base está incompleto. Por isso o período padrão do dashboard começa em jan/2017.
- A base é de 2016 a 2018, então os padrões podem não refletir o mercado atual.
- A relação entre atraso e nota é observacional; outros fatores (qualidade do produto, por exemplo) também influenciam a avaliação.

## Como rodar

1. Baixe o dataset [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) e coloque os CSVs em `data/raw/`.
2. Crie o ambiente e instale as dependências:
   ```bash
   conda create -n olist python=3.12 -y
   conda activate olist
   pip install -r requirements.txt
   ```
3. Gere os dados tratados:
   ```bash
   python src/prepare_data.py
   ```
4. Abra o dashboard:
   ```bash
   streamlit run app.py
   ```

## Estrutura do projeto

```
├── app.py                  # Dashboard Streamlit
├── src/prepare_data.py     # Limpeza e junção das tabelas
├── notebooks/              # Análise exploratória
├── data/
│   ├── raw/                # CSVs originais (não versionados)
│   └── processed/          # items.parquet
└── requirements.txt
```

## Tecnologias

Python · pandas · Plotly · Streamlit · Parquet

## Autor

_Daniel Fernando_ · [LinkedIn](https://www.linkedin.com/in/daniel-fernando-a88a81217/) · [GitHub](https://github.com/idanfer)

Dados: Olist, disponibilizados publicamente no Kaggle.

git init
git add .
git commit -m "Dashboard de vendas Olist"
git branch -M main
git remote add origin https://github.com/idanfer/Dashboard-Vendas-Olist.git
git push -u origin main