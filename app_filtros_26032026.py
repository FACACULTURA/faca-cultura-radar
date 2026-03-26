import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="FAÇA CULTURA - Radar de Editais", layout="wide")

DIAS_ALERTA = 30
PESOS_PRIORIDADE = {
    'Fundos grandes': 3,
    'Coprodução': 2,
    'Laboratórios de pitching': 2,
    'Leis de incentivo': 1,
    'Exibição em plataforma pública': 1,
    'Privado': 1,
    'Pequenos projetos': 0.5,
    'Formação': 0.5,
}
COLUNAS_NECESSARIAS = ['nome', 'instituicao', 'tipo', 'prazo', 'link', 'observacoes']


@st.cache_data
def carregar_base(caminho_arquivo: str) -> pd.DataFrame:
    caminho = Path(caminho_arquivo)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

    ultimo_erro = None
    for encoding in ('utf-8', 'utf-8-sig', 'latin1'):
        try:
            df = pd.read_csv(caminho, encoding=encoding)
            break
        except Exception as e:
            ultimo_erro = e
    else:
        raise ultimo_erro

    df.columns = df.columns.str.strip().str.lower()

    faltando = [c for c in COLUNAS_NECESSARIAS if c not in df.columns]
    if faltando:
        raise ValueError(
            "Faltam colunas obrigatórias no CSV: " + ", ".join(faltando)
        )

    for col in COLUNAS_NECESSARIAS:
        df[col] = df[col].fillna('').astype(str).str.strip()

    return df


def extrair_opcoes(series: pd.Series) -> list[str]:
    valores = set()
    for item in series:
        for parte in str(item).split(';'):
            parte = parte.strip()
            if parte:
                valores.add(parte)
    return sorted(valores)


def calcular_pontuacao(observacoes: str) -> float:
    score = 0.0
    for p in str(observacoes).split(';'):
        score += PESOS_PRIORIDADE.get(p.strip(), 0)
    return score


def alerta_prazo(prazo: str) -> str:
    try:
        data = pd.to_datetime(prazo)
        dias = (data.normalize() - pd.Timestamp.today().normalize()).days
        return "⚠️ Prazo próximo" if 0 <= dias <= DIAS_ALERTA else ""
    except Exception:
        return ""


st.title("🎬 FAÇA CULTURA - Radar de Editais")
st.caption("Versão robusta para teste local e deploy no Streamlit Cloud")

arquivo_padrao = 'base_editais.csv'

try:
    df = carregar_base(arquivo_padrao)
except Exception as e:
    st.error(f"Erro ao carregar {arquivo_padrao}: {e}")
    st.info("Confirme se o arquivo está na mesma pasta do app e se contém as colunas: nome, instituicao, tipo, prazo, link e observacoes.")
    st.stop()

with st.expander("Diagnóstico da base", expanded=False):
    st.write("Colunas detectadas:", list(df.columns))
    st.write("Quantidade de linhas:", len(df))
    st.dataframe(df.head(5), use_container_width=True)

col1, col2 = st.columns([1, 1])
with col1:
    tipo_opcao = st.selectbox("Filtrar por tipo de projeto", ["Todos"] + extrair_opcoes(df['tipo']))
with col2:
    instituicao_opcao = st.text_input("Filtrar por instituição")


df_filtrado = df.copy()
if tipo_opcao != "Todos":
    df_filtrado = df_filtrado[df_filtrado['tipo'].str.contains(tipo_opcao, case=False, na=False)]
if instituicao_opcao:
    df_filtrado = df_filtrado[df_filtrado['instituicao'].str.contains(instituicao_opcao, case=False, na=False)]

df_filtrado['Pontuação'] = df_filtrado['observacoes'].apply(calcular_pontuacao)
df_filtrado['Alerta'] = df_filtrado['prazo'].apply(alerta_prazo)
df_filtrado = df_filtrado.sort_values(by=['Pontuação', 'prazo'], ascending=[False, True])

st.subheader("📋 Editais encontrados")
st.dataframe(df_filtrado, use_container_width=True)

csv_export = df_filtrado.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Baixar CSV filtrado",
    data=csv_export,
    file_name="relatorio_editais.csv",
    mime="text/csv",
)

st.subheader("📅 Calendário de inscrições")
df_cal = df_filtrado.copy()
df_cal['prazo_dt'] = pd.to_datetime(df_cal['prazo'], errors='coerce')
df_cal = df_cal.dropna(subset=['prazo_dt'])

if df_cal.empty:
    st.warning("Nenhuma data válida encontrada na coluna 'prazo'.")
else:
    df_cal['Faixa'] = df_cal['Pontuação'].apply(
        lambda x: 'Alta' if x >= 4 else ('Média' if x >= 2 else 'Baixa')
    )
    fig = px.scatter(
        df_cal,
        x='prazo_dt',
        y='Pontuação',
        text='nome',
        color='Faixa',
        hover_data=['instituicao', 'tipo', 'Alerta'],
        height=520,
    )
    fig.update_traces(textposition='top center')
    fig.update_layout(
        xaxis_title='Prazo de inscrição',
        yaxis_title='Pontuação',
    )
    st.plotly_chart(fig, use_container_width=True)

st.success("App carregado com sucesso.")
