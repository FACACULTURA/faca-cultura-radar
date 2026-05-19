# processamento/normalizador_feed.py
"""
F.CULT — normalizador_feed.py

Transforma item bruto/semântico em card final para o app:
- título limpo
- resumo curto
- fonte preenchida
- prazo/data
- categoria final
- descarte de anexos, atas, formulários e ruído estrutural
"""

import re
from urllib.parse import urlparse, unquote


MESES_EN = {
    "january": "01",
    "february": "02",
    "march": "03",
    "april": "04",
    "may": "05",
    "june": "06",
    "july": "07",
    "august": "08",
    "september": "09",
    "october": "10",
    "november": "11",
    "december": "12",
}

TRADUCOES_SIMPLES = {
    "deadline": "prazo",
    "apply": "inscrição",
    "applications open": "inscrições abertas",
    "open call": "chamada aberta",
    "call for entries": "chamada para inscrições",
    "call for proposals": "chamada para projetos",
    "submission": "inscrição",
    "submissions": "inscrições",
    "market": "mercado",
    "film festival": "festival de cinema",
    "film": "filme",
    "funding": "financiamento",
    "grant": "fomento",
    "program": "programa",
    "read more": "",
}


def _txt(valor):
    return str(valor or "").strip()


def limpar_espacos(texto):
    return re.sub(r"\s+", " ", _txt(texto)).strip()


def normalizar_lower(texto):
    return limpar_espacos(texto).lower()


def texto_total(item):
    partes = [
        item.get("titulo_principal"),
        item.get("titulo"),
        item.get("titulo_original"),
        item.get("resumo"),
        item.get("descricao_original"),
        item.get("tipo_item"),
        item.get("tipo"),
        item.get("classe"),
        item.get("link"),
        item.get("url"),
    ]
    return limpar_espacos(" ".join(_txt(p) for p in partes if p))


def extrair_dominio(url):
    try:
        host = urlparse(_txt(url)).netloc.replace("www.", "")
        return host or None
    except Exception:
        return None


def nome_fonte_por_link(url):
    host = extrair_dominio(url)

    if not host:
        return None

    mapa = {
        "secult.mg.gov.br": "SECULT-MG",
        "secult.es.gov.br": "SECULT-ES",
        "gov.br/cultura": "MinC",
        "gov.br/ancine": "ANCINE",
        "spcine.com.br": "SPCine",
        "riofilme.rio": "RioFilme",
        "telefilm.ca": "Telefilm Canada",
        "bogotamarket.com": "Bogotá Audiovisual Market",
        "filmfreeway.com": "FilmFreeway",
        "canadacouncil.ca": "Canada Council",
        "dohafilminstitute.com": "Doha Film Institute",
        "filmindependent.org": "Film Independent",
        "screenaustralia.gov.au": "Screen Australia",
        "nfvf.co.za": "NFVF",
    }

    full = _txt(url).lower()
    for chave, nome in mapa.items():
        if chave in full or chave in host:
            return nome

    return host


def detectar_pais_por_link(url, pais_original=None):
    if pais_original and pais_original not in ["Não identificado", "Nao identificado", ""]:
        return pais_original

    host = extrair_dominio(url) or ""

    if host.endswith(".br") or "gov.br" in host:
        return "Brasil"
    if host.endswith(".pt"):
        return "Portugal"
    if host.endswith(".es"):
        return "Espanha"
    if host.endswith(".fr"):
        return "França"
    if host.endswith(".it"):
        return "Itália"
    if host.endswith(".de"):
        return "Alemanha"
    if host.endswith(".ca"):
        return "Canadá"
    if host.endswith(".co"):
        return "Colômbia"
    if host.endswith(".au") or ".gov.au" in host:
        return "Austrália"
    if host.endswith(".za"):
        return "África do Sul"

    return pais_original or "Não identificado"


def extrair_data(texto):
    texto = _txt(texto)

    padroes = [
        r"\b\d{1,2}/\d{1,2}/\d{4}\b",
        r"\b\d{4}-\d{2}-\d{2}\b",
        r"\b\d{1,2}\.\d{1,2}\.\d{4}\b",
    ]

    for padrao in padroes:
        m = re.search(padrao, texto)
        if m:
            return m.group(0)

    m = re.search(
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),\s*(\d{4})\b",
        texto,
        flags=re.IGNORECASE,
    )
    if m:
        mes = MESES_EN.get(m.group(1).lower())
        dia = m.group(2).zfill(2)
        ano = m.group(3)
        return f"{dia}/{mes}/{ano}"

    return None


def eh_lixo_estrutural(texto, link=""):
    base = normalizar_lower(f"{texto} {link}")

    lixos_fortes = [
        "termos de uso",
        "terms of use",
        "privacy",
        "política de privacidade",
        "politica de privacidade",
        "cookies",
        "anexo",
        "formulário de recurso",
        "formulario de recurso",
        "interposição de recurso",
        "interposicao de recurso",
        "lista de inscritos",
        "ata comissão",
        "ata comissao",
        "ata de julgamento",
        "resultado final",
        "homologação",
        "homologacao",
        "designação da comissão",
        "designacao da comissao",
        "autodeclaração",
        "autodeclaracao",
        "planilha de custos",
        "termo de execução",
        "termo de execucao",
        "declaração de representação",
        "declaracao de representacao",
        "formulário do projeto",
        "formulario do projeto",
        "ficha de inscrição",
        "ficha de inscricao",
        "vídeos tutoriais",
        "videos tutoriais",
    ]

    extensoes_ruins = [
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ods",
    ]

    return any(p in base for p in lixos_fortes) or any(p in base for p in extensoes_ruins)


def classificar_categoria_final(item):
    texto = normalizar_lower(texto_total(item))
    link = normalizar_lower(item.get("link") or item.get("url") or "")

    if eh_lixo_estrutural(texto, link):
        return "descartar"

    if any(p in texto for p in [
        "licitação audiovisual",
        "licitacao audiovisual",
        "produção audiovisual",
        "producao audiovisual",
        "serviço audiovisual",
        "servico audiovisual",
        "filmagem",
        "vídeo institucional",
        "video institucional",
    ]) and any(p in texto for p in ["pregão", "pregao", "licitação", "licitacao", "contratação", "contratacao"]):
        return "licitacoes"

    if any(p in texto for p in [
        "edital ",
        "editais ",
        "chamada pública",
        "chamada publica",
        "chamamento público",
        "chamamento publico",
        "seleção pública",
        "selecao publica",
        "pnab",
        "lei paulo gustavo",
        "lpg",
        "lei rouanet",
    ]):
        return "editais"

    if any(p in texto for p in [
        "deadline",
        "open call",
        "call for entries",
        "call for proposals",
        "applications open",
        "submissions open",
        "apply",
        "inscrições abertas",
        "inscricoes abertas",
        "convocatória",
        "convocatoria",
        "market",
        "film festival",
        "festival 2026",
        "lab",
        "residency",
        "fellowship",
        "grant",
        "funding",
        "pitch",
        "mentoria",
        "laboratório",
        "laboratorio",
        "mercado audiovisual",
    ]):
        return "oportunidades"

    if any(p in texto for p in [
        "notícia",
        "noticia",
        "news",
        "lança",
        "lanca",
        "anuncia",
        "divulga",
        "publica",
        "abre inscrições",
        "abre inscricoes",
    ]):
        return "noticias"

    return "descartar"


def limpar_titulo_base(titulo):
    titulo = unquote(_txt(titulo))
    titulo = limpar_espacos(titulo)

    cortes = [
        "Read more",
        "read more",
        "Clique aqui",
        "clique aqui",
        "Saiba mais",
        "saiba mais",
        "Baixar",
        "baixar",
    ]

    for c in cortes:
        titulo = titulo.replace(c, "")

    return re.sub(r"\s+", " ", titulo).strip(" -–—|:;,.")


def titulo_por_link(link):
    link = _txt(link)
    if not link:
        return ""

    path = urlparse(link).path
    nome = path.split("/")[-1]
    nome = unquote(nome)
    nome = re.sub(r"\.(pdf|docx?|xlsx?|ods)$", "", nome, flags=re.I)
    nome = nome.replace("-", " ").replace("_", " ")
    return limpar_espacos(nome)


def gerar_titulo_semantico(item, categoria):
    bruto = (
        item.get("titulo_principal")
        or item.get("titulo")
        or item.get("titulo_original")
        or item.get("resumo")
        or ""
    )

    titulo = limpar_titulo_base(bruto)
    texto = limpar_espacos(texto_total(item))
    link = item.get("link") or item.get("url") or ""

    m = re.search(
        r"([A-ZÁÉÍÓÚÂÊÔÃÕÇ][^\.]{8,120}?(?:2025|2026|2027))\s+Deadline",
        texto,
        flags=re.I,
    )
    if m:
        titulo = limpar_titulo_base(m.group(1))

    if categoria == "editais":
        m = re.search(r"(Edital[^\.|]{5,140})", texto, flags=re.I)
        if m:
            titulo = limpar_titulo_base(m.group(1))
        elif "edital" in normalizar_lower(link):
            titulo_link = titulo_por_link(link)
            if titulo_link:
                titulo = titulo_link

    if categoria == "oportunidades":
        for padrao in [
            r"([A-Z][A-Za-zÀ-ÿ0-9\s\-\|:]+(?:Market|Festival|Lab|Forum|Fund|Grant|Residency|Fellowship)[A-Za-zÀ-ÿ0-9\s\-\|:]*\d{4})",
            r"([A-Z][A-Za-zÀ-ÿ0-9\s\-\|:]+(?:2025|2026|2027))",
        ]:
            m = re.search(padrao, texto)
            if m:
                titulo = limpar_titulo_base(m.group(1))
                break

    titulo = limpar_espacos(titulo)

    if eh_lixo_estrutural(titulo, link):
        return None

    if len(titulo) < 8:
        return None

    if len(titulo) > 115:
        titulo = titulo[:112].rstrip() + "..."

    return titulo


def traduzir_basico(texto):
    texto = _txt(texto)

    for origem, destino in TRADUCOES_SIMPLES.items():
        texto = re.sub(origem, destino, texto, flags=re.I)

    return limpar_espacos(texto)


def gerar_resumo_semantico(item, categoria, titulo, prazo=None):
    resumo = (
        item.get("resumo")
        or item.get("descricao_original")
        or item.get("titulo_original")
        or item.get("titulo")
        or ""
    )

    resumo = traduzir_basico(resumo)
    resumo = limpar_titulo_base(resumo)

    fonte = item.get("fonte") or item.get("instituicao") or nome_fonte_por_link(item.get("link") or item.get("url") or "")

    if categoria == "editais":
        base = f"Edital ou chamada pública identificada em {fonte or 'fonte institucional'}."
    elif categoria == "oportunidades":
        base = f"Oportunidade audiovisual/cultural identificada em {fonte or 'fonte monitorada'}."
    elif categoria == "licitacoes":
        base = "Possível licitação ou contratação relacionada ao audiovisual."
    else:
        base = "Informação relevante do setor cultural/audiovisual."

    if prazo:
        base += f" Prazo identificado: {prazo}."

    resumo_limpo = resumo
    if len(resumo_limpo) < 40 or eh_lixo_estrutural(resumo_limpo, item.get("link") or item.get("url") or ""):
        resumo_limpo = base

    if len(resumo_limpo) > 220:
        resumo_limpo = resumo_limpo[:217].rstrip() + "..."

    return resumo_limpo


def normalizar_item_feed(item):
    """
    Retorna item pronto para o app ou None se deve sair do feed.
    """

    link = item.get("link") or item.get("url") or item.get("origem") or ""
    texto = texto_total(item)

    categoria = classificar_categoria_final(item)

    if categoria == "descartar":
        return None

    titulo = gerar_titulo_semantico(item, categoria)

    if not titulo:
        return None

    prazo = item.get("prazo") or item.get("deadline") or extrair_data(texto)

    fonte = (
        item.get("fonte")
        or item.get("instituicao")
        or item.get("fonte_origem")
        or nome_fonte_por_link(link)
        or "Fonte não informada"
    )

    pais = detectar_pais_por_link(link, item.get("pais"))

    resumo = gerar_resumo_semantico(item, categoria, titulo, prazo)

    tipo = {
        "editais": "edital",
        "oportunidades": "oportunidade",
        "noticias": "noticia",
        "licitacoes": "licitacao",
    }.get(categoria, "oportunidade")

    return {
        "id": item.get("id") or f"{link}-{titulo}",
        "titulo_principal": titulo,
        "titulo": titulo,
        "resumo": resumo,
        "tipo_item": tipo,
        "tipo": tipo,
        "classe": tipo,
        "categoria_feed": categoria,
        "fonte": fonte,
        "instituicao": fonte,
        "cidade": item.get("cidade"),
        "estado": item.get("estado"),
        "pais": pais,
        "prazo": prazo,
        "deadline": prazo,
        "published_at": item.get("published_at") or item.get("data_publicacao"),
        "link": link,
        "link_edital": item.get("link_edital") or link,
        "link_inscricao": item.get("link_inscricao"),
        "score": item.get("score_final") or item.get("score_peneira") or item.get("score") or 50,
        "tags": item.get("tags") or [],
        "titulo_original": item.get("titulo_original") or item.get("titulo"),
        "descricao_original": item.get("descricao_original") or item.get("resumo"),
    }
