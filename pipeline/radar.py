import streamlit as st
import pandas as pd

st.set_page_config(page_title="Radar - Faça Cultura", layout="wide")

st.title("🎬 Radar de Oportunidades")

# =========================
# CARREGAR DADOS
# =========================

try:
    df = pd.read_csv("output/oportunidades.csv")
except:
    st.error("Arquivo oportunidades.csv não encontrado.")
    st.stop()

if df.empty:
    st.warning("Nenhuma oportunidade encontrada.")
    st.stop()

# =========================
# FILTROS
# =========================

col1, col2, col3 = st.columns(3)

with col1:
    pais = st.selectbox("País", ["Todos"] + sorted(df["pais"].dropna().unique().tolist()))

with col2:
    tipo = st.selectbox("Tipo", ["Todos"] + sorted(df["tipo"].dropna().unique().tolist()))

with col3:
    produto = st.selectbox("Produto", ["Todos"] + sorted(df["produto"].dropna().unique().tolist()))

# aplicar filtros
df_filtrado = df.copy()

if pais != "Todos":
    df_filtrado = df_filtrado[df_filtrado["pais"] == pais]

if tipo != "Todos":
    df_filtrado = df_filtrado[df_filtrado["tipo"] == tipo]

if produto != "Todos":
    df_filtrado = df_filtrado[df_filtrado["produto"] == produto]

# ordenar por score
df_filtrado = df_filtrado.sort_values(by="score", ascending=False)

# =========================
# LISTAGEM
# =========================

st.markdown(f"### {len(df_filtrado)} oportunidades encontradas")

for _, row in df_filtrado.iterrows():
    st.markdown("---")

    col1, col2 = st.columns([4, 1])

    with col1:
        st.markdown(f"### {row['titulo']}")
        st.markdown(f"**Fonte:** {row['fonte']}")
        st.markdown(f"**Tipo:** {row['tipo']} | **Produto:** {row['produto']}")
        st.markdown(f"**País:** {row['pais']}")
        st.markdown(f"Score: {row['score']}")

    with col2:
        st.link_button("Abrir", row["link"])