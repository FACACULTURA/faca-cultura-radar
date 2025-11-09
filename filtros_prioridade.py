import csv

# Definir pesos para cada prioridade
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

def main():
    base = carregar_base('base_editais.csv')
    
    print("Filtros disponíveis. Pressione Enter para pular um filtro.")
    tipo_busca = input("Digite o tipo de projeto (ex: Curtas, Longas, Série): ").strip()
    instituicao_busca = input("Digite a instituição (ex: Funarte, Ancine): ").strip()
    
    tipo_busca = tipo_busca if tipo_busca else None
    instituicao_busca = instituicao_busca if instituicao_busca else None
    
    resultados = filtrar_editais(base, tipo_projeto=tipo_busca, instituicao=instituicao_busca)
    
    if resultados:
        # Calcula pontuação e ordena por prioridade
        resultados = calcular_pontuacao(resultados)
        resultados.sort(key=lambda x: x['pontuacao'], reverse=True)
        
        print("\nEditais encontrados (ordenados por prioridade):\n")
        for r in resultados:
            print(f"- {r['nome']} ({r['instituicao']}) | Prazo: {r['prazo']} | Link: {r['link']} | Observações: {r['observacoes']} | Pontuação: {r['pontuacao']}")
    else:
        print("\nNenhum edital encontrado com os filtros aplicados.")

if __name__ == "__main__":
    main()


