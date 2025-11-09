import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Pesos para ranking
PESOS_PRIORIDADE = {
    'Fundos grandes': 3,
    'Coprodução': 2,
    'Laboratórios de pitching': 2,
    'Leis de incentivo': 1,
    'Exibição em plataforma pública': 1,
    'Privado': 1,
    'Pequenos projetos': 0.5,
    'Formação': 0.5
}

DIAS_AVISO = 30

# Carregar base
df = pd.read_csv('base_editais.csv')

# Streamlit - interface
st.title("FAÇA CULTURA - Radar de Editais")

# Filtros
tipo_opcao = st.selectbox("Tipo de projeto", ["Todos"] + list(set(";".join(df['tipo']).split(";"))))
instituicao_opcao = st.text_input("Instituição (ex: Funarte, Ancine)")

# Filtrar dados
def filtrar(df, tipo=None, instituicao=None):
    df_filtrado = df.copy()
    if tipo and tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado['tipo'].str.contains(tipo)]
    if instituicao:
        df_filtrado = df_filtrado[df_filtrado['instituicao'].str.contains(instituicao, case=False)]
    return df_filtrado

df_filtrado = filtrar(df, tipo_opcao, instituicao_opcao)

# Calcular pontuação
def calcular_pontuacao(row):
    score = 0
    for p in row['observacoes'].split(";"):
        score += PESOS_PRIORIDADE.get(p.strip(), 0)
    return score

df_filtrado['Pontuação'] = df_filtrado.apply(calcular_pontuacao, axis=1)
df_filtrado = df_filtrado.sort_values(by='Pontuação', ascending=False)

# Aviso de prazos próximos
def aviso_prazos(row):
    try:
        prazo = datetime.strptime(row['prazo'], '%Y-%m-%d')
        if 0 <= (prazo - datetime.today()).days <= DIAS_AVISO:
            return True
        else:
            return False
    except:
        return False

df_filtrado['Prazo próximo'] = df_filtrado.apply(aviso_prazos, axis=1)

# Mostrar tabela
st.dataframe(df_filtrado)

# Destaque de prazos próximos
st.subheader("⚠️ Prazos próximos")
st.dataframe(df_filtrado[df_filtrado['Prazo próximo']])


