# =========================================================
# F.CULT — FILTRO AUDIOVISUAL
#
# Objetivo:
# impedir que o pipeline investigue páginas
# sem relação real com audiovisual.
#
# Esse filtro deve rodar LOGO NO INÍCIO do motor.
# Antes de:
# - score
# - enriquecimento
# - diversidade
# - contexto editorial
#
# =========================================================

import re


TERMOS_AUDIOVISUAIS = [

    # núcleo audiovisual
    "audiovisual",
    "cinema",
    "filme",
    "filmes",
    "film",
    "movie",
    "tv",
    "televisão",
    "televisao",
    "streaming",

    # formatos
    "documentário",
    "documentario",
    "série",
    "serie",
    "curta",
    "curta-metragem",
    "longa",
    "longa-metragem",
    "animação",
    "animacao",
    "videoclipe",
    "videoarte",

    # mercado
    "festival",
    "mostra",
    "pitching",
    "coprodução",
    "coproducao",
    "film commission",
    "mercado audiovisual",
    "rodada de negócios",
    "rodada de negocios",

    # criação
    "roteiro",
    "roteirista",
    "direção",
    "direcao",
    "produção audiovisual",
    "producao audiovisual",

    # plataformas / ecossistema
    "netflix",
    "prime video",
    "disney",
    "hbo",
    "ancine",
    "spcine",

    # técnicos
    "vfx",
    "motion",
    "fotografia",
    "sound design",
    "montagem",
    "edição",
    "edicao",

    # games e convergência
    "games",
    "game audiovisual",
]


TERMOS_FORTES = [

    "edital audiovisual",
    "festival de cinema",
    "produção audiovisual",
    "producao audiovisual",
    "film commission",
    "mercado audiovisual",
]

FONTES_ESTRATEGICAS = [

    "spcine",
    "ancine",
    "MinC",
    "Secult-MG",
    "secult",
    "ministério do turismo",
    "fundação municipal de cultura",
    "secretaria estadual de cultura",
    "film commission",
    "netflix",
    "hbo"
    "prime video",
    "disney plus",
    "telefilm",
    "berlinale",
    "sundance",
    "european commission",
    "canada council",
    "durban film office",
]

def limpar_texto(txt):

    if not txt:
        return ""

    txt = str(txt).lower()

    txt = re.sub(r"https?://\S+", " ", txt)
    txt = re.sub(r"[^\wÀ-ÿ]+", " ", txt)
    txt = re.sub(r"\s+", " ", txt)

    return txt.strip()


def texto_audiovisual(item):

    partes = [

        item.get("titulo"),
        item.get("resumo"),
        item.get("descricao"),
        item.get("texto_pagina"),
        item.get("texto_semantico_regional"),
        item.get("page_title"),
        item.get("titulo_principal"),
        item.get("titulo_semantico"),
        item.get("origem"),
        item.get("fonte"),
    ]

    texto = " ".join([
        str(p)
        for p in partes
        if p
    ])

    return limpar_texto(texto)


def contar_termos_audiovisuais(texto):

    encontrados = []

    for termo in TERMOS_AUDIOVISUAIS:

        if termo in texto:
            encontrados.append(termo)

    return len(set(encontrados)), encontrados


def tem_contexto_audiovisual(item):

    texto = texto_audiovisual(item)

    qtd, encontrados = contar_termos_audiovisuais(texto)

    # termos extremamente fortes
    if any(t in texto for t in TERMOS_FORTES):
        return True

    # cobertura mínima
    if qtd >= 2:
        return True

    # combinação estratégica
    if (
        ("cinema" in texto or "audiovisual" in texto)
        and
        ("edital" in texto or "festival" in texto or "inscrição" in texto)
    ):
        return True

    if any(t in texto for t in FONTES_ESTRATEGICAS):
        return True

    return False


def filtrar_audiovisual(itens):

    aprovados = []
    descartados = []

    for item in itens:

        if tem_contexto_audiovisual(item):

            item["contexto_audiovisual"] = True
            aprovados.append(item)

        else:

            item["contexto_audiovisual"] = False
            item["motivo_descarte"] = "sem_contexto_audiovisual"

            descartados.append(item)

    return aprovados