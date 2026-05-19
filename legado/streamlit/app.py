import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# --- Configurações ---
DIAS_ALERTA = 30
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

# --- Carregar base de editais ---
df = pd.read_csv('base_editais.csv')

# --- Interface Streamlit ---
st.set_page_config(page_title="FAÇA CULTURA - Radar de Editais", layout="wide")
st.title("🎬 FAÇA CULTURA - Radar de Editais")

# --- Filtros ---
tipo_opcao = st.selectbox("Filtrar por tipo de projeto", ["Todos"] + sorted(list(set(";".join(df['tipo']).split(";")))))
instituicao_opcao = st.text_input("Filtrar por instituição")

def filtrar(df, tipo=None, instituicao=None):
    df_filtrado = df.copy()
    if tipo and tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado['tipo'].str.contains(tipo)]
    if instituicao:
        df_filtrado = df_filtrado[df_filtrado['instituicao'].str.contains(instituicao, case=False)]
    return df_filtrado

df_filtrado = filtrar(df, tipo_opcao, instituicao_opcao)

# --- Ranking / Pontuação ---
def calcular_pontuacao(row):
    score = 0
    for p in row['observacoes'].split(";"):
        score += PESOS_PRIORIDADE.get(p.strip(), 0)
    return score

df_filtrado['Pontuação'] = df_filtrado.apply(calcular_pontuacao, axis=1)
df_filtrado = df_filtrado.sort_values(by='Pontuação', ascending=False)

# --- Alertas de prazo ---
def alerta_prazo(row):
    try:
        prazo = datetime.strptime(row['prazo'], '%Y-%m-%d')
        if 0 <= (prazo - datetime.today()).days <= DIAS_ALERTA:
            return "⚠️ Prazo próximo"
        else:
            return ""
    except:
        return ""

df_filtrado['Alerta'] = df_filtrado.apply(alerta_prazo, axis=1)

# --- Exibição da tabela ---
st.subheader("📋 Editais encontrados")
st.dataframe(df_filtrado.style.applymap(lambda x: 'background-color: #FFCCCC' if x == "⚠️ Prazo próximo" else '', subset=['Alerta']))

# --- Exportação de relatório ---
st.subheader("💾 Exportar relatório")
if st.button("Exportar CSV"):
    df_filtrado.to_csv('relatorio_editais.csv', index=False)
    st.success("Relatório exportado como relatorio_editais.csv!")

# --- Calendário interativo ---
st.subheader("📅 Calendário de Inscrições")

df_cal = df_filtrado.copy()
df_cal['prazo_dt'] = pd.to_datetime(df_cal['prazo'], errors='coerce')
df_cal = df_cal.dropna(subset=['prazo_dt'])

def cor_prioridade(row):
    if row['Pontuação'] >= 4:
        return 'red'
    elif row['Pontuação'] >= 2:
        return 'orange'
    else:
        return 'green'

df_cal['cor'] = df_cal.apply(cor_prioridade, axis=1)

fig = px.scatter(df_cal, x='prazo_dt', y='Pontuação', text='nome',
                 color='cor', color_discrete_map={'red':'#FF0000','orange':'#FFA500','green':'#00AA00'},
                 size_max=15, hover_data=['instituicao', 'tipo', 'Alerta'])
fig.update_layout(yaxis_title='Pontuação', xaxis_title='Prazo de inscrição',
                  showlegend=False, height=500)

st.plotly_chart(fig, use_container_width=True)

st.markdown("🚀 **Versão quase comercial pronta para hospedagem!**")
