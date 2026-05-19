# backend/radar/descoberta_autonoma.py

from urllib.parse import urlparse
from datetime import datetime
import json
import os


ARQUIVO_ENTRADA = "data/input/pistas.json"
ARQUIVO_SAIDA = "data/output/fontes_autonomas.json"


PALAVRAS_POSITIVAS = [
    "cultura",
    "secretaria",
    "fundacao",
    "fundação",
    "audiovisual",
    "cinema",
    "festival",
    "film",
    "lab",
    "fund",
    "grant",
    "edital",
    "fomento",
    "chamamento",
    "chamada",
    "mostra",
    "instituto",
    "minc",
    "ancine",
    "spcine",
    "riofilme",
    "funarte",
    "brde",
    "pnab",
    "rouanet",
]


PALAVRAS_NEGATIVAS = [
    "blog",
    "noticia",
    "notícia",
    "news",
    "materia",
    "matéria",
    "post",
    "instagram",
    "facebook",
    "linkedin",
    "youtube",
    "twitter",
    "x.com",
]


def normalizar_url(url: str) -> str:
    if not url:
        return ""

    url = str(url).strip()

    if not url.startswith("http"):
        url = "https://" + url

    return url


def extrair_dominio(url: str) -> str:
    url = normalizar_url(url)
    parsed = urlparse(url)

    dominio = parsed.netloc.lower()

    if dominio.startswith("www."):
        dominio = dominio[4:]

    return dominio


def identificar_tipo(dominio: str, url: str = "") -> str:
    texto = f"{dominio} {url}".lower()

    if ".gov.br" in dominio or ".gov" in dominio:
        return "governo"

    if "festival" in texto or "filmfestival" in texto:
        return "festival"

    if "film" in texto or "cinema" in texto or "audiovisual" in texto:
        return "audiovisual"

    if "fund" in texto or "grant" in texto or "lab" in texto:
        return "fomento_internacional"

    if "instituto" in texto or "fundacao" in texto or "fundação" in texto:
        return "instituicao_cultural"

    return "indefinido"


def calcular_score(dominio: str, url: str = "", titulo: str = "", resumo: str = "") -> int:
    texto = f"{dominio} {url} {titulo} {resumo}".lower()

    score = 0

    if ".gov.br" in dominio:
        score += 50

    elif ".gov" in dominio:
        score += 40

    if ".org" in dominio:
        score += 20

    if ".edu" in dominio:
        score += 15

    for palavra in PALAVRAS_POSITIVAS:
        if palavra in texto:
            score += 10

    for palavra in PALAVRAS_NEGATIVAS:
        if palavra in texto:
            score -= 20

    partes = dominio.split(".")
    if len(partes) > 4:
        score -= 10

    return max(0, min(score, 100))


def classificar_status(score: int) -> str:
    if score >= 70:
        return "fonte_confiavel"

    if score >= 45:
        return "revisao"

    return "descartar"


def carregar_json(caminho: str, padrao):
    if not os.path.exists(caminho):
        return padrao

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return padrao


def salvar_json(caminho: str, dados):
    pasta = os.path.dirname(caminho)

    if pasta:
        os.makedirs(pasta, exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def normalizar_pistas(dados):
    if isinstance(dados, list):
        return dados

    if isinstance(dados, dict):
        pistas = []

        for chave in ["fortes", "medias", "fracas", "results", "pistas"]:
            valor = dados.get(chave)
            if isinstance(valor, list):
                pistas.extend(valor)

        return pistas

    return []


def descobrir_fontes(pistas: list[dict]) -> list[dict]:
    fontes_por_dominio = {}

    for pista in normalizar_pistas(pistas):
        if not isinstance(pista, dict):
            continue

        url = pista.get("url") or pista.get("link") or pista.get("origem") or ""
        titulo = pista.get("titulo") or pista.get("title") or ""
        resumo = pista.get("resumo") or pista.get("snippet") or pista.get("descricao") or ""

        if not url:
            continue

        dominio = extrair_dominio(url)

        if not dominio:
            continue

        score = calcular_score(dominio, url, titulo, resumo)
        tipo = identificar_tipo(dominio, url)
        status = classificar_status(score)

        fonte = {
            "dominio": dominio,
            "url": f"https://{dominio}",
            "url_base": f"https://{dominio}",
            "nome": dominio,
            "tipo": tipo,
            "score": score,
            "score_confianca": score,
            "status": status,
            "ativo": status != "descartar",
            "origem": "descoberta_autonoma",
            "origem_tipo": "fonte_descoberta",
            "primeira_pista": {
                "url": url,
                "titulo": titulo,
                "resumo": resumo,
            },
            "atualizado_em": datetime.now().isoformat(),
        }

        if dominio not in fontes_por_dominio:
            fontes_por_dominio[dominio] = fonte
        else:
            if score > fontes_por_dominio[dominio].get("score_confianca", 0):
                fontes_por_dominio[dominio] = fonte

    return sorted(
        fontes_por_dominio.values(),
        key=lambda x: x.get("score_confianca", 0),
        reverse=True,
    )


def atualizar_fontes():
    pistas = carregar_json(ARQUIVO_ENTRADA, [])
    fontes_existentes = carregar_json(ARQUIVO_SAIDA, [])

    pistas = normalizar_pistas(pistas)
    fontes_existentes = normalizar_pistas(fontes_existentes)

    novas_fontes = descobrir_fontes(pistas)

    mapa = {}

    for fonte in fontes_existentes:
        dominio = fonte.get("dominio") or extrair_dominio(fonte.get("url") or fonte.get("url_base") or "")
        if dominio:
            mapa[dominio] = fonte

    for fonte in novas_fontes:
        dominio = fonte.get("dominio")

        if not dominio:
            continue

        if dominio not in mapa:
            mapa[dominio] = fonte
        else:
            score_novo = fonte.get("score_confianca", 0)
            score_antigo = mapa[dominio].get("score_confianca", 0)

            if score_novo > score_antigo:
                mapa[dominio].update(fonte)

    resultado = sorted(
        mapa.values(),
        key=lambda x: x.get("score_confianca", 0),
        reverse=True,
    )

    salvar_json(ARQUIVO_SAIDA, resultado)

    return resultado


# Alias esperado pelo core/motor_oportunidades.py
def atualizar_fontes_autonomas(fontes_base=None):
    return atualizar_fontes()


if __name__ == "__main__":
    fontes = atualizar_fontes()

    print("\n[F.CULT] Descoberta autônoma finalizada.")
    print(f"Fontes encontradas/atualizadas: {len(fontes)}\n")

    for fonte in fontes[:20]:
        print(
            f"{fonte.get('score_confianca', 0):>3} | "
            f"{fonte.get('status', ''):<16} | "
            f"{fonte.get('tipo', ''):<22} | "
            f"{fonte.get('dominio', '')}"
        )