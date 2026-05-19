import requests
from bs4 import BeautifulSoup

ARQUIVO_FONTES = "fontes.txt"

PALAVRAS_CHAVE = [
    "edital",
    "chamada",
    "concurso",
    "seleção",
    "festival",
    "mostra",
    "laboratório",
    "laboratorio",
    "formação",
    "formacao",
    "audiovisual",
    "cinema",
    "filme",
    "documentário",
    "documentario",
    "curta",
    "longa",
    "série",
    "serie",
]

def carregar_fontes(nome_arquivo):
    with open(nome_arquivo, "r", encoding="utf-8") as arquivo:
        linhas = arquivo.readlines()

    fontes = []
    for linha in linhas:
        url = linha.strip()
        if url:
            fontes.append(url)

    return fontes


def baixar_pagina(url):
    try:
        resposta = requests.get(url, timeout=20)
        resposta.raise_for_status()
        return resposta.text
    except Exception as erro:
        print(f"Erro ao acessar {url}: {erro}")
        return None


def extrair_links_relevantes(html):
    soup = BeautifulSoup(html, "html.parser")
    links = soup.find_all("a")

    resultados = []
    vistos = set()

    for link in links:
        texto = link.get_text(strip=True)
        href = link.get("href")

        if not texto:
            continue

        texto_minusculo = texto.lower()

        relevante = any(palavra in texto_minusculo for palavra in PALAVRAS_CHAVE)

        if relevante and texto not in vistos:
            vistos.add(texto)
            resultados.append((texto, href))

    return resultados


def main():
    print("\n=== ASSISTENTE DE EDITAIS ===\n")

    fontes = carregar_fontes(ARQUIVO_FONTES)

    print(f"Total de fontes carregadas: {len(fontes)}\n")

    for url in fontes:
        print("=" * 60)
        print(f"FONTE: {url}\n")

        html = baixar_pagina(url)

        if html is None:
            print("Não foi possível ler esta fonte.\n")
            continue

        resultados = extrair_links_relevantes(html)

        if not resultados:
            print("Nenhum resultado relevante encontrado.\n")
            continue

        print("Resultados encontrados:\n")
        for titulo, link in resultados:
            print(f"- {titulo}")
            if link:
                print(f"  Link: {link}")
        print()

if __name__ == "__main__":
    main()