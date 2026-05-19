import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent.parent

ARQUIVO = (
    BASE_DIR
    / "data"
    / "input"
    / "fontes_diarios_oficiais.json"
)


def carregar_fontes():
    with open(ARQUIVO, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_fontes(fontes):
    with open(ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(fontes, f, ensure_ascii=False, indent=2)


def buscar_url_oficial(nome, estado=None, cidade=None):

    termos = []

    if nome:
        termos.append(str(nome))

    if cidade:
        termos.append(str(cidade))

    if estado:
        termos.append(str(estado))

    termos.append("diário oficial")

    query = " ".join(termos)

    url = f"https://duckduckgo.com/html/?q={query}"

    try:

        r = requests.get(
            url,
            timeout=20,
            headers={"User-Agent": "Mozilla/5.0"},
        )

        soup = BeautifulSoup(r.text, "html.parser")

        links = soup.select("a.result__a")

        for a in links:

            href = a.get("href")

            if not href:
                continue

            if any(x in href for x in [
                ".gov.br",
                "diariooficial",
                "imprensaoficial",
                "dom",
                "doe",
                "dio",
            ]):
                return href

    except Exception as e:
        print(f"Erro buscando {nome}: {e}")

    return None


def executar_descoberta():

    fontes = carregar_fontes()

    atualizadas = 0

    for fonte in fontes:

        if fonte.get("url"):
            continue

        print(
            f"🔎 Descobrindo URL:"
            f" {fonte.get('cidade') or fonte.get('nome')}"
        )

        nome_busca = fonte.get("nome") or f"Diário Oficial do Município de {fonte.get('cidade')}"

    url = buscar_url_oficial(
        nome=nome_busca,
        estado=fonte.get("estado"),
        cidade=fonte.get("cidade"),
    )
    if url:

                fonte["url"] = url
                fonte["status"] = "url_confirmada"

                atualizadas += 1

                print(f"✅ {url}")

    else:
                print("⚠️ não encontrada")

    salvar_fontes(fontes)

    print()
    print(f"URLs atualizadas: {atualizadas}")


    if __name__ == "__main__":
        executar_descoberta()