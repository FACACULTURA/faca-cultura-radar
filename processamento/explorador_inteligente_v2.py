# processamento/explorador_inteligente_v2.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FCultRadar/2.0)"
}

TIMEOUT = (5, 15)

# 🔥 termos que justificam exploração
TERMOS_INTERESSE = [
    "audiovisual", "cinema", "filme", "vídeo", "video",
    "fotografia", "festival", "mostra", "edital",
    "inscrição", "inscricoes", "chamada", "cultura"
]

# 🔥 termos lixo
TERMOS_LIXO = [
    "anexo", "recurso", "ata", "resultado",
    "lista de inscritos", "cookies", "privacidade"
]


def eh_url_valida(url):
    return url.startswith("http")


def texto_limpo(txt):
    return " ".join((txt or "").split()).strip()


def tem_interesse(texto):
    texto = texto.lower()
    return any(t in texto for t in TERMOS_INTERESSE)


def eh_lixo(texto):
    texto = texto.lower()
    return any(t in texto for t in TERMOS_LIXO)


def baixar_html(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        if "html" not in r.headers.get("content-type", ""):
            return None
        return r.text
    except:
        return None


def extrair_links(soup, base_url):
    links = []

    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"])
        texto = texto_limpo(a.get_text())

        if not eh_url_valida(href):
            continue

        if eh_lixo(texto):
            continue

        if len(texto) < 3:
            continue

        links.append({
            "url": href,
            "texto": texto
        })

    return links


def explorar_pagina(url, profundidade=1, max_links=10):
    """
    🔥 Função principal:
    entra na página e explora links internos relevantes
    """

    html = baixar_html(url)

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    resultados = []

    # 🔥 extrai links da página
    links = extrair_links(soup, url)

    # 🔥 prioriza links com palavras relevantes
    links_priorizados = []

    for l in links:
        score = 0
        texto = (l["texto"] + " " + l["url"]).lower()

        if any(t in texto for t in TERMOS_INTERESSE):
            score += 10

        if ".pdf" in texto:
            score += 8

        if "edital" in texto:
            score += 10

        if "inscr" in texto:
            score += 10

        links_priorizados.append((score, l))

    links_priorizados.sort(reverse=True, key=lambda x: x[0])

    # 🔥 limita exploração
    selecionados = [l for _, l in links_priorizados[:max_links]]

    for link in selecionados:
        resultados.append(link)

        # 🔥 exploração profunda (nível 2)
        if profundidade > 1:
            time.sleep(0.5)  # evita bloqueio
            sub_links = explorar_pagina(link["url"], profundidade=profundidade-1, max_links=5)
            resultados.extend(sub_links)

    return resultados


def enriquecer_com_exploracao(item):
    """
    🔥 Integra com seu motor:
    pega o item e adiciona links descobertos
    """

    url = item.get("link") or item.get("url")

    if not url:
        return item

    novos_links = explorar_pagina(url, profundidade=2)

    item["links_explorados"] = novos_links

    # 🔥 tenta encontrar link de edital escondido
    for l in novos_links:
        texto = (l["texto"] + " " + l["url"]).lower()

        if "edital" in texto or ".pdf" in texto:
            item["link_edital"] = l["url"]

        if "inscr" in texto:
            item["link_inscricao"] = l["url"]

    return item