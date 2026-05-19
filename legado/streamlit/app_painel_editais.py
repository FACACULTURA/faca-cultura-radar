import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Radar Audiovisual", layout="wide")

CSV_PATH = Path("output/editais.csv")


@st.cache_data
def carregar_dados(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        return pd.DataFrame()

    df = pd.read_csv(caminho)

    for coluna in ["ano", "score"]:
        if coluna in df.columns:
            df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    for coluna in ["fonte", "titulo", "tipo", "categoria", "pais", "status", "link"]:
        if coluna in df.columns:
            df[coluna] = df[coluna].fillna("")

    return df


st.title("Radar Inteligente de Oportunidades Audiovisuais")
st.caption("Painel inicial para explorar editais, festivais, labs, bolsas e histórico.")

df = carregar_dados(CSV_PATH)

if df.empty:
    st.warning("Nenhum dado encontrado em output/editais.csv. Rode primeiro: python3 run.py")
    st.stop()

with st.sidebar:
    st.header("Filtros")

    tipos = sorted([x for x in df.get("tipo", pd.Series(dtype=str)).dropna().unique() if str(x).strip()])
    categorias = sorted([x for x in df.get("categoria", pd.Series(dtype=str)).dropna().unique() if str(x).strip()])
    paises = sorted([x for x in df.get("pais", pd.Series(dtype=str)).dropna().unique() if str(x).strip()])
    fontes = sorted([x for x in df.get("fonte", pd.Series(dtype=str)).dropna().unique() if str(x).strip()])

    filtro_texto = st.text_input("Buscar por título")
    filtro_tipos = st.multiselect("Tipo", tipos)
    filtro_categorias = st.multiselect("Categoria", categorias)
    filtro_paises = st.multiselect("País", paises)
    filtro_fontes = st.multiselect("Fonte", fontes)

    anos_validos = df["ano"].dropna() if "ano" in df.columns else pd.Series(dtype=float)
    if not anos_validos.empty:
        ano_min = int(anos_validos.min())
        ano_max = int(anos_validos.max())
        faixa_anos = st.slider("Faixa de anos", min_value=ano_min, max_value=ano_max, value=(ano_min, ano_max))
    else:
        faixa_anos = None

    score_validos = df["score"].dropna() if "score" in df.columns else pd.Series(dtype=float)
    score_minimo = int(score_validos.min()) if not score_validos.empty else 0
    score_maximo = int(score_validos.max()) if not score_validos.empty else 20
    filtro_score = st.slider("Score mínimo", min_value=score_minimo, max_value=score_maximo, value=score_minimo)


filtrado = df.copy()

if filtro_texto and "titulo" in filtrado.columns:
    filtrado = filtrado[filtrado["titulo"].str.contains(filtro_texto, case=False, na=False)]

if filtro_tipos and "tipo" in filtrado.columns:
    filtrado = filtrado[filtrado["tipo"].isin(filtro_tipos)]

if filtro_categorias and "categoria" in filtrado.columns:
    filtrado = filtrado[filtrado["categoria"].isin(filtro_categorias)]

if filtro_paises and "pais" in filtrado.columns:
    filtrado = filtrado[filtrado["pais"].isin(filtro_paises)]

if filtro_fontes and "fonte" in filtrado.columns:
    filtrado = filtrado[filtrado["fonte"].isin(filtro_fontes)]

if faixa_anos and "ano" in filtrado.columns:
    filtrado = filtrado[(filtrado["ano"].fillna(0) >= faixa_anos[0]) & (filtrado["ano"].fillna(0) <= faixa_anos[1])]

if "score" in filtrado.columns:
    filtrado = filtrado[filtrado["score"].fillna(0) >= filtro_score]

if "score" in filtrado.columns and "ano" in filtrado.columns:
    filtrado = filtrado.sort_values(by=["score", "ano"], ascending=[False, False])
elif "score" in filtrado.columns:
    filtrado = filtrado.sort_values(by="score", ascending=False)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de oportunidades", len(filtrado))
col2.metric("Fontes", filtrado["fonte"].nunique() if "fonte" in filtrado.columns else 0)
col3.metric("Tipos", filtrado["tipo"].nunique() if "tipo" in filtrado.columns else 0)
col4.metric("Países", filtrado["pais"].nunique() if "pais" in filtrado.columns else 0)

st.subheader("Distribuição por tipo")
if "tipo" in filtrado.columns and not filtrado.empty:
    contagem_tipo = filtrado["tipo"].value_counts().reset_index()
    contagem_tipo.columns = ["tipo", "quantidade"]
    st.bar_chart(contagem_tipo.set_index("tipo"))
else:
    st.info("Sem dados suficientes para o gráfico de tipos.")

st.subheader("Histórico por ano")
if "ano" in filtrado.columns and filtrado["ano"].dropna().shape[0] > 0:
    contagem_ano = filtrado.dropna(subset=["ano"]).copy()
    contagem_ano["ano"] = contagem_ano["ano"].astype(int)
    contagem_ano = contagem_ano["ano"].value_counts().sort_index()
    st.line_chart(contagem_ano)
else:
    st.info("Sem dados suficientes para o gráfico histórico.")

st.subheader("Oportunidades")

if filtrado.empty:
    st.warning("Nenhum resultado encontrado com os filtros atuais.")
else:
    for _, row in filtrado.head(100).iterrows():
        titulo = row.get("titulo", "Sem título")
        link = row.get("link", "")
        fonte = row.get("fonte", "")
        tipo = row.get("tipo", "")
        categoria = row.get("categoria", "")
        ano = row.get("ano", "")
        pais = row.get("pais", "")
        score = row.get("score", "")
        status = row.get("status", "")

        with st.container():
            if link:
                st.markdown(f"### [{titulo}]({link})")
            else:
                st.markdown(f"### {titulo}")

            st.markdown(
                f"**Fonte:** {fonte}  \\n**Tipo:** {tipo}  \\n**Categoria:** {categoria}  \\n**Ano:** {ano}  \\n**País:** {pais}  \\n**Status:** {status}  \\n**Score:** {score}"
            )
            st.divider()

st.subheader("Tabela analítica")
colunas_preferidas = [
    c for c in ["fonte", "titulo", "tipo", "categoria", "ano", "pais", "status", "score", "link"]
    if c in filtrado.columns
]
st.dataframe(filtrado[colunas_preferidas], use_container_width=True)
