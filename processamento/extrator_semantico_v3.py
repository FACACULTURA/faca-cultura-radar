import re
from typing import Any, Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse


def normalizar_texto(valor: Any) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()


def juntar_textos(item: Dict[str, Any]) -> str:
    partes = [
        item.get("titulo", ""),
        item.get("titulo_principal", ""),
        item.get("titulo_original", ""),
        item.get("descricao", ""),
        item.get("descricao_original", ""),
        item.get("conteudo", ""),
        item.get("texto", ""),
        item.get("texto_pagina", ""),
        item.get("resumo", ""),
        item.get("resumo_pagina", ""),
        item.get("titulo_pagina", ""),
        item.get("page_title", ""),
        item.get("breadcrumbs", ""),
        item.get("link", ""),
        item.get("url", ""),
    ]
    return normalizar_texto(" ".join(str(p or "") for p in partes))


def detectar_pais_por_url(url: str) -> Optional[str]:
    dominio = urlparse(url or "").netloc.lower()

    mapa = {
        ".gov.br": "Brasil",
        ".br": "Brasil",
        ".ca": "Canadá",
        ".au": "Austrália",
        ".co": "Colômbia",
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
    }

    for sufixo, pais in sorted(mapa.items(), key=lambda x: len(x[0]), reverse=True):
        if dominio.endswith(sufixo):
            return pais

    return None


def converter_data_en(data: str) -> Optional[str]:
    formatos = [
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
    ]

    for formato in formatos:
        try:
            return datetime.strptime(data.strip(), formato).strftime("%Y-%m-%d")
        except Exception:
            pass

    return None


def extrair_prazo(item: Dict[str, Any]) -> Optional[str]:
    candidatos = [
        normalizar_texto(item.get("prazo")),
        normalizar_texto(item.get("deadline")),
        normalizar_texto(item.get("prazo_final")),
        normalizar_texto(item.get("titulo")),
        normalizar_texto(item.get("titulo_original")),
        normalizar_texto(item.get("descricao")),
        normalizar_texto(item.get("conteudo")),
        normalizar_texto(item.get("texto_pagina")),
        normalizar_texto(item.get("resumo_pagina")),
        normalizar_texto(item.get("page_title")),
    ]

    for texto in candidatos:
        if not texto:
            continue

        match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", texto)
        if match:
            d, m, y = match.groups()
            if len(y) == 2:
                y = "20" + y
            return f"{d.zfill(2)}/{m.zfill(2)}/{y}"

        padroes_en = [
            r"deadline[:\s]*([A-Za-z]+\s\d{1,2},\s\d{4})",
            r"applications close.*?(\d{1,2}\s[A-Za-z]+\s\d{4})",
            r"applications close.*?([A-Za-z]+\s\d{1,2},\s\d{4})",
            r"closes?.*?(\d{1,2}\s[A-Za-z]+\s\d{4})",
            r"closes?.*?([A-Za-z]+\s\d{1,2},\s\d{4})",
        ]

        for padrao in padroes_en:
            match = re.search(padrao, texto, re.IGNORECASE)
            if match:
                data = converter_data_en(match.group(1))
                if data:
                    return data

    return None


def extrair_titulo_principal(item: Dict[str, Any]) -> str:
    candidatos = [
        item.get("titulo_pagina"),
        item.get("titulo_principal"),
        item.get("titulo"),
        item.get("page_title"),
        item.get("titulo_original"),
    ]

    for c in candidatos:
        titulo = normalizar_texto(c)
        if not titulo:
            continue

        titulo = titulo.lower()

        # 🔥 remove lixo comum
        cortes = [
            r"\|.*",  # remove | site
            r"-.*",   # remove - complemento
            r"home.*",
            r"about.*",
            r"menu.*",
            r"skip to.*",
        ]

        for corte in cortes:
            titulo = re.sub(corte, "", titulo, flags=re.I).strip()

        # 🔥 remove termos inúteis
        lixo = [
            "application process",
            "guidelines",
            "introduction",
            "overview",
            "information",
            "details",
            "program",
            "page",
        ]

        if any(l in titulo for l in lixo):
            continue

        palavras = titulo.split()

        # 🔥 mantém só até 6 palavras
        if 3 <= len(palavras) <= 12:
            titulo = " ".join(palavras[:6])
            return titulo.capitalize()

    # fallback inteligente
    texto = juntar_textos(item)
    if not texto:
        return "Sem título"

    frases = [f.strip() for f in re.split(r"[.!?]", texto) if f.strip()]

    for frase in frases:
        palavras = frase.split()
        if 5 <= len(palavras) <= 12:
            return " ".join(palavras[:6]).capitalize()

    return texto[:60].capitalize()


def extrair_instituicao(item: Dict[str, Any]) -> Optional[str]:
    if item.get("instituicao"):
        return item.get("instituicao")

    if item.get("fonte"):
        return item.get("fonte")

    texto = juntar_textos(item).lower()

    mapeamento = {
        "telefilm": "Telefilm Canada",
        "screen australia": "Screen Australia",
        "film independent": "Film Independent",
        "secult": "SECULT",
        "prefeitura de são paulo": "Prefeitura de São Paulo",
        "ancine": "Ancine",
        "funarte": "Funarte",
        "minc": "Ministério da Cultura",
        "ministério da cultura": "Ministério da Cultura",
        "sesc": "Sesc",
        "itaú cultural": "Itaú Cultural",
    }

    for chave, valor in mapeamento.items():
        if chave in texto:
            return valor

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

    eh_sp_real = (
        "spcine" in url
        or "prefeitura de são paulo" in texto
        or "prefeitura de sao paulo" in texto
    )

    if eh_sp_real:
        cidade = cidade or "São Paulo"
        estado = estado or "SP"
        pais = pais or "Brasil"

    if ".gov.br" in url or "secult" in url or "cultura.gov.br" in url:
        pais = "Brasil"

    if "secult.mg" in url or "minas gerais" in texto:
        estado = estado or "MG"
        pais = "Brasil"

    if "secult.es" in url or "espírito santo" in texto or "espirito santo" in texto:
        estado = estado or "ES"
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


def extrair_condicao(item: Dict[str, Any]) -> Optional[str]:
    texto = juntar_textos(item).lower()

    if any(p in texto for p in ["gratuito", "gratuita", "gratuitos", "gratuitas"]):
        return "gratuito"

    if any(p in texto for p in ["pago", "pagamento", "inscrição paga", "taxa de inscrição"]):
        return "pago"

    return item.get("condicao")


def extrair_oferta(item: Dict[str, Any]) -> List[str]:
    texto = juntar_textos(item).lower()
    ofertas: List[str] = []

    mapa = [
        ("curso", "curso"),
        ("oficina", "oficina"),
        ("formação", "formação"),
        ("laboratório", "laboratório"),
        ("laboratorio", "laboratório"),
        ("mentoria", "mentoria"),
        ("residência", "residência"),
        ("residencia", "residência"),
        ("mercado", "mercado"),
        ("pitching", "pitching"),
        ("coprodução", "coprodução"),
        ("co-production", "coprodução"),
        ("festival", "festival"),
        ("mostra", "mostra"),
        ("documentário", "documentário"),
        ("documentary", "documentário"),
        ("roteiro", "roteiro"),
    ]

    for chave, rotulo in mapa:
        if chave in texto and rotulo not in ofertas:
            ofertas.append(rotulo)

    return ofertas


def classificar_tipo_item(item: Dict[str, Any]) -> str:
    texto = juntar_textos(item).lower()

    if any(t in texto for t in ["pregão", "pregao", "licitação", "licitacao", "termo de referência"]):
        return "licitacao"

    if any(t in texto for t in ["edital", "chamada pública", "chamada publica", "regulamento"]):
        return "edital"

    if any(t in texto for t in ["inscrições abertas", "applications open", "apply", "open call", "curso", "oficina", "laboratório", "programa"]):
        return "oportunidade"

    return "noticia"


def gerar_resumo(item: Dict[str, Any]) -> str:
    texto = normalizar_texto(
        item.get("resumo_pagina")
        or item.get("texto_pagina")
        or item.get("descricao")
        or item.get("conteudo")
        or item.get("titulo")
    )

    if not texto:
        return "Sem resumo disponível."

    cortes = [
        r"CONTRASTE\s*\|\s*ACESSIBILIDADE.*",
        r"Skip to main content.*",
        r"Home\s*/\s*",
    ]

    for corte in cortes:
        texto = re.sub(corte, "", texto, flags=re.I).strip()

    return texto if len(texto) <= 600 else texto[:600].rstrip() + "..."


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
    for chave in ["cidade", "estado", "pais"]:
        valor = geo.get(chave)
        if valor and valor != "Não identificado" and valor not in tags:
            tags.append(valor)

    escopo = "nacional" if geo.get("pais") == "Brasil" else "internacional"
    if escopo not in tags:
        tags.append(escopo)

    return tags[:6]


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


def gerar_sinais_contexto(item: Dict[str, Any]) -> Dict[str, Any]:
    texto = juntar_textos(item).lower()

    tem_audiovisual = any(p in texto for p in [
        "audiovisual", "cinema", "film", "filme", "documentário",
        "documentary", "roteiro", "screenplay", "animation", "animação",
        "tv", "televisão", "festival", "mostra", "coprodução",
    ])

    tem_inscricao = any(p in texto for p in [
        "inscrição", "inscrições", "inscricao", "inscricoes",
        "apply", "application", "applications", "submit",
        "submittable", "open call", "call for entries",
    ])

    tem_prazo = bool(extrair_prazo(item)) or any(p in texto for p in [
        "deadline", "prazo", "applications close", "inscrições até",
    ])

    tem_edital = any(p in texto for p in [
        "edital", "regulamento", "guidelines", "chamada pública",
        "chamada publica",
    ])

    tem_licitacao = any(p in texto for p in [
        "licitação", "licitacao", "pregão", "pregao",
    ])

    return {
        "tem_audiovisual": tem_audiovisual,
        "tem_inscricao": tem_inscricao,
        "tem_prazo": tem_prazo,
        "tem_edital": tem_edital,
        "tem_licitacao": tem_licitacao,
        "tem_valor": any(p in texto for p in ["$", "r$", "grant", "funding", "fomento", "prêmio", "premio"]),
        "tem_selecao": any(p in texto for p in ["seleção", "selecao", "selected", "selecionados", "participants"]),
        "score_semantico": item.get("score_enriquecimento") or 0,
    }


def extrair_item_semantico(item: Dict[str, Any]) -> Dict[str, Any]:
    geo = extrair_geografia(item)
    prazo = extrair_prazo(item)

    resultado = dict(item)

    resultado.update({
        "titulo_principal": extrair_titulo_principal(item),
        "tipo_item": item.get("tipo_item") or classificar_tipo_item(item),
        "prazo": prazo,
        "deadline": item.get("deadline") or prazo,
        "fonte": item.get("fonte") or extrair_instituicao(item),
        "instituicao": extrair_instituicao(item),
        "categoria": item.get("categoria") or None,
        "cidade": geo.get("cidade"),
        "estado": geo.get("estado"),
        "pais": geo.get("pais"),
        "condicao": extrair_condicao(item),
        "oferta": item.get("oferta") or extrair_oferta(item),
        "tags": gerar_tags(item),
        "resumo": gerar_resumo(item),
        "documentos_necessarios": extrair_documentos_necessarios(item),
        "link": item.get("link") or item.get("url"),
        "titulo_original": item.get("titulo_original") or item.get("titulo"),
        "descricao_original": item.get("descricao_original") or item.get("descricao"),
        "origem": item.get("origem"),
        "classe": item.get("classe"),
    })

    sinais_existentes = item.get("sinais_contexto") or item.get("sinais_pagina") or {}
    sinais_novos = gerar_sinais_contexto(resultado)
    sinais_novos.update(sinais_existentes)

    if prazo:
        sinais_novos["tem_prazo"] = True

    resultado["sinais_contexto"] = sinais_novos
    resultado["sinais_pagina"] = item.get("sinais_pagina") or sinais_novos

    return resultado


def extrair_semantica_v2(item: Dict[str, Any]) -> Dict[str, Any]:
    return extrair_item_semantico(item)