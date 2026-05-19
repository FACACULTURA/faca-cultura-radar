"""
F.CULT — curadores_editais.py

Objetivo:
Usar sites de curadoria, revistas e portais especializados como fontes intermediárias.

Regra:
Curador NÃO entra direto no feed.
Curador gera pistas para o core investigar.
"""

import re
import json
from pathlib import Path
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

CURADORES_BASE = [
    # Brasil — curadoria / agregadores
    "https://procult.ufc.br/pt/oportunidades-da-cultura/",
    "https://procultufc.substack.com/",
    "https://www.brblaw.com.br/?s=editais+culturais",
    "https://blog.benfeitoria.com/tag/edital/",
    "https://prosas.com.br/inicio?locale=pt",


    # Brasil — oficiais que também funcionam como hubs
    "https://www.gov.br/cultura/pt-br/assuntos/editais/inscricoes-abertas",
    "https://www.gov.br/cultura/pt-br/assuntos/editais/inscricoes-em-andamento",

    # Internacional — depois refinamos
    "https://www.filmindependent.org/programs/",
    "https://www.filmfreeway.com/",
]

TERMOS_INTERESSE = [
    "edital",
    "chamada",
    "chamamento",
    "inscrição",
    "inscrições",
    "fomento",
    "audiovisual",
    "cinema",
    "curta",
    "longa",
    "documentário",
    "série",
    "roteiro",
    "produção",
    "cultura",
    "lei paulo gustavo",
    "pnab",
    "rouanet",
    "ancine",
    "minc",
    "secult",
]


TERMOS_FONTE_OFICIAL = [
    ".gov.br",
    "cultura.",
    "secult",
    "prefeitura",
    "fundacao",
    "fundação",
    "ancine",
    "minc",
    "funarte",
    "brde",
    "spcine",
]



def limpar_texto(texto):
    return re.sub(r"\s+", " ", texto or "").strip()


def dominio(url):
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def texto_relevante(texto):
    base = texto.lower()
    return any(t in base for t in TERMOS_INTERESSE)


def parece_fonte_oficial(url, texto=""):
    base = f"{url} {texto}".lower()
    return any(t in base for t in TERMOS_FONTE_OFICIAL)


def extrair_links_da_pagina(url):
    pistas = []

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as erro:
        print(f"⚠️ Erro ao acessar curador {url}: {erro}")
        return pistas

    soup = BeautifulSoup(r.text, "html.parser")

    for a in soup.find_all("a", href=True):
        titulo = limpar_texto(a.get_text(" ", strip=True))
        href = urljoin(url, a.get("href"))

        if not titulo or len(titulo) < 8:
            continue

        contexto = titulo

        pai = a.parent
        if pai:
            contexto = limpar_texto(pai.get_text(" ", strip=True))

        texto_base = f"{titulo} {contexto} {href}"

        if not texto_relevante(texto_base):
            continue

        pista = {
            "titulo": titulo[:220],
            "resumo": contexto[:500],
            "url": href,
            "dominio": dominio(href),
            "fonte_intermediaria": url,
            "tipo_origem": "curador_intermediario",
            "parece_oficial": parece_fonte_oficial(href, texto_base),
            "score": calcular_score_pista(href, texto_base),
        }

        pistas.append(pista)

    return deduplicar(pistas)


def calcular_score_pista(url, texto):
    score = 0
    base = f"{url} {texto}".lower()

    if texto_relevante(base):
        score += 20

    if "edital" in base:
        score += 20

    if "inscri" in base:
        score += 15

    if "audiovisual" in base or "cinema" in base:
        score += 20

    if parece_fonte_oficial(url, texto):
        score += 30

    if "blog" in base or "noticia" in base or "news" in base:
        score -= 10

    return score


def deduplicar(lista):
    vistos = set()
    resultado = []

    for item in lista:
        chave = item.get("url")
        if not chave or chave in vistos:
            continue
        vistos.add(chave)
        resultado.append(item)

    return resultado


def buscar_em_curadores(curadores=None):
    curadores = curadores or CURADORES_BASE

    todas_pistas = []

    for url in curadores:
        print(f"🔎 Lendo curador intermediário: {url}")
        pistas = extrair_links_da_pagina(url)
        todas_pistas.extend(pistas)

    todas_pistas = deduplicar(todas_pistas)

    fortes = [p for p in todas_pistas if p["score"] >= 50]
    medias = [p for p in todas_pistas if 25 <= p["score"] < 50]
    fracas = [p for p in todas_pistas if p["score"] < 25]

    return {
        "fortes": fortes,
        "medias": medias,
        "fracas": fracas,
        "total": len(todas_pistas),
    }


def salvar_pistas(resultado, caminho="data/pistas_curadores.json"):
    path = Path(caminho)
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"✅ Pistas salvas em: {path}")


if __name__ == "__main__":
    resultado = buscar_em_curadores()
    salvar_pistas(resultado)