import re


TERMOS_DERIVADOS_FORTES = [
    "anexo",
    "ata",
    "resultado",
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
    "comissão julgadora",
    "comissao julgadora",
    "parecer",
    "termo de compromisso",
    "termo de premiação",
    "termo de premiacao",
]

TERMOS_EDITAL_REAL = [
    "edital",
    "chamada pública",
    "chamada publica",
    "chamada aberta",
    "inscrições abertas",
    "inscricoes abertas",
    "seleção pública",
    "selecao publica",
    "processo seletivo",
    "concurso",
    "prêmio",
    "premio",
    "bolsa",
    "residência",
    "residencia",
    "fomento",
]


def normalizar(txt):
    if not txt:
        return ""
    txt = str(txt).lower()
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()


def detectar_documento_derivado(item):
    titulo = normalizar(item.get("titulo") or item.get("titulo_principal") or "")
    link = normalizar(item.get("link") or "")
    texto = normalizar(item.get("texto_pagina") or item.get("resumo_pagina") or "")

    base = f"{titulo} {link} {texto[:1000]}"

    derivados = [t for t in TERMOS_DERIVADOS_FORTES if t in base]
    edital_real = [t for t in TERMOS_EDITAL_REAL if t in base]

    eh_pdf_doc = any(link.endswith(ext) for ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx"])
    ano = item.get("ano")

    antigo = False
    try:
        if ano and int(float(ano)) < 2024:
            antigo = True
    except Exception:
        antigo = False

    score_derivado = 0

    if derivados:
        score_derivado += 80

    if eh_pdf_doc:
        score_derivado += 25

    if antigo:
        score_derivado += 50

    if "resultado" in base or "ata" in base or "homolog" in base:
        score_derivado += 100

    if "anexo" in base or "formulário" in base or "formulario" in base:
        score_derivado += 80

    if edital_real and not derivados:
        score_derivado -= 40

    if "inscrições abertas" in base or "inscricoes abertas" in base:
        score_derivado -= 60

    tipo_documento = "principal"

    if score_derivado >= 100:
        tipo_documento = "derivado"

    if "resultado" in base:
        tipo_documento = "resultado"

    if "ata" in base:
        tipo_documento = "ata"

    if "anexo" in base:
        tipo_documento = "anexo"

    if "formulário" in base or "formulario" in base or "ficha de inscrição" in base:
        tipo_documento = "formulario"

    return {
        "eh_documento_derivado": score_derivado >= 100,
        "tipo_documento": tipo_documento,
        "score_documento_derivado": score_derivado,
        "motivos_documento_derivado": derivados,
    }


def aplicar_classificacao_documento(item):
    diagnostico = detectar_documento_derivado(item)

    item["eh_documento_derivado"] = diagnostico["eh_documento_derivado"]
    item["tipo_documento"] = diagnostico["tipo_documento"]
    item["score_documento_derivado"] = diagnostico["score_documento_derivado"]
    item["motivos_documento_derivado"] = diagnostico["motivos_documento_derivado"]

    if item["eh_documento_derivado"]:
        item["prioridade_feed"] = "baixa"
        item["deve_entrar_feed"] = False

    return item