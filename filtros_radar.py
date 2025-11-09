import csv
from datetime import datetime, timedelta

# Pesos para cada prioridade
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

# Quantos dias antes do prazo avisar
DIAS_AVISO = 30

def carregar_base(arquivo):
    editais = []
    with open(arquivo, newline='', encoding='utf-8') as csvfile:
        leitor = csv.DictReader(csvfile)
        for linha in leitor:
            editais.append(linha)
    return editais

def calcular_pontuacao(editais):
    for e in editais:
        score = 0
        prioridades = e['observacoes'].split(';')
        for p in prioridades:
            p = p.strip()
            score += PESOS_PRIORIDADE.get(p, 0)
        e['pontuacao'] = score
    return editais

def filtrar_editais(editais, tipo_projeto=None, instituicao=None):
    filtrados = []
    for e in editais:
        tipos = e['tipo'].split(';')
        if tipo_projeto and tipo_projeto not in tipos:
            continue
        if instituicao and instituicao.lower() not in e['instituicao'].lower():
            continue
        filtrados.append(e)
    return filtrados

def avisar_prazos(editais):
    hoje = datetime.today()
    avisos = []
    for e in editais:
        try:
            prazo = datetime.strptime(e['prazo'], '%Y-%m-%d')
            if 0 <= (prazo - hoje).days <= DIAS_AVISO:
                avisos.append((e['nome'], e['prazo'], (prazo - hoje).days))
        except:
            pass
    return avisos

def main():
    base = carregar_base('base_editais.csv')
    
    print("Filtros disponíveis. Pressione Enter para pular um filtro.")
    tipo_busca = input("Digite o tipo de projeto (ex: Curtas, Longas, Série): ").strip()
    instituicao_busca = input("Digite a instituição (ex: Funarte, Ancine): ").strip()
    
    tipo_busca = tipo_busca if tipo_busca else None
    instituicao_busca = instituicao_busca if instituicao_busca else None
    
    resultados = filtrar_editais(base, tipo_projeto=tipo_busca, instituicao=instituicao_busca)
    
    if resultados


