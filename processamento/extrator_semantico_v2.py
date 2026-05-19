# =========================================================
# F.CULT — EXTRATOR SEMÂNTICO V3
# foco:
# - separar ruído de conteúdo principal
# - gerar título semântico limpo
# - preservar sinais contextuais
# - não descartar cedo demais
# - leitura por região semântica
# =========================================================

import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup


PALAVRAS_RUIDO = [
    "read more",
    "saiba mais",
    "clique aqui",
    "tags:",
    "publicado",
    "notícias",
    "noticias",
    "home",
    "menu",
    "galeria",
    "copyright",
    "todos os direitos reservados",
]

PALAVRAS_EDITAL = [
    "edital",
    "chamada",
    "seleção",
    "inscrições abertas para edital",
    "convocatória",
    "pitching",
    "laboratório",
    "residência",
]

PALAVRAS_RESULTADO = [
    "resultado final",
    "resultado preliminar",
    "homologação",
    "ata",
    "ata comissão julgadora",
    "convocação",
    "selecionados",
]

PALAVRAS_AUDIOVISUAL = [
    "audiovisual",
    "cinema",
    "filme",
    "documentário",
    "animação",
    "série",
    "roteiro",
    "curta",
    "longa",
    "videoart",
    "videopoesia",
    "videoarte",
    "videoclipe",
    "videoclip",

]

SELETORES_RUIDO = [
    "script",
    "style",
    "noscript",
    "header",
    "footer",
    "nav",
    "aside",
    "form",
    "iframe",
    ".menu",
    ".navbar",
    ".nav",
    ".footer",
    ".sidebar",
    ".breadcrumb",
    ".breadcrumbs",
    ".cookie",
    ".cookies",
    ".share",
    ".social",
    ".widget",
    ".related",
    ".relacionados",
    ".pagination",
    "#menu",
    "#footer",
    "#header",
    "#sidebar",
]


# =========================================================
# LIMPEZA
# =========================================================

def limpar_texto(texto: str) -> str:
    if not texto:
        return ""

    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\n+", " ", texto)
    texto = texto.strip()

    return texto


def texto_ruim(texto: str) -> bool:
    texto = texto.lower()

    score = 0

    for termo in PALAVRAS_RUIDO:
        if termo in texto:
            score += 1

    return score >= 3


def remover_ruido_html(soup):
    for seletor in SELETORES_RUIDO:
        for bloco in soup.select(seletor):
            bloco.decompose()
    return soup


# =========================================================
# HIERARQUIA SEMÂNTICA
# =========================================================

def extrair_h1(soup) -> Optional[str]:
    h1 = soup.find("h1")

    if h1:
        return limpar_texto(h1.get_text())

    return None


def extrair_h2(soup):
    encontrados = []

    for h2 in soup.find_all("h2"):
        texto = limpar_texto(h2.get_text())

        if len(texto) > 20:
            encontrados.append(texto)

    return encontrados


def extrair_paragrafos(soup):
    paragrafos = []

    for p in soup.find_all("p"):
        texto = limpar_texto(p.get_text())

        if len(texto) > 40:
            paragrafos.append(texto)

    return paragrafos


def encontrar_bloco_principal(soup):
    seletores = [
        "main",
        "article",
        ".content",
        ".conteudo",
        ".main-content",
        ".entry-content",
        ".post-content",
        ".news-content",
        ".corpo",
        ".texto",
        ".materia",
        ".page-content",
    ]

    candidatos = []

    for seletor in seletores:
        for el in soup.select(seletor):
            texto = limpar_texto(el.get_text(" ", strip=True))
            if len(texto) > 120:
                candidatos.append((len(texto), texto))

    if candidatos:
        candidatos.sort(reverse=True, key=lambda x: x[0])
        return candidatos[0][1]

    body = soup.body or soup
    return limpar_texto(body.get_text(" ", strip=True))


def leitura_por_regiao_semantica(soup):
    titulo = extrair_h1(soup)

    if not titulo and soup.title:
        titulo = limpar_texto(soup.title.get_text(" ", strip=True))

    h2s = extrair_h2(soup)
    subtitulo = h2s[0] if h2s else ""

    paragrafos = extrair_paragrafos(soup)
    primeiro_paragrafo = paragrafos[0] if paragrafos else ""

    bloco_principal = encontrar_bloco_principal(soup)

    partes = []

    if titulo:
        partes.extend([titulo] * 5)

    if subtitulo:
        partes.extend([subtitulo] * 3)

    if primeiro_paragrafo:
        partes.extend([primeiro_paragrafo] * 3)

    if bloco_principal:
        partes.append(bloco_principal[:5000])

    return {
        "titulo": titulo,
        "subtitulo": subtitulo,
        "primeiro_paragrafo": primeiro_paragrafo,
        "bloco_principal": bloco_principal,
        "texto_semantico": limpar_texto(" ".join(partes)),
    }


# =========================================================
# SCORE SEMÂNTICO
# =========================================================

def pontuar_titulo(texto: str) -> int:
    texto_lower = texto.lower()

    score = 0

    for termo in PALAVRAS_EDITAL:
        if termo in texto_lower:
            score += 5

    for termo in PALAVRAS_AUDIOVISUAL:
        if termo in texto_lower:
            score += 3

    for termo in PALAVRAS_RESULTADO:
        if termo in texto_lower:
            score -= 8

    if texto_ruim(texto):
        score -= 5

    return score


# =========================================================
# TÍTULO PRINCIPAL
# =========================================================

def gerar_titulo_semantico(soup, item, leitura_regional=None):
    candidatos = []

    if leitura_regional and leitura_regional.get("titulo"):
        candidatos.append(leitura_regional.get("titulo"))

    h1 = extrair_h1(soup)

    if h1:
        candidatos.append(h1)

    candidatos.extend(extrair_h2(soup))

    candidatos.extend([
        item.get("titulo"),
        item.get("titulo_pagina"),
        item.get("page_title"),
    ])

    candidatos = [limpar_texto(c) for c in candidatos if c]

    if not candidatos:
        return None

    candidatos = sorted(
        candidatos,
        key=lambda x: pontuar_titulo(x),
        reverse=True
    )

    titulo = candidatos[0]

    titulo = re.sub(r"tags?:.*", "", titulo, flags=re.IGNORECASE)
    titulo = re.sub(r"publicado.*", "", titulo, flags=re.IGNORECASE)

    titulo = limpar_texto(titulo)



def encurtar_titulo(titulo):
    if not titulo:
        return titulo

    titulo = limpar_texto(titulo)

    padroes = [
        r"(Edital\s+\d+[^-–]*[-–]\s*[^.]{10,80})",
        r"(Edital\s+[^.]{10,80})",
        r"(Chamada Pública\s+[^.]{10,80})",
        r"(Seleção\s+[^.]{10,80})",
        r"(Prêmio\s+[^.]{10,80})",
        r"(Festival\s+[^.]{10,80})",
        r"(Mostra\s+[^.]{10,80})",
        r"(Residência\s+[^.]{10,80})",
        r"(Laboratório\s+[^.]{10,80})",
    ]

    for padrao in padroes:
        m = re.search(padrao, titulo, flags=re.IGNORECASE)
        if m:
            return limpar_texto(m.group(1))[:100]

    partes = re.split(r"[-–|:]", titulo)

    for parte in partes:
        parte = limpar_texto(parte)
        if 20 <= len(parte) <= 100:
            return parte

    palavras = titulo.split()
    if len(palavras) > 12:
        return " ".join(palavras[:12]) + "..."

    return encurtar_titulo(titulo)


# =========================================================
# RESUMO
# =========================================================

def gerar_resumo_semantico(soup, leitura_regional=None):
    if leitura_regional:
        primeiro = leitura_regional.get("primeiro_paragrafo")
        if primeiro and not texto_ruim(primeiro):
            return primeiro[:400]

    paragrafos = extrair_paragrafos(soup)

    if not paragrafos:
        return None

    melhores = []

    for p in paragrafos:
        if texto_ruim(p):
            continue

        score = pontuar_titulo(p)

        melhores.append((score, p))

    if not melhores:
        return None

    melhores = sorted(melhores, reverse=True)

    return melhores[0][1][:400]


# =========================================================
# CLASSIFICAÇÃO CONTEXTUAL
# =========================================================

def detectar_contexto(texto: str):
    texto = texto.lower()

    for termo in PALAVRAS_RESULTADO:
        if termo in texto:
            return "resultado"

    for termo in PALAVRAS_EDITAL:
        if termo in texto:
            return "edital"

    return "noticia"


# =========================================================
# EXTRATOR PRINCIPAL
# =========================================================

def extrair_semantica_v3(item: Dict[str, Any]) -> Dict[str, Any]:

    html = item.get("html") or item.get("html_bruto") or item.get("conteudo_html") or ""

    soup = BeautifulSoup(html, "html.parser")
    soup = remover_ruido_html(soup)

    leitura_regional = leitura_por_regiao_semantica(soup)

    titulo = gerar_titulo_semantico(soup, item, leitura_regional)

    resumo = gerar_resumo_semantico(soup, leitura_regional)

    texto_total = leitura_regional.get("texto_semantico") or limpar_texto(soup.get_text(" "))

    contexto = detectar_contexto(texto_total)

    resultado = dict(item)

    resultado.update({

        "titulo_principal": titulo,

        "resumo": resumo,

        "tipo_contexto": contexto,

        "possivel_lixo": texto_ruim(texto_total),

        "titulo_regional": leitura_regional.get("titulo"),

        "subtitulo_regional": leitura_regional.get("subtitulo"),

        "primeiro_paragrafo": leitura_regional.get("primeiro_paragrafo"),

        "texto_semantico_regional": leitura_regional.get("texto_semantico"),

        "leitura_semantica": {
            "tipo_contexto": contexto,
            "titulo_semantico": titulo,
        }

    })

    return resultado


# =========================================================
# COMPATIBILIDADE COM MOTOR
# =========================================================

def extrair_item_semantico(item):
    return extrair_semantica_v3(item)