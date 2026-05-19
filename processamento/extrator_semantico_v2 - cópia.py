# =========================================================
# F.CULT — EXTRATOR SEMÂNTICO V3
# foco:
# - separar ruído de conteúdo principal
# - gerar título semântico limpo
# - preservar sinais contextuais
# - não descartar cedo demais
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
    "inscrições abertas",
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

def gerar_titulo_semantico(soup, item):
    candidatos = []

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

    return titulo


# =========================================================
# RESUMO
# =========================================================

def gerar_resumo_semantico(soup):
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

    html = item.get("html") or ""
    soup = BeautifulSoup(html, "html.parser")

    titulo = gerar_titulo_semantico(soup, item)

    resumo = gerar_resumo_semantico(soup)

    texto_total = limpar_texto(soup.get_text(" "))

    contexto = detectar_contexto(texto_total)

    resultado = dict(item)

    resultado.update({

        "titulo_principal": titulo,

        "resumo": resumo,

        "tipo_contexto": contexto,

        "possivel_lixo": texto_ruim(texto_total),

        "leitura_semantica": {
            "tipo_contexto": contexto,
            "titulo_semantico": titulo,
        }

    })

    return resultado

    return resultado


# =========================================================
# COMPATIBILIDADE COM MOTOR
# =========================================================

def extrair_item_semantico(item):
    return extrair_semantica_v3(item)