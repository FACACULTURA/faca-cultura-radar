# processamento/leitor_semantico.py

import re


ACOES = {
    "edital": [
        "selecionar",
        "seleção",
        "fomento",
        "premiação",
        "premiacao",
        "chamada pública",
        "chamada publica",
        "edital",
    ],

    "oportunidade": [
        "inscrições abertas",
        "inscricoes abertas",
        "festival",
        "mostra",
        "workshop",
        "laboratório",
        "laboratorio",
        "mercado",
        "pitching",
        "residência",
        "residencia",
        "curso",
    ],

    "licitacao": [
        "licitação",
        "licitacao",
        "pregão",
        "pregao",
        "contratação",
        "contratacao",
        "termo de referência",
    ],

    "resultado": [
        "resultado final",
        "resultado preliminar",
        "lista de selecionados",
        "homologação",
        "habilitados",
    ],
}


OBJETOS = [
    "documentário",
    "documentario",
    "série",
    "serie",
    "tv",
    "televisão",
    "televisao",
    "cinema",
    "audiovisual",
    "vídeo institucional",
    "video institucional",
    "animação",
    "animacao",
    "curta",
    "longa",
    "festival",
    "obra audiovisual",
]


def limpar(txt):
    return re.sub(r"\s+", " ", str(txt or "")).strip().lower()


def detectar_intencao(texto):
    texto = limpar(texto)

    scores = {}

    for tipo, termos in ACOES.items():
        pontos = 0

        for termo in termos:
            if termo in texto:
                pontos += 1

        scores[tipo] = pontos

    if not scores:
        return "indefinido"

    vencedor = max(scores, key=scores.get)

    if scores[vencedor] == 0:
        return "indefinido"

    return vencedor


def detectar_objeto(texto):
    texto = limpar(texto)

    encontrados = []

    for obj in OBJETOS:
        if obj in texto:
            encontrados.append(obj)

    return encontrados[:3]


def gerar_titulo_semantico(texto):
    texto = limpar(texto)

    intencao = detectar_intencao(texto)
    objetos = detectar_objeto(texto)

    principal = objetos[0] if objetos else ""

    MAPA = {
        "edital": "Edital de",
        "oportunidade": "",
        "licitacao": "Licitação de",
        "resultado": "Resultado de",
    }

    prefixo = MAPA.get(intencao, "")

    titulo = f"{prefixo} {principal}".strip()

    titulo = re.sub(r"\s+", " ", titulo)

    return titulo[:80]


def ler_item_semantico(item):
    texto = " ".join([
        str(item.get("titulo") or ""),
        str(item.get("titulo_pagina") or ""),
        str(item.get("texto_pagina") or ""),
        str(item.get("resumo") or ""),
    ])

    intencao = detectar_intencao(texto)
    objetos = detectar_objeto(texto)

    return {
        "tipo_contexto": intencao,
        "objetos_detectados": objetos,
        "titulo_semantico": gerar_titulo_semantico(texto),
    }