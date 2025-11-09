import csv

def carregar_base(arquivo):
    editais = []
    with open(arquivo, newline='', encoding='utf-8') as csvfile:
        leitor = csv.DictReader(csvfile)
        for linha in leitor:
            editais.append(linha)
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
    
    # Se o usuário não digitar nada, considera None
    tipo_busca = tipo_busca if tipo_busca else None
    instituicao_busca = instituicao_busca if instituicao_busca else None
    
    resultados = filtrar_editais(base, tipo_projeto=tipo_busca, instituicao=instituicao_busca)
    
    if resultados:
        print("\nEditais encontrados:\n")
        for r in resultados:
            print(f"- {r['nome']} ({r['instituicao']}) | Prazo: {r['prazo']} | Link: {r['link']} | Observações: {r['observacoes']}")
    else:
        print("\nNenhum edital encontrado com os filtros aplicados.")

if __name__ == "__main__":
    main()


