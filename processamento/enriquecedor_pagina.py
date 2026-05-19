# processamento/enriquecedor_pagina.py
"""
F.CULT — enriquecedor_pagina.py

Abre a URL real e enriquece o item com:
- h1/title/breadcrumb
- data publicada e prazo
- parágrafos principais
- links de edital/PDF/inscrição/licitação
- sinais escondidos de oportunidade

Uso:
    from processamento.enriquecedor_pagina import enriquecer_item_com_pagina
"""

import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FCultRadar/1.0)"
}

TIMEOUT = (8, 22)

TERMOS_INSCRICAO = [
    "inscreva", "inscrição", "inscrições", "inscricoes",
    "formulário de inscrição", "formulario de inscricao",
    "plataforma", "prosas", "mapa cultural", "mapa.cultura",
    "descentra", "submit", "apply", "application",
]

TERMOS_EDITAL = [
    "edital", "regulamento", "chamada pública", "chamada publica",
    "chamamento público", "chamamento publico", "seleção pública",
    "selecao publica", "termo de referência", "termo de referencia",
]

TERMOS_LICITACAO = [
    "licitação", "licitacao", "pregão", "pregao",
    "concorrência", "concorrencia", "contratação",
    "contratacao", "compras", "dispensa",
]


def _txt(valor):
    return str(valor or "").strip()


def limpar_texto(texto):
    return re.sub(r"\s+", " ", _txt(texto)).strip()


def normalizar_lower(texto):
    return limpar_texto(texto).lower()


def eh_url_http(url):
    return _txt(url).startswith(("http://", "https://"))


def baixar_html(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()

        ctype = resp.headers.get("content-type", "").lower()

        if "text/html" not in ctype and "<html" not in resp.text[:800].lower():
            return None

        return resp.text

    except Exception:
        return None


def extrair_title(soup):
    if soup.title and soup.title.string:
        return limpar_texto(soup.title.string)
    return ""


def extrair_h1(soup):
    h1 = soup.find("h1")
    if h1:
        return limpar_texto(h1.get_text(" ", strip=True))
    return ""


def extrair_breadcrumbs(soup):
    seletores = [
        ".breadcrumb",
        ".breadcrumbs",
        "[class*=breadcrumb]",
        "nav[aria-label*=breadcrumb]",
    ]

    for seletor in seletores:
        for el in soup.select(seletor):
            texto = limpar_texto(el.get_text(" ", strip=True))
            if texto and len(texto) < 300:
                return texto

    return ""


def extrair_data_texto(texto):
    texto = _txt(texto)

    padroes = [
        r"\b\d{1,2}/\d{1,2}/\d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{1,2}\s+de\s+[a-zçãé]+\s+de\s+\d{4}\b",
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s*\d{4}\b",
    ]

    for p in padroes:
        m = re.search(p, texto, flags=re.I)
        if m:
            return m.group(0)

    return None


def extrair_data_publicacao(soup, texto_total):
    metas = [
        "article:published_time",
        "date",
        "DC.date",
        "DC.Date",
        "publishdate",
        "pubdate",
        "datePublished",
    ]

    for nome in metas:
        meta = soup.find("meta", attrs={"property": nome}) or soup.find("meta", attrs={"name": nome})
        if meta and meta.get("content"):
            data = extrair_data_texto(meta.get("content"))
            if data:
                return data

    for t in soup.find_all("time"):
        valor = t.get("datetime") or t.get_text(" ", strip=True)
        data = extrair_data_texto(valor)
        if data:
            return data

    return extrair_data_texto(texto_total)


def extrair_paragrafos(soup):
    paragrafos = []

    for tag in soup(["script", "style", "noscript", "svg", "form"]):
        tag.decompose()

    for p in soup.find_all(["p", "li"]):
        texto = limpar_texto(p.get_text(" ", strip=True))

        if len(texto) < 40:
            continue

        base = normalizar_lower(texto)

        if any(lixo in base for lixo in [
            "uso de cookies", "utilizamos cookies", "compartilhe",
            "facebook", "twitter", "instagram", "linkedin",
            "voltar ao topo", "acessibilidade", "contraste",
        ]):
            continue

        paragrafos.append(texto)

        if len(paragrafos) >= 10:
            break

    return paragrafos


def pontuar_link(texto, href):
    base = normalizar_lower(f"{texto} {href}")
    score = 0

    for termo in TERMOS_EDITAL:
        if termo in base:
            score += 35

    for termo in TERMOS_INSCRICAO:
        if termo in base:
            score += 35

    for termo in TERMOS_LICITACAO:
        if termo in base:
            score += 25

    if ".pdf" in base:
        score += 20

    if any(t in base for t in [
        "audiovisual", "cinema", "fotografia", "filme",
        "vídeo", "video", "mostra", "festival"
    ]):
        score += 25

    if any(t in base for t in [
        "anexo", "recurso", "ata", "resultado final", "lista de inscritos"
    ]):
        score -= 50

    return score


def extrair_links_relevantes(soup, url_base):
    links = []

    for a in soup.find_all("a", href=True):
        texto = limpar_texto(a.get_text(" ", strip=True))
        href = urljoin(url_base, a.get("href"))

        if not eh_url_http(href):
            continue

        score = pontuar_link(texto, href)

        if score <= 0:
            continue

        links.append({
            "texto": texto,
            "url": href,
            "score": score,
        })

    return sorted(links, key=lambda x: x["score"], reverse=True)[:12]


def escolher_link_edital(links):
    for l in links:
        base = normalizar_lower(f"{l.get('texto')} {l.get('url')}")
        if any(t in base for t in TERMOS_EDITAL) and not any(r in base for r in [
            "recurso", "ata", "resultado", "lista de inscritos"
        ]):
            return l.get("url")

    for l in links:
        base = normalizar_lower(f"{l.get('texto')} {l.get('url')}")
        if ".pdf" in base and not any(r in base for r in [
            "recurso", "ata", "resultado", "lista de inscritos", "anexo"
        ]):
            return l.get("url")

    return None


def escolher_link_inscricao(links):
    for l in links:
        base = normalizar_lower(f"{l.get('texto')} {l.get('url')}")
        if any(t in base for t in TERMOS_INSCRICAO):
            return l.get("url")
    return None


def detectar_sinais(texto):
    base = normalizar_lower(texto)

    sinais = {
        "tem_edital": any(t in base for t in TERMOS_EDITAL),
        "tem_inscricao": any(t in base for t in TERMOS_INSCRICAO),
        "tem_licitacao": any(t in base for t in TERMOS_LICITACAO),
        "tem_audiovisual": any(t in base for t in [
            "audiovisual", "cinema", "filme", "fotografia",
            "vídeo", "video", "mostra", "festival"
        ]),
        "tem_prazo": any(t in base for t in [
            "prazo", "deadline", "até ", "ate ", "encerra", "encerramento"
        ]),
        "tem_pnab_lpg": any(t in base for t in [
            "pnab", "lpg", "lei paulo gustavo", "aldir blanc"
        ]),
    }

    score = 0
    if sinais["tem_edital"]:
        score += 35
    if sinais["tem_inscricao"]:
        score += 35
    if sinais["tem_licitacao"]:
        score += 20
    if sinais["tem_audiovisual"]:
        score += 30
    if sinais["tem_prazo"]:
        score += 25
    if sinais["tem_pnab_lpg"]:
        score += 25

    sinais["score_enriquecimento"] = score

    return sinais


def enriquecer_item_com_pagina(item):
    if not isinstance(item, dict):
        return item

    url = item.get("link") or item.get("url") or item.get("link_edital")

    if not eh_url_http(url):
        return item

    html = baixar_html(url)

    if not html:
        return item

    soup = BeautifulSoup(html, "html.parser")

    h1 = extrair_h1(soup)
    title = extrair_title(soup)
    breadcrumbs = extrair_breadcrumbs(soup)
    paragrafos = extrair_paragrafos(soup)

    texto_pagina = limpar_texto(" ".join([h1, title, breadcrumbs] + paragrafos))

    data_publicacao = extrair_data_publicacao(soup, texto_pagina)
    data_prazo = extrair_data_texto(texto_pagina)

    links = extrair_links_relevantes(soup, url)
    link_edital = escolher_link_edital(links)
    link_inscricao = escolher_link_inscricao(links)

    sinais = detectar_sinais(
        texto_pagina + " " +
        " ".join([l.get("texto", "") + " " + l.get("url", "") for l in links])
    )

    enriquecido = dict(item)

    enriquecido["titulo_pagina"] = h1 or title or item.get("titulo")
    enriquecido["titulo_principal"] = h1 or item.get("titulo_principal") or item.get("titulo")
    enriquecido["page_title"] = title
    enriquecido["breadcrumbs"] = breadcrumbs
    enriquecido["texto_pagina"] = texto_pagina[:2500]
    enriquecido["resumo_pagina"] = " ".join(paragrafos[:3])[:700]
    enriquecido["data_publicacao"] = item.get("data_publicacao") or data_publicacao
    enriquecido["published_at"] = item.get("published_at") or data_publicacao
    enriquecido["prazo"] = item.get("prazo") or item.get("deadline") or data_prazo
    enriquecido["deadline"] = enriquecido["prazo"]

    if link_edital:
        enriquecido["link_edital"] = link_edital

    if link_inscricao:
        enriquecido["link_inscricao"] = link_inscricao

    enriquecido["links_relevantes"] = links
    enriquecido["sinais_pagina"] = sinais
    enriquecido["score_enriquecimento"] = sinais.get("score_enriquecimento", 0)

    if sinais.get("tem_licitacao"):
        enriquecido["categoria_hint"] = "licitacoes"
    elif sinais.get("tem_edital") or sinais.get("tem_pnab_lpg"):
        enriquecido["categoria_hint"] = "editais"
    elif sinais.get("tem_inscricao") or sinais.get("tem_prazo"):
        enriquecido["categoria_hint"] = "oportunidades"

    return enriquecido
