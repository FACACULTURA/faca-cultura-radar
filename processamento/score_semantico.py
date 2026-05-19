# =========================================================
# F.CULT — SCORE SEMÂNTICO CONTEXTUAL
# =========================================================

import re
from datetime import datetime


ANO_ATUAL = datetime.now().year


# =========================================================
# TERMOS
# =========================================================

TERMOS_ULTRA_QUENTES = [
    "inscrições abertas",
    "inscricoes abertas",
    "submissões abertas",
    "submit now",
    "apply now",
    "deadline",
    "prazo final",
    "últimos dias",
    "ultimos dias",
]

TERMOS_EDITAL_FORTE = [
    "edital",
    "chamada pública",
    "convocatória",
    "residência",
    "laboratório",
    "pitching",
    "rodada de negócios",
    "seleção",
    "bolsa",
    "programa de aceleração",
]

TERMOS_AUDIOVISUAL = [
    "audiovisual",
    "cinema",
    "filme",
    "curta",
    "longa",
    "documentário",
    "documentario",
    "série",
    "serie",
    "animação",
    "animacao",
    "roteiro",
]

TERMOS_RESULTADO = [
    "resultado final",
    "resultado preliminar",
    "homologação",
    "homologacao",
    "ata",
    "ata comissão",
    "convocação",
    "convocacao",
    "habilitados",
    "inabilitados",
    "selecionados",
]

TERMOS_NOTICIA_FRIA = [
    "governador",
    "evento",
    "seminário",
    "seminario",
    "reunião",
    "reuniao",
    "visita",
    "turismo",
    "exposição",
    "exposicao",
]

TERMOS_RUIDO = [
    "read more",
    "saiba mais",
    "clique aqui",
    "tags:",
    "copyright",
    "todos os direitos reservados",
]


# =========================================================
# HELPERS
# =========================================================

def normalizar(txt):
    return str(txt or "").lower().strip()


def contem(texto, lista):
    texto = normalizar(texto)

    for termo in lista:
        if termo in texto:
            return True

    return False


def extrair_ano(texto):
    anos = re.findall(r"(20\d{2})", str(texto))

    if anos:
        try:
            return int(anos[0])
        except:
            return None

    return None


# =========================================================
# SCORE PRINCIPAL
# =========================================================

def calcular_score_semantico(item):

    texto = " ".join([
        str(item.get("titulo") or ""),
        str(item.get("titulo_principal") or ""),
        str(item.get("titulo_pagina") or ""),
        str(item.get("texto_pagina") or ""),
        str(item.get("resumo") or ""),
    ])

    texto = normalizar(texto)

    score = 0
    motivos = []

    sinais = item.get("sinais_pagina") or {}
    leitura = item.get("leitura_semantica") or {}

    tipo_contexto = leitura.get("tipo_contexto")


    # =====================================================
    # CONTEXTO SEMÂNTICO
    # =====================================================

    if tipo_contexto == "edital":
        score += 120
        motivos.append("contexto edital")

    elif tipo_contexto == "licitacao":
        score += 80
        motivos.append("contexto licitação")

    elif tipo_contexto == "resultado":
        score -= 180
        motivos.append("resultado derivado")

    elif tipo_contexto == "noticia":
        score -= 30
        motivos.append("notícia genérica")


    # =====================================================
    # INSCRIÇÃO
    # =====================================================

    if sinais.get("tem_inscricao"):
        score += 180
        motivos.append("tem inscrição")

    if item.get("link_inscricao"):
        score += 220
        motivos.append("link inscrição")

    if contem(texto, TERMOS_ULTRA_QUENTES):
        score += 150
        motivos.append("urgência ativa")


    # =====================================================
    # EDITAL
    # =====================================================

    if sinais.get("tem_edital"):
        score += 80
        motivos.append("tem edital")

    if contem(texto, TERMOS_EDITAL_FORTE):
        score += 60
        motivos.append("termos edital forte")


    # =====================================================
    # AUDIOVISUAL
    # =====================================================

    if sinais.get("tem_audiovisual"):
        score += 100
        motivos.append("audiovisual")

    if contem(texto, TERMOS_AUDIOVISUAL):
        score += 80
        motivos.append("termos audiovisual")


    # =====================================================
    # PRAZO
    # =====================================================

    if sinais.get("tem_prazo"):
        score += 70
        motivos.append("tem prazo")

    if item.get("deadline"):
        score += 60
        motivos.append("deadline")

    if item.get("prazo"):
        score += 40
        motivos.append("prazo explícito")


    # =====================================================
    # PDF
    # =====================================================

    link = normalizar(item.get("link"))

    if ".pdf" in link:
        score += 45
        motivos.append("pdf")

    if item.get("link_edital"):
        score += 100
        motivos.append("link edital")


    # =====================================================
    # RESULTADO / DERIVADO
    # =====================================================

    if contem(texto, TERMOS_RESULTADO):
        score -= 220
        motivos.append("resultado/homologação")

    if "ata" in texto:
        score -= 250
        motivos.append("ata")

    if "homologação" in texto or "homologacao" in texto:
        score -= 250
        motivos.append("homologação")

    if "resultado final" in texto:
        score -= 300
        motivos.append("resultado final")


    # =====================================================
    # NOTÍCIA FRIA
    # =====================================================

    if contem(texto, TERMOS_NOTICIA_FRIA):
        score -= 90
        motivos.append("notícia fria")


    # =====================================================
    # RUÍDO
    # =====================================================

    if contem(texto, TERMOS_RUIDO):
        score -= 40
        motivos.append("ruído estrutural")


   # =====================================================
# ANO
# =====================================================

    ano_detectado = (
        item.get("ano")
        or extrair_ano(texto)
    )

    try:

        if ano_detectado is not None:

            ano_float = float(ano_detectado)

            if str(ano_float).lower() != "nan":

                ano_detectado = int(ano_float)

                diferenca = ANO_ATUAL - ano_detectado

                if diferenca >= 5:
                    score -= 250
                    motivos.append("muito antigo")

                elif diferenca >= 3:
                    score -= 150
                    motivos.append("antigo")

                elif diferenca >= 2:
                    score -= 80
                    motivos.append("desatualizado")

    except:
        pass

    # =====================================================
    # SCORE FONTE
    # =====================================================

    score += item.get("score_fonte", 0)


    # =====================================================
    # BONUS
    # =====================================================

    if (
        sinais.get("tem_edital")
        and sinais.get("tem_inscricao")
        and sinais.get("tem_prazo")
    ):
        score += 180
        motivos.append("combo edital real")


    # =====================================================
    # FINAL
    # =====================================================

    item["score_semantico"] = score
    item["motivos_score_semantico"] = motivos

    return item