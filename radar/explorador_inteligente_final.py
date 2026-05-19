# explorador_inteligente.py

from pathlib import Path
from urllib.parse import urljoin, urlparse
from collections import deque
from datetime import datetime
import requests
import json
import re
import time

from bs4 import BeautifulSoup


# ============================================================
# CAMINHOS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BRUTO_DIR = DATA_DIR / "bruto"
URLS_CANDIDATAS = BRUTO_DIR / "urls_candidatas.json"

FONTES_PADRAO = BASE_DIR / "coleta" / "config_fontes" / "fontes.json"


# ============================================================
# CONFIG
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

PALAVRAS_FORTES = [
    "edital", "editais", "chamada", "chamamento", "seleção", "selecao",
    "inscrição", "inscrições", "inscricao", "inscricoes",
    "regulamento", "resultado", "premiação", "premiacao",
    "fomento", "incentivo", "bolsa", "apoio", "financiamento",
    "licitação", "licitacao", "pregão", "pregao",
    "audiovisual", "cinema", "filme", "documentário", "documentario",
    "festival", "mostra", "laboratório", "laboratorio", "residência",
    "residencia", "pitching", "coprodução", "coproducao",
    "lei rouanet", "pnab", "lei paulo gustavo", "lpg", "fsa",
    "salic", "pronac", "mecenato", "captação", "captacao",
]

PALAVRAS_CAMINHO = [
    "cultura", "programas", "programa", "notícias", "noticias",
    "transparência", "transparencia", "publicações", "publicacoes",
    "serviços", "servicos", "oportunidades", "agenda",
    "comunicados", "imprensa", "institucional", "fomento",
    "editais", "lei de incentivo", "audiovisual",
]

PALAVRAS_INSCRICAO = [
    "inscreva-se", "inscrever", "formulário", "formulario",
    "forms.gle", "docs.google.com/forms", "typeform", "airtable",
    "application", "apply", "submit", "submission"
]

EXTENSOES_DOCUMENTOS = [
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".odt", ".ods"
]


# ============================================================
# UTILITÁRIOS
# ============================================================

def normalizar(texto):
    if not texto:
        return ""
    texto = str(texto).lower()
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def salvar_json(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def carregar_json(caminho, chave=None):
    path = Path(caminho)

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if chave and isinstance(data, dict):
        return data.get(chave, [])

    if isinstance(data, dict) and "fontes" in data:
        return data.get("fontes", [])

    if isinstance(data, list):
        return data

    return []


def dominio(url):
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def limpar_url(url):
    if not url:
        return ""

    url = url.strip()

    if "#" in url:
        url = url.split("#")[0]

    return url.rstrip("/")


def eh_documento(url):
    url_lower = normalizar(url)
    return any(ext in url_lower for ext in EXTENSOES_DOCUMENTOS)


def eh_formulario(url):
    url_lower = normalizar(url)
    return any(p in url_lower for p in PALAVRAS_INSCRICAO)


def url_valida(url):
    if not url:
        return False

    if url.startswith("mailto:"):
        return False

    if url.startswith("tel:"):
        return False

    if url.startswith("javascript:"):
        return False

    return url.startswith("http")


def extrair_url_fonte(fonte):
    if isinstance(fonte, str):
        return fonte

    if isinstance(fonte, dict):
        return (
            fonte.get("url")
            or fonte.get("link")
            or fonte.get("site")
            or fonte.get("fonte")
            or ""
        )

    return ""


def extrair_nome_fonte(fonte, url):
    if isinstance(fonte, dict):
        return fonte.get("nome") or fonte.get("titulo") or dominio(url)

    return dominio(url)


# ============================================================
# SCORE
# ============================================================

def score_fonte(fonte, url):
    texto = normalizar(json.dumps(fonte, ensure_ascii=False)) if isinstance(fonte, dict) else normalizar(url)
    host = dominio(url)

    score = 0

    if ".gov.br" in host or "gov.br" in host:
        score += 50

    if any(p in texto for p in ["secretaria", "secult", "fundação", "fundacao"]):
        score += 35

    if any(p in texto for p in ["cultura", "audiovisual", "cinema"]):
        score += 25

    if any(p in texto for p in ["minc", "ancine", "prefeitura", "estado", "governo"]):
        score += 30

    if any(p in texto for p in ["festival", "mostra", "film commission", "instituto", "fundo"]):
        score += 20

    if any(p in texto for p in ["lei rouanet", "pnab", "lpg", "fsa", "salic", "pronac"]):
        score += 30

    if any(p in texto for p in ["blog", "noticia", "revista"]):
        score += 5

    return score


def score_link(texto, url, pagina_relevante=False):
    texto_total = normalizar(f"{texto} {url}")

    score = 0

    for palavra in PALAVRAS_FORTES:
        if palavra in texto_total:
            score += 8

    for palavra in PALAVRAS_CAMINHO:
        if palavra in texto_total:
            score += 3

    for palavra in PALAVRAS_INSCRICAO:
        if palavra in texto_total:
            score += 12

    if eh_documento(url):
        score += 20

    if eh_formulario(url):
        score += 25

    if pagina_relevante:
        score += 5

    if any(lixo in texto_total for lixo in [
        "facebook", "instagram", "youtube", "twitter", "x.com",
        "linkedin", "whatsapp", "privacy", "cookies", "termos-de-uso",
        "politica-de-privacidade"
    ]):
        score -= 10

    return score


# ============================================================
# HTML
# ============================================================

def baixar_html(url, timeout=18):
    try:
        resposta = requests.get(url, headers=HEADERS, timeout=timeout, verify=False)

        if resposta.status_code >= 400:
            return None

        content_type = resposta.headers.get("content-type", "").lower()

        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return None

        resposta.encoding = resposta.apparent_encoding
        return resposta.text

    except Exception:
        return None


def classificar_pagina(html, url):
    soup = BeautifulSoup(html, "html.parser")

    titulo = ""
    if soup.title:
        titulo = soup.title.get_text(" ", strip=True)

    h1 = soup.find("h1")
    if h1:
        titulo = h1.get_text(" ", strip=True) or titulo

    texto = soup.get_text(" ", strip=True)
    texto_norm = normalizar(texto)

    score = 0

    for palavra in PALAVRAS_FORTES:
        if palavra in texto_norm:
            score += 5

    for palavra in PALAVRAS_INSCRICAO:
        if palavra in texto_norm:
            score += 8

    if ".pdf" in texto_norm:
        score += 10

    if "prazo" in texto_norm or "deadline" in texto_norm:
        score += 10

    if "inscri" in texto_norm:
        score += 10

    if "edital" in texto_norm:
        score += 12

    if any(p in texto_norm for p in ["lei rouanet", "pnab", "lei paulo gustavo", "fsa", "salic", "pronac"]):
        score += 18

    tipo = "caminho"

    if score >= 35:
        tipo = "forte"
    elif score >= 15:
        tipo = "media"
    elif any(p in texto_norm for p in PALAVRAS_CAMINHO):
        tipo = "caminho"
    else:
        tipo = "fraca"

    return {
        "titulo": titulo or url,
        "tipo_pagina": tipo,
        "score_pagina": score,
        "resumo": texto[:700],
    }


def extrair_links(html, url_base, dominio_origem, pagina_relevante=False):
    soup = BeautifulSoup(html, "html.parser")
    links = []

    for a in soup.find_all("a", href=True):
        href = limpar_url(a.get("href", ""))
        texto = a.get_text(" ", strip=True)

        absoluto = limpar_url(urljoin(url_base, href))

        if not url_valida(absoluto):
            continue

        host_link = dominio(absoluto)
        externo_util = eh_formulario(absoluto)

        # mantém mesmo domínio; permite formulários externos
        if host_link != dominio_origem and not externo_util:
            continue

        s = score_link(texto, absoluto, pagina_relevante=pagina_relevante)

        if s <= 0:
            continue

        links.append({
            "url": absoluto,
            "texto": texto,
            "score_link": s,
            "tipo_link": "documento" if eh_documento(absoluto) else "formulario" if eh_formulario(absoluto) else "pagina",
        })

    links.sort(key=lambda x: x["score_link"], reverse=True)
    return links


def montar_candidato(url, fonte_nome, origem, score, tipo, profundidade, texto=""):
    return {
        "url": url,
        "fonte": fonte_nome,
        "origem": origem,
        "tipo_candidato": tipo,
        "score_candidato": score,
        "profundidade": profundidade,
        "texto_link": texto,
        "data_exploracao": datetime.now().isoformat(),
    }


# ============================================================
# EXPLORA UMA FONTE
# ============================================================

def explorar_fonte(
    fonte,
    profundidade_max=3,
    limite_paginas=60,
    pausa=0.4,
    score_minimo_continuar=8
):
    url_inicial = limpar_url(extrair_url_fonte(fonte))

    if not url_inicial:
        return []

    if not url_inicial.startswith("http"):
        url_inicial = "https://" + url_inicial

    nome_fonte = extrair_nome_fonte(fonte, url_inicial)
    dominio_origem = dominio(url_inicial)
    prioridade = score_fonte(fonte, url_inicial)

    if prioridade < 10:
        print(f"⚠️ Fonte fraca ignorada: {nome_fonte} — {url_inicial}")
        return []

    fila = deque()
    visitadas = set()
    candidatos = []

    fila.append({
        "url": url_inicial,
        "profundidade": 0,
        "origem": "fonte_inicial",
        "score_entrada": prioridade,
    })

    while fila and len(visitadas) < limite_paginas:
        atual = fila.popleft()
        url = atual["url"]
        profundidade = atual["profundidade"]

        if url in visitadas:
            continue

        visitadas.add(url)

        if eh_documento(url):
            candidatos.append(
                montar_candidato(
                    url=url,
                    fonte_nome=nome_fonte,
                    origem=atual.get("origem", "documento"),
                    score=atual.get("score_entrada", 0) + 20,
                    tipo="documento",
                    profundidade=profundidade,
                )
            )
            continue

        html = baixar_html(url)

        if not html:
            continue

        analise = classificar_pagina(html, url)
        pagina_relevante = analise["tipo_pagina"] in ["forte", "media"]

        if pagina_relevante:
            candidatos.append(
                montar_candidato(
                    url=url,
                    fonte_nome=nome_fonte,
                    origem=atual.get("origem", "pagina"),
                    score=analise["score_pagina"] + prioridade,
                    tipo=analise["tipo_pagina"],
                    profundidade=profundidade,
                    texto=analise.get("titulo", ""),
                )
            )

        links = extrair_links(
            html=html,
            url_base=url,
            dominio_origem=dominio_origem,
            pagina_relevante=pagina_relevante,
        )

        for link in links:
            link_url = link["url"]
            score_total = link["score_link"] + analise["score_pagina"]

            if link["tipo_link"] in ["documento", "formulario"]:
                candidatos.append(
                    montar_candidato(
                        url=link_url,
                        fonte_nome=nome_fonte,
                        origem=url,
                        score=score_total + prioridade,
                        tipo=link["tipo_link"],
                        profundidade=profundidade + 1,
                        texto=link.get("texto", ""),
                    )
                )
                continue

            if profundidade < profundidade_max and score_total >= score_minimo_continuar:
                if link_url not in visitadas:
                    fila.append({
                        "url": link_url,
                        "profundidade": profundidade + 1,
                        "origem": url,
                        "score_entrada": score_total,
                    })

        time.sleep(pausa)

    candidatos_unicos = {}

    for item in candidatos:
        url = item["url"]

        if url not in candidatos_unicos:
            candidatos_unicos[url] = item
        else:
            if item["score_candidato"] > candidatos_unicos[url]["score_candidato"]:
                candidatos_unicos[url] = item

    resultado = list(candidatos_unicos.values())
    resultado.sort(key=lambda x: x["score_candidato"], reverse=True)

    print(f"✅ {nome_fonte}: {len(resultado)} candidatos / {len(visitadas)} páginas visitadas")
    return resultado


# ============================================================
# EXECUTA EXPLORAÇÃO
# ============================================================

def executar_exploracao(fontes=None):
    print("\n🚀 Iniciando exploração inteligente...\n")

    if fontes is None:
        fontes = carregar_json(FONTES_PADRAO, "fontes")

    if not fontes:
        print("[ERRO] Nenhuma fonte fornecida.")
        salvar_json(URLS_CANDIDATAS, [])
        return []

    print(f"Fontes recebidas: {len(fontes)}")

    todos_candidatos = []

    for fonte in fontes:
        try:
            nome = fonte.get("nome", "Fonte") if isinstance(fonte, dict) else str(fonte)
            url = extrair_url_fonte(fonte)

            if not url:
                continue

            peso = 1
            if isinstance(fonte, dict):
                peso = fonte.get("peso_exploracao", 1) or 1

            profundidade = 1
            limite_paginas = 30

            if peso >= 3:
                profundidade = 3
                limite_paginas = 80
            elif peso == 2:
                profundidade = 2
                limite_paginas = 55

            print(f"\n🔎 Explorando: {nome} | peso={peso} | profundidade={profundidade}")

            candidatos = explorar_fonte(
                fonte,
                profundidade_max=profundidade,
                limite_paginas=limite_paginas
            )

            print(f"→ {len(candidatos)} candidatos encontrados")
            todos_candidatos.extend(candidatos)

        except Exception as e:
            print(f"[ERRO NA FONTE] {fonte}: {e}")

    unicos = {}

    for item in todos_candidatos:
        url = item["url"]

        if url not in unicos:
            unicos[url] = item
        else:
            if item["score_candidato"] > unicos[url]["score_candidato"]:
                unicos[url] = item

    resultado = list(unicos.values())
    resultado.sort(key=lambda x: x["score_candidato"], reverse=True)

    salvar_json(URLS_CANDIDATAS, resultado)

    print("\n📊 Exploração finalizada")
    print(f"Total de candidatos: {len(resultado)}")
    print(f"📁 Salvo em: {URLS_CANDIDATAS}\n")

    return resultado


if __name__ == "__main__":
    executar_exploracao()
