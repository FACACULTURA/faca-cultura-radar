# =========================================================
# F.CULT — CONTEXTO EDITORIAL
# Decide o destino real do item.
# =========================================================

import re


def texto_item(item):

    partes = [

        item.get("titulo"),
        item.get("resumo"),
        item.get("descricao"),
        item.get("texto_pagina"),
        item.get("titulo_principal"),
        item.get("titulo_semantico"),
    ]

    return " ".join([
        str(p).lower()
        for p in partes
        if p
    ])


def analisar_contexto_editorial(item):

    texto = texto_item(item)

    contexto = {

        "destino_principal": "noticias",
        "tags_destino": [],
        "relevancia_estrategica": 0,
    }

    # ==========================
    # LICITAÇÕES
    # ==========================
    termos_licitacao = [

        "licitação",
        "licitacao",
        "pregão",
        "pregao",
        "concorrência",
        "concorrencia",
        "contratação",
        "contratacao",
    ]

    if any(t in texto for t in termos_licitacao):

        contexto["destino_principal"] = "licitacoes"
        contexto["tags_destino"].append("compra_publica")
        contexto["relevancia_estrategica"] += 80

        return contexto

    # ==========================
    # EDITAIS
    # ==========================
    termos_edital = [

        "edital",
        "chamada pública",
        "chamada publica",
        "inscrição",
        "inscricao",
        "seleção",
        "selecao",
        "fomento",
        "laboratório",
        "laboratorio",
        "pitching",
        "bolsa",
        "residência",
        "residencia",
    ]

    if any(t in texto for t in termos_edital):

        contexto["destino_principal"] = "editais"
        contexto["tags_destino"].append("oportunidade")
        contexto["relevancia_estrategica"] += 100

        return contexto

    # ==========================
    # OPORTUNIDADES
    # ==========================
    termos_oportunidade = [

        "film commission",
        "coprodução",
        "coproducao",
        "mercado audiovisual",
        "rodada de negócios",
        "rodada de negocios",
        "networking",
        "aceleração",
        "aceleracao",
    ]

    if any(t in texto for t in termos_oportunidade):

        contexto["destino_principal"] = "oportunidades"
        contexto["tags_destino"].append("mercado")
        contexto["relevancia_estrategica"] += 90

        return contexto

    # ==========================
    # NOTÍCIAS
    # ==========================
    contexto["destino_principal"] = "noticias"

    return contexto