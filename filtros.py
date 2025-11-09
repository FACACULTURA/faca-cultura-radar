import csv

def carregar_base(arquivo):
    editais = []
    with open(arquivo, newline='', encoding='utf-8') as csvfile:
        leitor = csv.DictReader(csvfile)
        for linha in leitor:
            editais.append(linha)
    return editais

def filtrar_por_tipo(editais, tipo_projeto):
    filtrados = []
    for e in editais:
        tipos = e['tipo'].split(';')
        if tipo_projeto in tipos:
            filtrados.append(e)
    return filtrados

def main():
    base = carregar_base('base_editais.csv')
    tipo_busca = input("Digite o tipo de projeto que deseja buscar (ex: Curtas, Longas, Série): ")
    resultados = filtrar_por_tipo(base, tipo_busca)
    
    print("\nEditais encontrados:\n")
    for r in resultados:
        print(f"- {r['nome']} ({r['instituicao']}) | Prazo: {r['prazo']} | Link: {r['link']} | Observações: {r['observacoes']}")

if __name__ == "__main__":
    main()


