# processamento/extrator_semantico_v2.py

import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalizar_texto(valor: Any) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()


def texto_lower(valor: Any) -> str:
    return normalizar_texto(valor).lower()


def juntar_textos(item: Dict[str, Any]) -> str:
    partes = [
        item.get("titulo", ""),
        item.get("titulo_principal", ""),
        item.get("titulo_original", ""),
        item.get("titulo_pagina", ""),
        item.get("page_title", ""),
        item.get("descricao", ""),
        item.get("descricao_original", ""),
        item.get("conteudo", ""),
        item.get("texto", ""),
        item.get("texto_pagina", ""),
        item.get("resumo", ""),
        item.get("resumo_pagina", ""),
        item.get("breadcrumbs", ""),
        item.get("link", ""),
        item.get("url", ""),
    ]
    return normalizar_texto(" ".join(str(p or "") for p in partes))


# ============================================================
# DATAS
# ============================================================

MESES_PT = {
    "janeiro": "01",
    "fevereiro": "02",
    "março": "03",
    "marco": "03",
    "abril": "04",
    "maio": "05",
    "junho": "06",
    "julho": "07",
    "agosto": "08",
    "setembro": "09",
    "outubro": "10",
    "novembro": "11",
    "dezembro": "12",
}

MESES_EN = {
    "january": "01",
    "jan": "01",
    "february": "02",
    "feb": "02",
    "march": "03",
    "mar": "03",
    "april": "04",
    "apr": "04",
    "may": "05",
    "june": "06",
    "jun": "06",
    "july": "07",
    "jul": "07",
    "august": "08",
    "aug": "08",
    "september": "09",
    "sep": "09",
    "sept": "09",
    "october": "10",
    "oct": "10",
    "november": "11",
    "nov": "11",
    "december": "12",
    "dec": "12",
}


def normalizar_ano(ano: str) -> str:
    ano = str(ano or "").strip()
    if len(ano) == 2:
        return "20" + ano
    return ano


def data_iso_para_br(data: str) -> Optional[str]:
    data = normalizar_texto(data)

    if re.match(r"^\d{4}-\d{2}-\d{2}$", data):
        ano, mes, dia = data.split("-")
        return f"{dia}/{mes}/{ano}"

    return None


def extrair_data_texto(texto: str) -> Optional[str]:
    texto = normalizar_texto(texto)

    if not texto:
        return None

    # yyyy-mm-dd
    match = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", texto)
    if match:
        ano, mes, dia = match.groups()
        return f"{dia}/{mes}/{ano}"

    # dd/mm/yyyy ou dd-mm-yyyy
    match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", texto)
    if match:
        dia, mes, ano = match.groups()
        return f"{dia.zfill(2)}/{mes.zfill(2)}/{normalizar_ano(ano)}"

    # 21 de novembro de 2024
    match = re.search(
        r"\b(\d{1,2})\s+de\s+([A-Za-zÀ-ÿ]+)\s+de\s+(20\d{2})\b",
        texto,
        flags=re.I,
    )
    if match:
        dia, mes_nome, ano = match.groups()
        mes = MESES_PT.get(mes_nome.lower())
        if mes:
            return f"{dia.zfill(2)}/{mes}/{ano}"

    # October 28, 2025
    match = re.search(
        r"\b([A-Za-z]+)\s+(\d{1,2}),\s*(20\d{2})\b",
        texto,
        flags=re.I,
    )
    if match:
        mes_nome, dia, ano = match.groups()
        mes = MESES_EN.get(mes_nome.lower())
        if mes:
            return f"{dia.zfill(2)}/{mes}/{ano}"

    # 28 October 2025
    match = re.search(
        r"\b(\d{1,2})\s+([A-Za-z]+)\s+(20\d{2})\b",
        texto,
        flags=re.I,
    )
    if match:
        dia, mes_nome, ano = match.groups()
        mes = MESES_EN.get(mes_nome.lower())
        if mes:
            return f"{dia.zfill(2)}/{mes}/{ano}"

    return None


def extrair_prazo(item: Dict[str, Any]) -> Optional[str]:
    candidatos = [
        item.get("prazo"),
        item.get("deadline"),
        item.get("prazo_final"),
        item.get("titulo"),
        item.get("titulo_original"),
        item.get("titulo_principal"),
        item.get("titulo_pagina"),
        item.get("page_title"),
        item.get("descricao"),
        item.get("conteudo"),
        item.get("texto_pagina"),
        item.get("resumo_pagina"),
        item.get("resumo"),
    ]

    for candidato in candidatos:
        texto = normalizar_texto(candidato)

        if not texto:
            continue

        iso = data_iso_para_br(texto)
        if iso:
            return iso

        # Deadline: May 6, 2026
        match = re.search(
            r"(deadline|prazo|inscrições até|inscricoes ate|applications close|applications deadline)[:\s]*(.*?)(?:\.|$)",
            texto,
            flags=re.I,
        )
        if match:
            data = extrair_data_texto(match.group(2))
            if data:
                return data

        # Busca geral no texto
        data = extrair_data_texto(texto)
        if data:
            return data

    return None


def extrair_data_publicacao(item: Dict[str, Any]) -> Optional[str]:
    candidatos = [
        item.get("data_publicacao"),
        item.get("published_at"),
        item.get("titulo_pagina"),
        item.get("page_title"),
        item.get("texto_pagina"),
        item.get("resumo_pagina"),
    ]

    for candidato in candidatos:
        data = extrair_data_texto(normalizar_texto(candidato))
        if data:
            return data

    return None


# ============================================================
# TÍTULO
# ============================================================

PALAVRAS_TITULO_LIXO = [
    "ibid",
    "home",
    "menu",
    "close menu",
    "skip navigation",
    "skip to main content",
    "read more",
    "continuar lendo",
    "acesso ao site",
    "clique aqui",
    "saiba mais",
    "mais informações",
    "mais informacoes",
    "voltar",
    "baixar",
    "pdf",
    "untitled",
]


def limpar_titulo_basico(titulo: str) -> str:
    titulo = normalizar_texto(titulo)

    if not titulo:
        return ""

    titulo = re.sub(r"\s*\|\s*.+$", "", titulo).strip()
    titulo = re.sub(r"\s+[-–]\s+Blog.*$", "", titulo, flags=re.I).strip()
    titulo = re.sub(r"\s+[-–]\s+Home.*$", "", titulo, flags=re.I).strip()
    titulo = re.sub(r"\s+[-–]\s+Telefilm Canada.*$", "", titulo, flags=re.I).strip()
    titulo = re.sub(r"\s+[-–]\s+Governo.*$", "", titulo, flags=re.I).strip()
    titulo = re.sub(r"\s+—\s+.+$", "", titulo).strip()

    titulo = titulo.replace("_", " ")
    titulo = titulo.replace("%20", " ")
    titulo = re.sub(r"\.pdf$", "", titulo, flags=re.I).strip()
    titulo = re.sub(r"^pdf\s+", "", titulo, flags=re.I).strip()
    titulo = re.sub(r"^read more\s+", "", titulo, flags=re.I).strip()
    titulo = re.sub(r"\s+read more$", "", titulo, flags=re.I).strip()

    titulo = re.sub(r"\s{2,}", " ", titulo).strip()

    return titulo


def titulo_eh_lixo(titulo: str) -> bool:
    base = texto_lower(titulo)

    if not base:
        return True

    if len(base) < 6:
        return True

    if base.startswith("http"):
        return True

    if base.startswith("#"):
        return True

    if any(p in base for p in PALAVRAS_TITULO_LIXO):
        return True

    palavras = base.split()

    if len(palavras) >= 2 and len(set(palavras)) <= 2:
        return True

    if base in ["tag", "blog", "categoria", "noticias", "editais"]:
        return True

    return False


def recortar_titulo_inteligente(titulo: str) -> str:
    titulo = limpar_titulo_basico(titulo)

    # Padrões bons em inglês/português
    padroes = [
        r"(?:\d+(?:st|nd|rd|th)?\s+)?[A-Za-zÀ-ÿ\s]+Film Festival\s*\d{4}",
        r"[A-Za-zÀ-ÿ\s]+Audiovisual Market\s*[-–]?\s*[A-Za-z0-9\s]*\d{4}",
        r"[A-Za-zÀ-ÿ\s]+Fast Track\s*\d{4}",
        r"[A-Za-zÀ-ÿ\s]+Development Program\s*\d{4}",
        r"Edital\s*[nº°]?\s*\d+\/\d{4}[^.]{0,80}",
        r"Chamada Pública[^.]{0,90}",
        r"Chamada Publica[^.]{0,90}",
        r"Seleção de Projetos[^.]{0,90}",
        r"Selecao de Projetos[^.]{0,90}",
        r"Produção Audiovisual[^.]{0,90}",
        r"Producao Audiovisual[^.]{0,90}",
        r"Desenvolvimento de Projetos[^.]{0,90}",
        r"Inscrições abertas[^.]{0,90}",
        r"Inscricoes abertas[^.]{0,90}",
    ]

    for padrao in padroes:
        match = re.search(padrao, titulo, flags=re.I)
        if match:
            achado = limpar_titulo_basico(match.group(0))
            if not titulo_eh_lixo(achado):
                return " ".join(achado.split()[:10])

    palavras = titulo.split()

    if len(palavras) > 10:
        titulo = " ".join(palavras[:10])

    return titulo


def extrair_titulo_principal(item: Dict[str, Any]) -> str:
    candidatos = [
        item.get("h1"),
        item.get("titulo_pagina"),
        item.get("page_title"),
        item.get("titulo_principal"),
        item.get("titulo"),
        item.get("titulo_original"),
    ]

    for candidato in candidatos:
        titulo = recortar_titulo_inteligente(normalizar_texto(candidato))

        if not titulo_eh_lixo(titulo):
            return titulo[:1].upper() + titulo[1:]

    texto = normalizar_texto(item.get("texto_pagina") or item.get("resumo_pagina") or juntar_textos(item))

    frases = [f.strip() for f in re.split(r"[.!?]", texto) if f.strip()]

    for frase in frases:
        titulo = recortar_titulo_inteligente(frase)

        if not titulo_eh_lixo(titulo):
            return titulo[:1].upper() + titulo[1:]

    return "Sem título"


# ============================================================
# RESUMO
# ============================================================

BLOCOS_MENU = [
    "who we are",
    "about us",
    "board of directors",
    "executive leadership",
    "service charter",
    "strategic plan",
    "careers",
    "newsroom",
    "contact",
    "close menu",
    "learn more",
    "skip navigation",
    "home /",
    "ir para o conteúdo",
    "ir para o conteudo",
    "ir para o menu",
    "ir para a busca",
    "voltar ao topo",
    "contraste",
    "acessibilidade",
    "portal",
]


def limpar_resumo(texto: str) -> str:
    texto = normalizar_texto(texto)

    if not texto:
        return ""

    # Remove blocos evidentes de menu/nav
    partes = re.split(r"(?<=[.!?])\s+", texto)
    filtradas = []

    for frase in partes:
        base = frase.lower()

        if len(base) < 15:
            continue

        if any(bloco in base for bloco in BLOCOS_MENU):
            continue

        if base.count("menu") >= 2:
            continue

        if base.count("learn more") >= 1:
            continue

        filtradas.append(frase)

    if filtradas:
        texto = " ".join(filtradas)

    texto = re.sub(r"\s{2,}", " ", texto).strip()

    return texto


def gerar_resumo(item: Dict[str, Any]) -> str:
    candidatos = [
        item.get("resumo_pagina"),
        item.get("texto_pagina"),
        item.get("descricao"),
        item.get("conteudo"),
        item.get("resumo"),
        item.get("titulo_original"),
        item.get("titulo"),
    ]

    for candidato in candidatos:
        texto = limpar_resumo(normalizar_texto(candidato))

        if texto and len(texto) >= 40:
            return texto[:600].rstrip() + ("..." if len(texto) > 600 else "")

    return "Sem resumo disponível."


def traduzir_resumo(texto: str) -> str:
    """
    Placeholder seguro.
    Não traduz de verdade, apenas marca que precisa de tradução.
    Melhor do que inventar tradução incorreta.
    """
    if not texto:
        return texto

    base = texto.lower()

    sinais_ingles = [
        "deadline",
        "apply",
        "application",
        "film",
        "festival",
        "submission",
        "program",
        "market",
        "participants",
        "documentary",
    ]

    if any(s in base for s in sinais_ingles):
        return "[PT] " + texto

    return texto


# ============================================================
# INSTITUIÇÃO
# ============================================================

INSTITUICOES_FALSAS = [
    "festivals, activities and cinemas",
    "bolsas e apoios & awards",
    "read more",
    "home",
    "menu",
    "close menu",
    "acesso ao site",
    "reveja as imersões",
    "reveja as imersoes",
]


def instituicao_invalida(valor: Any) -> bool:
    texto = texto_lower(valor)

    if not texto:
        return True

    if texto in INSTITUICOES_FALSAS:
        return True

    if any(x in texto for x in INSTITUICOES_FALSAS):
        return True

    if len(texto) < 3:
        return True

    return False


def extrair_instituicao(item: Dict[str, Any]) -> Optional[str]:
    candidatos = [
        item.get("instituicao"),
        item.get("fonte"),
        item.get("dominio"),
        item.get("origem"),
        item.get("link"),
        item.get("url"),
    ]

    texto = juntar_textos(item).lower()

    mapeamento = {
        "telefilm.ca": "Telefilm Canada",
        "telefilm": "Telefilm Canada",
        "screen australia": "Screen Australia",
        "film independent": "Film Independent",
        "submittable.com": "Submittable",
        "secult.mg": "SECULT-MG",
        "secult.es": "SECULT-ES",
        "secult": "SECULT",
        "ancine": "ANCINE",
        "brde": "BRDE",
        "fsa": "Fundo Setorial do Audiovisual",
        "gov.br/cultura": "Ministério da Cultura",
        "cultura.gov.br": "Ministério da Cultura",
        "funarte": "Funarte",
        "spcine": "Spcine",
        "prosas": "Prosas",
        "benfeitoria": "Benfeitoria",
        "mapa cultural": "Mapa Cultural",
    }

    for chave, valor in mapeamento.items():
        if chave in texto:
            return valor

    for candidato in candidatos:
        valor = normalizar_texto(candidato)

        if not instituicao_invalida(valor):
            return valor

    return None


# ============================================================
# GEOGRAFIA
# ============================================================

def detectar_pais_por_url(url: str) -> Optional[str]:
    dominio = urlparse(url or "").netloc.lower()

    mapa = {
        ".gov.br": "Brasil",
        ".br": "Brasil",
        ".ca": "Canadá",
        ".au": "Austrália",
        ".co.uk": "Reino Unido",
        ".uk": "Reino Unido",
        ".us": "Estados Unidos",
        ".pt": "Portugal",
        ".fr": "França",
        ".de": "Alemanha",
        ".it": "Itália",
        ".es": "Espanha",
        ".mx": "México",
        ".ar": "Argentina",
        ".cl": "Chile",
        ".uy": "Uruguai",
        ".co": "Colômbia",
    }

    for sufixo, pais in sorted(mapa.items(), key=lambda x: len(x[0]), reverse=True):
        if dominio.endswith(sufixo):
            return pais

    return None


def extrair_geografia(item: Dict[str, Any]) -> Dict[str, Optional[str]]:
    texto = juntar_textos(item).lower()
    url = (item.get("link") or item.get("url") or "").lower()

    cidade = item.get("cidade")
    estado = item.get("estado")
    pais = item.get("pais")

    pais_url = detectar_pais_por_url(url)

    if not pais or pais == "Não identificado":
        pais = pais_url

    if ".gov.br" in url or "cultura.gov.br" in url:
        pais = "Brasil"

    if "secult.mg" in url or "minas gerais" in texto:
        estado = estado or "MG"
        pais = "Brasil"

    if "secult.es" in url or "espírito santo" in texto or "espirito santo" in texto:
        estado = estado or "ES"
        pais = "Brasil"

    if "cultura.sp.gov" in url or "spcine" in url:
        estado = estado or "SP"
        pais = "Brasil"

    if "cultura.rj.gov" in url or "rio de janeiro" in texto:
        estado = estado or "RJ"
        pais = "Brasil"

    # Só define São Paulo se realmente for fonte paulista
    eh_sp_real = (
        "spcine" in url
        or "prefeitura de são paulo" in texto
        or "prefeitura de sao paulo" in texto
        or "cultura.sp.gov" in url
    )

    if eh_sp_real:
        cidade = cidade or "São Paulo"
        estado = estado or "SP"
        pais = "Brasil"

    if not eh_sp_real and cidade == "São Paulo":
        cidade = None
        if estado == "SP":
            estado = None

    if pais and pais != "Brasil":
        cidade = None
        estado = None

    return {
        "cidade": cidade,
        "estado": estado,
        "pais": pais or "Não identificado",
    }


# ============================================================
# OFERTA / CONDIÇÃO / DOCUMENTOS
# ============================================================

def extrair_condicao(item: Dict[str, Any]) -> Optional[str]:
    texto = juntar_textos(item).lower()

    if any(p in texto for p in ["gratuito", "gratuita", "gratuitos", "gratuitas", "free"]):
        return "gratuito"

    if any(p in texto for p in ["pago", "pagamento", "taxa de inscrição", "application fee", "$", "€"]):
        return "pago"

    return item.get("condicao")


def extrair_oferta(item: Dict[str, Any]) -> List[str]:
    texto = juntar_textos(item).lower()
    ofertas: List[str] = []

    mapa = [
        ("curso", "curso"),
        ("workshop", "workshop"),
        ("oficina", "oficina"),
        ("seminário", "seminário"),
        ("seminario", "seminário"),
        ("webinar", "webinário"),
        ("webinário", "webinário"),
        ("laboratório", "laboratório"),
        ("laboratorio", "laboratório"),
        ("lab", "laboratório"),
        ("mentoria", "mentoria"),
        ("residência", "residência"),
        ("residency", "residência"),
        ("mercado", "mercado"),
        ("market", "mercado"),
        ("pitching", "pitching"),
        ("festival", "festival"),
        ("mostra", "mostra"),
        ("documentário", "documentário"),
        ("documentary", "documentário"),
        ("roteiro", "roteiro"),
        ("screenplay", "roteiro"),
        ("edital", "edital"),
        ("chamada", "chamada"),
    ]

    for chave, rotulo in mapa:
        if chave in texto and rotulo not in ofertas:
            ofertas.append(rotulo)

    return ofertas[:6]


def extrair_documentos_necessarios(item: Dict[str, Any]) -> List[str]:
    texto = juntar_textos(item).lower()
    docs: List[str] = []

    mapa = [
        ("cpf", "CPF"),
        ("rg", "RG"),
        ("currículo", "Currículo"),
        ("curriculo", "Currículo"),
        ("portfolio", "Portfólio"),
        ("portfólio", "Portfólio"),
        ("comprovante de residência", "Comprovante de residência"),
        ("roteiro", "Roteiro"),
        ("sinopse", "Sinopse"),
        ("projeto", "Projeto"),
        ("plano de trabalho", "Plano de trabalho"),
    ]

    for chave, rotulo in mapa:
        if chave in texto and rotulo not in docs:
            docs.append(rotulo)

    return docs


# ============================================================
# CLASSIFICAÇÃO INICIAL
# ============================================================

def classificar_tipo_item(item: Dict[str, Any]) -> str:
    texto = juntar_textos(item).lower()

    if any(t in texto for t in ["pregão", "pregao", "licitação", "licitacao", "termo de referência"]):
        return "licitacao"

    if any(t in texto for t in ["edital", "chamada pública", "chamada publica", "regulamento"]):
        return "edital"

    if any(t in texto for t in [
        "inscrições abertas",
        "inscricoes abertas",
        "applications open",
        "apply",
        "submit",
        "open call",
        "call for entries",
        "curso",
        "oficina",
        "festival",
        "laboratório",
        "lab",
        "programa",
    ]):
        return "oportunidade"

    return "noticia"


def gerar_tags(item: Dict[str, Any]) -> List[str]:
    tags: List[str] = []

    condicao = extrair_condicao(item)
    if condicao:
        tags.append(condicao)

    for oferta in extrair_oferta(item):
        if oferta not in tags:
            tags.append(oferta)

    instituicao = extrair_instituicao(item)
    if instituicao and instituicao not in tags:
        tags.append(instituicao)

    geo = extrair_geografia(item)

    for chave in ["estado", "pais"]:
        valor = geo.get(chave)
        if valor and valor != "Não identificado" and valor not in tags:
            tags.append(valor)

    escopo = "nacional" if geo.get("pais") == "Brasil" else "internacional"
    if escopo not in tags:
        tags.append(escopo)

    return tags[:6]


# ============================================================
# SINAIS
# ============================================================

def gerar_sinais_contexto(item: Dict[str, Any]) -> Dict[str, Any]:
    texto = juntar_textos(item).lower()

    tem_audiovisual = any(p in texto for p in [
        "audiovisual",
        "cinema",
        "film",
        "filme",
        "documentário",
        "documentary",
        "roteiro",
        "screenplay",
        "animation",
        "animação",
        "tv",
        "televisão",
        "festival",
        "mostra",
        "coprodução",
        "production",
        "produtor",
        "diretor",
        "feature film",
        "short film",
    ])

    tem_inscricao = any(p in texto for p in [
        "inscrição",
        "inscrições",
        "inscricao",
        "inscricoes",
        "apply",
        "application",
        "applications open",
        "submit",
        "submission",
        "submittable",
        "open call",
        "call for entries",
        "registration form",
    ])

    tem_prazo = bool(extrair_prazo(item)) or any(p in texto for p in [
        "deadline",
        "prazo",
        "applications close",
        "inscrições até",
        "inscricoes ate",
    ])

    tem_edital = any(p in texto for p in [
        "edital",
        "regulamento",
        "guidelines",
        "chamada pública",
        "chamada publica",
        "seleção pública",
        "selecao publica",
    ])

    tem_licitacao = any(p in texto for p in [
        "licitação",
        "licitacao",
        "pregão",
        "pregao",
        "termo de referência",
    ])

    score = item.get("score_enriquecimento") or item.get("score") or 0

    return {
        "tem_audiovisual": tem_audiovisual,
        "tem_inscricao": tem_inscricao,
        "tem_prazo": tem_prazo,
        "tem_edital": tem_edital,
        "tem_licitacao": tem_licitacao,
        "tem_valor": any(p in texto for p in ["$", "r$", "€", "grant", "funding", "fomento", "prêmio", "premio"]),
        "tem_selecao": any(p in texto for p in ["seleção", "selecao", "selected", "selecionados", "participants"]),
        "score_semantico": score,
    }


# ============================================================
# SAÍDA PRINCIPAL
# ============================================================

def extrair_item_semantico(item: Dict[str, Any]) -> Dict[str, Any]:
    geo = extrair_geografia(item)

    prazo = extrair_prazo(item)
    data_publicacao = extrair_data_publicacao(item)
    titulo = extrair_titulo_principal(item)
    resumo = gerar_resumo(item)
    instituicao = extrair_instituicao(item)

    resultado = dict(item)

    resultado.update({
        "titulo_principal": titulo,
        "tipo_item": item.get("tipo_item") or classificar_tipo_item(item),
        "prazo": prazo,
        "deadline": prazo or item.get("deadline"),
        "data_publicacao": data_publicacao or item.get("data_publicacao"),
        "published_at": data_publicacao or item.get("published_at"),
        "fonte": item.get("fonte") if not instituicao_invalida(item.get("fonte")) else instituicao,
        "instituicao": instituicao,
        "categoria": item.get("categoria") or None,
        "cidade": geo.get("cidade"),
        "estado": geo.get("estado"),
        "pais": geo.get("pais"),
        "condicao": extrair_condicao(item),
        "oferta": item.get("oferta") or extrair_oferta(item),
        "tags": gerar_tags(item),
        "resumo": traduzir_resumo(resumo),
        "documentos_necessarios": extrair_documentos_necessarios(item),
        "link": item.get("link") or item.get("url"),
        "titulo_original": item.get("titulo_original") or item.get("titulo"),
        "descricao_original": item.get("descricao_original") or item.get("descricao"),
        "origem": item.get("origem"),
        "classe": item.get("classe"),
    })

    sinais_existentes = item.get("sinais_contexto") or item.get("sinais_pagina") or {}
    sinais_novos = gerar_sinais_contexto(resultado)

    sinais_final = dict(sinais_novos)
    sinais_final.update(sinais_existentes)

    if prazo:
        sinais_final["tem_prazo"] = True

    if sinais_novos.get("tem_audiovisual"):
        sinais_final["tem_audiovisual"] = True

    if sinais_novos.get("tem_inscricao"):
        sinais_final["tem_inscricao"] = True

    if sinais_novos.get("tem_edital"):
        sinais_final["tem_edital"] = True

    resultado["sinais_contexto"] = sinais_final
    resultado["sinais_pagina"] = item.get("sinais_pagina") or sinais_final

    return resultado


def extrair_semantica_v2(item: Dict[str, Any]) -> Dict[str, Any]:
    return extrair_item_semantico(item)