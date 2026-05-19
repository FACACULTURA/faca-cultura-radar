# peneiras.py

from processamento.vocabulary import (
    TERMOS_AUDIOVISUAL_DIRETO,
    TERMOS_AUDIOVISUAL_INDIRETO,
    TERMOS_CULTURA_AMPLA,
    TERMOS_FOMENTO_ESTRUTURAL,
)

import re


def normalizar(texto):
    if not texto:
        return ""
    return re.sub(r"\s+", " ", str(texto).lower()).strip()


# -----------------------------
# PENEIRA 1 — CULTURA
# -----------------------------
def peneira_cultura(texto):
    base = normalizar(texto)

    return any(t in base for t in TERMOS_CULTURA_AMPLA)


# -----------------------------
# PENEIRA 2 — FOMENTO / MECANISMO
# -----------------------------
def peneira_fomento(texto):
    base = normalizar(texto)

    return any(t in base for t in TERMOS_FOMENTO_ESTRUTURAL)


# -----------------------------
# PENEIRA 3 — OPORTUNIDADE REAL
# -----------------------------
def peneira_oportunidade(texto):
    base = normalizar(texto)

    sinais = 0

    if any(p in base for p in [
        "edital", "chamada", "chamamento",
        "inscricoes", "inscricao",
        "deadline", "prazo",
        "apply", "submit",
        "convocatoria",
    ]):
        sinais += 1

    if any(p in base for p in [
        "regulamento", "pdf",
        "selecao", "resultado",
    ]):
        sinais += 1

    return sinais >= 1


# -----------------------------
# PENEIRA 4 — AUDIOVISUAL
# -----------------------------
def peneira_audiovisual(texto):
    base = normalizar(texto)

    direto = any(t in base for t in TERMOS_AUDIOVISUAL_DIRETO)
    indireto = any(t in base for t in TERMOS_AUDIOVISUAL_INDIRETO)

    if direto:
        return "forte"

    if indireto:
        return "possivel"

    return "fraco"


# -----------------------------
# PENEIRA 5 — CLASSIFICAÇÃO FINAL
# -----------------------------
def classificar_item(texto):
    base = normalizar(texto)

    tem_cultura = peneira_cultura(base)
    tem_fomento = peneira_fomento(base)
    tem_oportunidade = peneira_oportunidade(base)
    nivel_av = peneira_audiovisual(base)

    # -----------------------------
    # DECISÃO FINAL
    # -----------------------------

    if tem_oportunidade and nivel_av == "forte":
        return "oportunidade"

    if tem_oportunidade and nivel_av == "possivel":
        return "oportunidade"

    if tem_oportunidade and tem_cultura:
        return "oportunidade"

    if tem_fomento and tem_cultura:
        return "fonte_mecanismo"

    if tem_cultura:
        return "noticia"

    return "descartar"