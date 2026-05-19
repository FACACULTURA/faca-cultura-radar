# =========================================================
# F.CULT — PENEIRA DE DIVERSIDADE
# Remove repetição semântica sem matar fontes quentes.
#
# Regra central:
# - Se for quente e tiver boa semântica, pode passar.
# - O que não pode passar é repetição, anexo, ata, resultado duplicado
#   e variação do mesmo item ocupando o feed.
# =========================================================

import re
from urllib.parse import urlparse
from difflib import SequenceMatcher


CAMPOS_TITULO = [
    "titulo_principal",
    "titulo_semantico",
    "titulo",
    "titulo_pagina",
    "page_title",
]

CAMPOS_SCORE = [
    "score_semantico",
    "score_validacao",
    "score_enriquecimento",
    "score_fonte",
    "score",
]

TERMOS_QUENTES = [
    "edital",
    "chamada",
    "inscrição",
    "inscrições",
    "inscricoes",
    "seleção",
    "selecao",
    "fomento",
    "prêmio",
    "premio",
    "bolsa",
    "residência",
    "residencia",
    "laboratório",
    "laboratorio",
    "pitching",
    "mercado",
    "festival",
    "mostra",
    "audiovisual",
    "cinema",
    "filme",
    "documentário",
    "documentario",
    "animação",
    "animacao",
    "roteiro",
    "curta",
    "longa",
    "série",
    "serie",
    "tv",
    "licitação",
    "licitacao",
    "regulamento",
    "submissão",
    "submissao",
]

TERMOS_DERIVADOS = [
    "anexo",
    "ata",
    "resultado final",
    "resultado preliminar",
    "homologação",
    "homologacao",
    "lista de inscritos",
    "lista de habilitados",
    "lista de selecionados",
    "formulário",
    "formulario",
    "ficha de inscrição",
    "ficha de inscricao",
    "declaração",
    "declaracao",
    "minuta",
    "planilha",
    "recurso",
    "errata",
    "retificação",
    "retificacao",
    "termo de compromisso",
    "parecer",
]

STOPWORDS = {
    "de", "da", "do", "das", "dos", "e", "em", "no", "na", "nos", "nas",
    "para", "por", "com", "a", "o", "as", "os", "um", "uma", "ao", "à",
    "edital", "chamada", "publica", "pública", "inscricao", "inscrição",
    "resultado", "final", "preliminar", "anexo", "ata", "formulario",
    "formulário", "baixar", "conteudo", "conteúdo", "atualizacao",
    "atualização", "formato", "tamanho",
}


def limpar_texto(txt):
    if not txt:
        return ""

    txt = str(txt).lower()
    txt = re.sub(r"https?://\S+", " ", txt)
    txt = re.sub(r"[^\wÀ-ÿ]+", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()

    return txt


def obter_titulo(item):
    for campo in CAMPOS_TITULO:
        valor = item.get(campo)
        if valor:
            return str(valor).strip()
    return ""


def obter_url(item):
    return item.get("url") or item.get("link") or ""


def obter_dominio(item):
    url = obter_url(item)

    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def obter_score(item):
    scores = []

    for campo in CAMPOS_SCORE:
        valor = item.get(campo)
        try:
            if valor is not None:
                scores.append(float(valor))
        except Exception:
            pass

    if not scores:
        return 0

    return max(scores)


def texto_base(item):
    partes = [
        obter_titulo(item),
        item.get("resumo") or "",
        item.get("descricao") or "",
        item.get("texto_pagina") or "",
        item.get("texto_semantico_regional") or "",
        obter_url(item),
    ]

    return limpar_texto(" ".join(str(p) for p in partes if p))


def contar_semantica_quente(item):
    texto = texto_base(item)
    encontrados = [t for t in TERMOS_QUENTES if t in texto]
    return len(set(encontrados)), encontrados


def eh_derivado(item):

    texto = texto_base(item)
    titulo = limpar_texto(obter_titulo(item))
    url = limpar_texto(obter_url(item))

    TERMOS_ESTRATEGICOS = [

        "film commission",
        "spcine",
        "ancine",
        "audiovisual",
        "cinema",
        "festival",
        "streaming",
        "coprodução",
        "coproducao",
        "mercado audiovisual",
    ]

    if any(t in texto for t in TERMOS_ESTRATEGICOS):
        return False

    if item.get("eh_documento_derivado") is True:
        return True

    derivados_encontrados = [
        t for t in TERMOS_DERIVADOS
        if t in texto
    ]

    if len(derivados_encontrados) >= 2:
        return True

    if any(ext in url for ext in [" pdf", " doc", " docx", " xls", " xlsx"]):
        if len(derivados_encontrados) >= 1:
            return True

    return False


def assinatura_semantica(item):
    """
    Cria uma assinatura curta do assunto.
    Serve para detectar variações do mesmo edital/documento.
    """
    titulo = limpar_texto(obter_titulo(item))

    # remove numeração de anexos, atalhos e ruídos
    titulo = re.sub(r"\banexo\s+[ivxlcdm0-9]+\b", " ", titulo)
    titulo = re.sub(r"\bata\s+comissao\s+julgadora\b", " ", titulo)
    titulo = re.sub(r"\bresultado\s+(final|preliminar)\b", " ", titulo)
    titulo = re.sub(r"\bbaixar\b", " ", titulo)
    titulo = re.sub(r"\b\d{1,4}\b", " ", titulo)

    palavras = [
        p for p in titulo.split()
        if len(p) > 2 and p not in STOPWORDS
    ]

    palavras = palavras[:12]

    return " ".join(palavras)


def similaridade(a, b):
    if not a or not b:
        return 0
    return SequenceMatcher(None, a, b).ratio()


def item_quente(item):
    qtd, termos = contar_semantica_quente(item)
    score = obter_score(item)

    tem_edital = item.get("sinais_pagina", {}).get("tem_edital") is True
    tem_inscricao = item.get("sinais_pagina", {}).get("tem_inscricao") is True
    tem_audiovisual = item.get("sinais_pagina", {}).get("tem_audiovisual") is True
    tem_prazo = item.get("sinais_pagina", {}).get("tem_prazo") is True

    cobertura_semantica = qtd / max(len(TERMOS_QUENTES), 1)

    if score >= 150:
        return True

    if qtd >= 5:
        return True

    if tem_edital and (tem_inscricao or tem_prazo or tem_audiovisual):
        return True

    if cobertura_semantica >= 0.70:
        return True

    return False


def qualidade_item(item):
    score = obter_score(item)
    qtd_semantica, _ = contar_semantica_quente(item)

    qualidade = score + (qtd_semantica * 20)

    if item_quente(item):
        qualidade += 100

    if eh_derivado(item):

        qualidade -= 150

        titulo = limpar_texto(obter_titulo(item))

        termos_bloqueio = [
            "ata",
            "comissão julgadora",
            "comissao julgadora",
            "resultado preliminar",
            "resultado final",
            "homologação",
            "homologacao",
            "retificação",
            "retificacao",
            "anexo",
            "errata",
            "parecer",
            "lista de habilitados",
            "lista de selecionados",
            "resultado icms",
        ]

        if any(t in titulo for t in termos_bloqueio):
            qualidade -= 100

        titulo = obter_titulo(item)

        if len(titulo) > 160:
            qualidade -= 30

        if item.get("prazo") or item.get("deadline"):
            qualidade += 30

        if ".gov.br" in obter_url(item).lower():
            qualidade += 40

        return qualidade


def deduplicar_repetidos(itens):
    """
    Remove:
    - URLs repetidas
    - títulos muito parecidos
    - assinaturas semânticas repetidas
    Mantém sempre o item de maior qualidade.
    """
    escolhidos = []
    urls_vistas = set()
    assinaturas_por_dominio = {}

    ordenados = sorted(
        itens,
        key=lambda x: qualidade_item(x),
        reverse=True
    )

    for item in ordenados:
        url = obter_url(item).rstrip("/").lower()
        dominio = obter_dominio(item)
        assinatura = assinatura_semantica(item)

        if url and url in urls_vistas:
            item["motivo_peneira"] = "url_repetida"
            continue

        if dominio not in assinaturas_por_dominio:
            assinaturas_por_dominio[dominio] = []

        repetido = False

        for assinatura_existente in assinaturas_por_dominio[dominio]:
            if assinatura and assinatura == assinatura_existente:
                repetido = True
                break

            if similaridade(assinatura, assinatura_existente) >= 0.86:
                repetido = True
                break

        if repetido:
            item["motivo_peneira"] = "repeticao_semantica_mesma_fonte"
            continue

        if url:
            urls_vistas.add(url)

        if assinatura:
            assinaturas_por_dominio[dominio].append(assinatura)

        escolhidos.append(item)

    return escolhidos


def aplicar_limite_inteligente_por_fonte(itens):
    """
    Não corta fonte quente à toa.
    Só limita fonte fria/redundante.
    """
    grupos = {}

    for item in itens:
        dominio = obter_dominio(item) or "sem_dominio"
        grupos.setdefault(dominio, []).append(item)

    finais = []

    for dominio, lista in grupos.items():
        lista = sorted(lista, key=lambda x: qualidade_item(x), reverse=True)

        quentes = [i for i in lista if item_quente(i) and not eh_derivado(i)]
        mornos = [i for i in lista if not item_quente(i) and not eh_derivado(i)]
        derivados = [i for i in lista if eh_derivado(i)]

        # Quentes passam sem limite rígido, desde que já deduplicados.
        finais.extend(quentes)

        # Mornos passam pouco.
        limite_mornos = 3

        if ".gov.br" in dominio or "secult" in dominio or "cultura" in dominio:
            limite_mornos = 5

        finais.extend(mornos[:limite_mornos])

       # derivados não entram mais no feed principal
    pass

    return finais


def peneirar_diversidade(itens):
    """
    Entrada: lista de itens já coletados/semantizados/validados.
    Saída: lista limpa, sem repetição dominante.
    """
    if not itens:
        return []

    etapa_1 = deduplicar_repetidos(itens)
    etapa_2 = aplicar_limite_inteligente_por_fonte(etapa_1)

    etapa_2 = sorted(
        etapa_2,
        key=lambda x: qualidade_item(x),
        reverse=True
    )

    return etapa_2


# Alias possível para integração com motor/validador
def aplicar_peneira_diversidade(itens):
    return peneirar_diversidade(itens)