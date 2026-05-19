import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

LISTA_URL = "https://www.gov.br/cultura/pt-br/assuntos/editais/inscricoes-em-andamento"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def limpar_texto(txt):
    return re.sub(r"\s+", " ", txt).strip()

def extrair_links_editais():
    resp = requests.get(LISTA_URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    resultados = []

    # pega todos os links da página
    for a in soup.find_all("a", href=True):
        titulo = limpar_texto(a.get_text(" ", strip=True))
        href = a["href"].strip()

        # filtra editais mais próximos do tema audiovisual/cinema
        if titulo and ("audiovisual" in titulo.lower() or "cinema" in titulo.lower()):
            link = urljoin(LISTA_URL, href)
            resultados.append({
                "titulo_lista": titulo,
                "link": link
            })

    # remove duplicados pelo link
    unicos = []
    vistos = set()
    for item in resultados:
        if item["link"] not in vistos:
            vistos.add(item["link"])
            unicos.append(item)

    return unicos

def extrair_detalhes_edital(url):
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    titulo = None
    h1 = soup.find("h1")
    if h1:
        titulo = limpar_texto(h1.get_text())

    texto_total = limpar_texto(soup.get_text(" ", strip=True))

    # tenta achar frase de encerramento das inscrições
    padrao_data = re.search(
        r"encerra-se em\s+(.+?)(?:\.|, às| às)",
        texto_total,
        flags=re.IGNORECASE
    )

    data_fechamento = padrao_data.group(1).strip() if padrao_data else None

    return {
        "titulo": titulo,
        "data_fechamento": data_fechamento,
        "link": url
    }

def main():
    print("Buscando editais na lista...\n")
    editais = extrair_links_editais()

    # mostra alguns encontrados
    for i, edital in enumerate(editais[:5], start=1):
        print(f"{i}. {edital['titulo_lista']}")
        print(f"   {edital['link']}")

    print("\nExtraindo detalhes dos 2 primeiros...\n")
    for edital in editais[:2]:
        detalhes = extrair_detalhes_edital(edital["link"])
        print("Título:", detalhes["titulo"])
        print("Data de fechamento:", detalhes["data_fechamento"])
        print("Link:", detalhes["link"])
        print("-" * 80)

if __name__ == "__main__":
    main()
