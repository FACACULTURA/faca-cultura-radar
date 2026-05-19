# coleta/validador_final.py

from urllib.parse import urlparse
from datetime import datetime
import re
import hashlib


# ============================================================
# VOCABULÁRIOS
# ============================================================

PALAVRAS_AUDIOVISUAL = [
    "audiovisual", "cinema", "filme", "film", "films",
    "documentário", "documentario", "documentary",
    "curta", "curtas", "longa", "longas", "metragem",
    "roteiro", "screenplay", "produção audiovisual", "producao audiovisual",
    "video", "vídeo", "tv", "televisão", "televisao",
    "série", "serie", "series", "festival", "mostra", "pitching",
    "coprodução", "coproducao", "co-production", "animation", "animação",
    "animacao", "videoclipe", "videoclip", "filmmaking", "filmaker",
    "produtora", "produtoras", "obra audiovisual", "obras audiovisuais",
]

PALAVRAS_CULTURA = [
    "cultura", "cultural", "artes", "arte", "patrimônio", "patrimonio",
    "museu", "biblioteca", "economia criativa", "criativa",
]

PALAVRAS_EDITAL_FORTE = [
    "edital", "chamada pública", "chamada publica",
    "seleção pública", "selecao publica",
    "chamamento público", "chamamento publico",
    "regulamento", "inscrições abertas", "inscricoes abertas",
    "fomento", "premiação", "premiacao",
    "termo de execução cultural", "termo de execucao cultural",
]

PALAVRAS_OPORTUNIDADE_FORTE = [
    "inscrição", "inscrições", "inscricao", "inscricoes",
    "apply", "application", "applications open",
    "submission", "submit", "deadline", "prazo",
    "open call", "call for entries", "call for proposals",
    "festival", "mostra", "curso", "oficina", "workshop",
    "seminário", "seminario", "webinário", "webinario",
    "lab", "laboratório", "laboratorio", "residency", "residência",
    "residencia", "pitching", "mercado", "market",
]

PALAVRAS_NOTICIA = [
    "notícia", "noticia", "news", "anuncia", "anunciou",
    "divulga", "divulgou", "publica", "publicou",
    "lança", "lanca", "lançou", "lancou",
    "firma acordo", "acordo", "resultado de", "balanço", "balanco",
    "setor contribui", "contributes", "report", "relatório", "relatorio",
]

PALAVRAS_LICITACAO = [
    "licitação", "licitacao", "pregão", "pregao",
    "termo de referência", "termo de referencia",
    "compras públicas", "compras publicas",
    "contratação", "contratacao",
]

PALAVRAS_OFICIAIS_BRASIL = [
    "ancine", "sav", "secretaria do audiovisual", "brde", "fsa",
    "fundo setorial do audiovisual", "minc", "ministério da cultura",
    "ministerio da cultura", "funarte", "rouanet",
    "lei rouanet", "salic", "pronac",
    "aldir blanc", "pnab", "lei paulo gustavo", "lpg",
    "secult", "secretaria de cultura", "fundação cultural",
    "fundacao cultural", "mapa cultural", "descentra",
    "cultura.gov.br", "gov.br/cultura",
]

PALAVRAS_RUIDO_TOTAL = [
    "ibid", "continuar lendo", "read more", "close menu",
    "skip navigation", "skip to main content", "acesso ao site",
    "home", "menu", "login", "sign in", "subscribe",
    "newsletter", "privacy", "terms", "contact", "about",
    "faq", "dúvidas", "duvidas",
]

PALAVRAS_DOCUMENTO_TECNICO = [
    "anexo", "ata", "resultado preliminar", "resultado final",
    "lista de inscritos", "lista de habilitados", "lista de selecionados",
    "recurso", "julgamento de recursos", "comissão", "comissao",
    "errata", "retificação", "retificacao", "homologação", "homologacao",
    "ato de confirmação", "ato de confirmacao",
    "parâmetros", "parametros", "manual", "tutorial",
    "dúvidas", "duvidas", "perguntas frequentes",
]

PALAVRAS_CURADOR_RUIDO = [
    "/tag/", "/category/", "/categoria/", "/author/",
    "blog.benfeitoria.com/tag", "matchfunding", "empoderamento",
    "representatividade", "financiamentocoletivo", "crowdfunding",
    "vaquinha", "#",
]

DOMINIOS_PAIS = {
    ".gov.br": "Brasil",
    ".br": "Brasil",
    ".pt": "Portugal",
    ".fr": "França",
    ".de": "Alemanha",
    ".it": "Itália",
    ".es": "Espanha",
    ".uk": "Reino Unido",
    ".co.uk": "Reino Unido",
    ".ca": "Canadá",
    ".au": "Austrália",
    ".ar": "Argentina",
    ".cl": "Chile",
    ".co": "Colômbia",
    ".mx": "México",
    ".uy": "Uruguai",
    ".py": "Paraguai",
    ".ie": "Irlanda",
    ".us": "Estados Unidos",
}


# ============================================================
# HELPERS
# ============================================================

def normalizar_texto(v):
    return re.sub(r"\s+", " ", str(v or "")).strip()


def contem(texto, lista):
    texto = texto.lower()
    return any(p.lower() in texto for p in lista)


def texto_item(item):
    campos = [
        item.get("titulo"),
        item.get("titulo_principal"),
        item.get("titulo_original"),
        item.get("titulo_pagina"),
        item.get("page_title"),
        item.get("resumo"),
        item.get("resumo_pagina"),
        item.get("texto_pagina"),
        item.get("breadcrumbs"),
        item.get("fonte"),
        item.get("instituicao"),
        item.get("link"),
        item.get("url"),
        item.get("origem"),
        item.get("link_inscricao"),
        item.get("link_edital"),
        item.get("link_pdf"),
    ]

    return normalizar_texto(" ".join(str(c or "") for c in campos)).lower()


def url_item(item):
    return str(item.get("link") or item.get("url") or "").lower()


def titulo_item(item):
    return str(item.get("titulo_principal") or item.get("titulo") or "").lower().strip()


def detectar_pais(url):
    dominio = urlparse(url or "").netloc.lower()
    for sufixo, pais in sorted(DOMINIOS_PAIS.items(), key=lambda x: len(x[0]), reverse=True):
        if dominio.endswith(sufixo):
            return pais
    return None


def corrigir_localizacao(item):
    url = url_item(item)
    texto = texto_item(item)

    pais = item.get("pais")
    pais_url = detectar_pais(url)

    if not pais or pais == "Não identificado":
        pais = pais_url

    if ".gov.br" in url or "cultura.gov.br" in url or "gov.br/cultura" in url:
        pais = "Brasil"

    if "secult.mg" in url or "minas gerais" in texto:
        item["estado"] = item.get("estado") or "MG"
        pais = "Brasil"

    if "cultura.sp.gov" in url or "spcine" in url:
        item["estado"] = item.get("estado") or "SP"
        pais = "Brasil"

    if "cultura.rj.gov" in url or "rio de janeiro" in texto:
        item["estado"] = item.get("estado") or "RJ"
        pais = "Brasil"

    if "secult.ba" in url or "bahia" in texto:
        item["estado"] = item.get("estado") or "BA"
        pais = "Brasil"

    if "secult.ce" in url or "ceará" in texto or "ceara" in texto:
        item["estado"] = item.get("estado") or "CE"
        pais = "Brasil"

    if "secult.pe" in url or "pernambuco" in texto:
        item["estado"] = item.get("estado") or "PE"
        pais = "Brasil"

    if "secult.pa" in url or "pará" in texto:
        item["estado"] = item.get("estado") or "PA"
        pais = "Brasil"

    if "secult.rn" in url or "rio grande do norte" in texto:
        item["estado"] = item.get("estado") or "RN"
        pais = "Brasil"

    if "df.gov" in url or "distrito federal" in texto:
        item["estado"] = item.get("estado") or "DF"
        pais = "Brasil"

    if "cultura.sc" in url or "santa catarina" in texto:
        item["estado"] = item.get("estado") or "SC"
        pais = "Brasil"

    if "cultura.pr" in url or "paraná" in texto or "parana" in texto:
        item["estado"] = item.get("estado") or "PR"
        pais = "Brasil"

    # evita São Paulo fake
    eh_sp_real = (
        "spcine" in url
        or "prefeitura de são paulo" in texto
        or "prefeitura de sao paulo" in texto
        or "cultura.sp.gov" in url
    )

    if not eh_sp_real and item.get("cidade") == "São Paulo":
        item["cidade"] = None
        if item.get("estado") == "SP":
            item["estado"] = None

    if pais and pais != "Brasil":
        item["cidade"] = None
        item["estado"] = None

    item["pais"] = pais or item.get("pais") or "Não identificado"
    return item


def chave(item):
    link = (item.get("link") or item.get("url") or "").split("#")[0].rstrip("/").lower()
    titulo = titulo_item(item)
    base = link or titulo
    return hashlib.md5(base.encode()).hexdigest()


def remover_duplicados(lista):
    vistos = set()
    out = []
    for item in lista:
        if not isinstance(item, dict):
            continue
        k = chave(item)
        if k in vistos:
            continue
        vistos.add(k)
        out.append(item)
    return out


def score_semantico(item):
    sinais = item.get("sinais_contexto") or item.get("sinais_pagina") or {}
    return (
        sinais.get("score_semantico")
        or sinais.get("score_enriquecimento")
        or item.get("score_enriquecimento")
        or item.get("score")
        or 0
    )


def tem_link_forte(item):
    texto = texto_item(item)
    url = url_item(item)

    if item.get("link_inscricao") or item.get("link_edital") or item.get("link_pdf"):
        return True

    if url.endswith(".pdf"):
        return True

    return any(p in texto for p in [
        "inscri", "edital", "regulamento", "submit",
        "application", "apply", "submittable", "forms.gle",
        "google.com/forms", "mapa cultural", "prosas",
        "descentra", "salic", "rouanet",
    ])


def extrair_ano(item):
    texto = texto_item(item)
    anos = re.findall(r"\b(20\d{2})\b", texto)
    if not anos:
        return None
    try:
        return max(int(a) for a in anos)
    except Exception:
        return None


def parse_data(item):
    raw = item.get("prazo") or item.get("deadline") or item.get("data_publicacao") or item.get("published_at")
    if not raw:
        return None

    raw = str(raw).strip()

    formatos = ["%d/%m/%Y", "%Y-%m-%d"]
    for fmt in formatos:
        try:
            return datetime.strptime(raw, fmt)
        except Exception:
            pass

    return None


def prazo_futuro(item):
    data = parse_data(item)
    if not data:
        return False
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return data >= hoje


def eh_oficial_brasil(item):
    texto = texto_item(item)
    url = url_item(item)
    return (
        ".gov.br" in url
        or "gov.br" in url
        or contem(texto, PALAVRAS_OFICIAIS_BRASIL)
    )


def eh_curador_intermediario(item):
    return item.get("tipo_origem") == "curador_intermediario" or bool(item.get("fonte_intermediaria"))


def eh_ruido_total(item):
    titulo = titulo_item(item)
    texto = texto_item(item)
    url = url_item(item)

    if not titulo or len(titulo) < 6:
        return True

    if titulo.startswith("http") or titulo.startswith("#"):
        return True

    if contem(titulo, PALAVRAS_RUIDO_TOTAL):
        return True

    if contem(url, PALAVRAS_CURADOR_RUIDO):
        return True

    # páginas tag/blog de curador não são destino final
    if eh_curador_intermediario(item) and contem(url, ["/tag/", "/category/", "/categoria/", "/author/"]):
        return True

    # "ibid 2 ibid" e similares
    palavras = titulo.split()
    if len(palavras) >= 2 and len(set(palavras)) <= 2:
        return True

    return False


def eh_documento_tecnico(item):
    texto = texto_item(item)
    titulo = titulo_item(item)
    url = url_item(item)

    if contem(titulo, PALAVRAS_DOCUMENTO_TECNICO):
        return True

    # PDFs técnicos só não são lixo se o próprio título for edital/chamada/regulamento
    if url.endswith(".pdf") and contem(texto, PALAVRAS_DOCUMENTO_TECNICO):
        if not contem(titulo, ["edital", "chamada", "regulamento"]):
            return True

    return False

def eh_noticia(item):
    texto = texto_item(item)
    titulo = titulo_item(item)

    if contem(titulo, PALAVRAS_NOTICIA):
        return True

    if "/noticia" in url_item(item) or "/news" in url_item(item):
        return True

    return False

def eh_audiovisual_ou_cultura(item):
    texto = texto_item(item)
    sinais = item.get("sinais_contexto") or item.get("sinais_pagina") or {}

    return bool(
        sinais.get("tem_audiovisual")
        or contem(texto, PALAVRAS_AUDIOVISUAL)
        or contem(texto, PALAVRAS_CULTURA)
    )

def eh_edital_real(item):
    texto = texto_item(item)
    titulo = titulo_item(item)
    sinais = item.get("sinais_contexto") or item.get("sinais_pagina") or {}

    tem_edital = (
        sinais.get("tem_edital")
        or contem(texto, PALAVRAS_EDITAL_FORTE)
    )

    if not tem_edital:
        return False

    if eh_noticia(item) and not contem(titulo, PALAVRAS_EDITAL_FORTE):
        return False

    if not eh_audiovisual_ou_cultura(item):
        return False

    if not (tem_link_forte(item) or eh_oficial_brasil(item)):
        return False

    return True


def eh_oportunidade_real(item):
    texto = texto_item(item)
    sinais = item.get("sinais_contexto") or item.get("sinais_pagina") or {}

    tem_forca = (
        sinais.get("tem_inscricao")
        or sinais.get("tem_prazo")
        or contem(texto, PALAVRAS_OPORTUNIDADE_FORTE)
    )

    if not tem_forca:
        return False

    if not eh_audiovisual_ou_cultura(item):
        return False

    if eh_noticia(item) and not (sinais.get("tem_inscricao") or sinais.get("tem_prazo") or tem_link_forte(item)):
        return False

    return True


def aplicar_status_temporal(item):
    data = parse_data(item)
    ano = extrair_ano(item)

    item["ano_detectado"] = ano

    if data:
        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        dias = (data.date() - hoje.date()).days
        item["dias_restantes"] = dias
        item["status_prazo"] = "aberto" if dias >= 0 else "encerrado"
        item["cor_status"] = "verde" if dias >= 0 else "vermelho"
        return item

    if ano:
        item["status_prazo"] = "sem_prazo_com_ano"
        item["cor_status"] = "cinza"
        return item

    item["status_prazo"] = "sem_data"
    item["cor_status"] = "cinza"
    return item


def prioridade_temporal(item):
    data = parse_data(item)
    ano = item.get("ano_detectado") or extrair_ano(item) or 0
    status = item.get("status_prazo")

    # 1. abertos com prazo futuro
    if status == "aberto" and data:
        grupo = 0
        data_ordem = data
    # 2. 2026 sem prazo claro
    elif ano == 2026:
        grupo = 1
        data_ordem = datetime(2026, 12, 31)
    # 3. encerrados de 2026
    elif status == "encerrado" and ano == 2026:
        grupo = 2
        data_ordem = data or datetime(2026, 1, 1)
    # 4. 2025
    elif ano == 2025:
        grupo = 3
        data_ordem = data or datetime(2025, 12, 31)
    # 5. 2024
    elif ano == 2024:
        grupo = 4
        data_ordem = data or datetime(2024, 12, 31)
    # 6. anos anteriores
    elif ano:
        grupo = 5
        data_ordem = data or datetime(int(ano), 12, 31)
    # 7. sem data confiável
    else:
        grupo = 6
        data_ordem = datetime.max

    return (
        grupo,
        data_ordem,
        (item.get("pais") or ""),
        (item.get("estado") or ""),
        titulo_item(item),
    )

def eh_resultado_edital(item):
    texto = texto_item(item)

    termos = [
        "resultado final",
        "resultado preliminar",
        "resultado definitivo",
        "resultado do edital",
        "resultado da seleção",
        "resultado da selecao",
        "lista de aprovados",
        "lista de selecionados",
        "lista de habilitados",
        "proponentes selecionados",
        "homologação",
        "homologacao",
        "habilitados",
        "inabilitados",
        "ato de convocação",
        "ato de convocacao",
        "convocação de proponentes",
        "convocacao de proponentes",
        "ata comissão julgadora",
        "ata comissao julgadora",
    ]

    return any(t in texto for t in termos)

# ============================================================
# CLASSIFICAÇÃO FINAL
# ============================================================

def classificar_final(item):
    texto = texto_item(item)

    if item.get("documento_derivado"):
        if eh_resultado_edital(item):
            item["tipo_noticia"] = "resultado_edital"
            item["notificavel"] = True
            return "noticias"

        if eh_oficial_brasil(item):
            return "revisao"

        return "descarte"

    inscricao = item.get("inscricao") or {}
    forca_inscricao = inscricao.get("forca", 0)
    sinais_inscricao = inscricao.get("sinais", {})

    tem_inscricao_forte = (
        forca_inscricao >= 3
        or sinais_inscricao.get("tem_secao_forte")
    )

    leitura = item.get("leitura_semantica") or {}
    tipo_contexto = leitura.get("tipo_contexto")
    if tipo_contexto == "resultado":
        
        ...
    # 0. RESULTADO DE EDITAL
    if eh_resultado_edital(item):
        return "noticias"

    # 1. EDITAL
    if eh_edital_real(item):
        if tem_inscricao_forte and (item.get("prazo") or item.get("deadline")):
            return "editais"
        return "revisao"

    # 2. OPORTUNIDADE
    if eh_oportunidade_real(item):
        if item.get("prazo") or item.get("deadline") or tem_inscricao_forte:
            return "oportunidades"
        return "revisao"

    # 3. NOTÍCIA
    if eh_noticia(item):
        if eh_audiovisual_ou_cultura(item) or eh_oficial_brasil(item):
            return "noticias"
        return "descarte"

    # 4. OFICIAL SEM PROVA
    if eh_oficial_brasil(item):
        if eh_audiovisual_ou_cultura(item) or contem(texto, PALAVRAS_EDITAL_FORTE):
            return "revisao"

    # 5. CURADOR
    if eh_curador_intermediario(item):
        if tem_link_forte(item) and (
            eh_audiovisual_ou_cultura(item)
            or contem(texto, PALAVRAS_EDITAL_FORTE)
        ):
            return "revisao"

        if eh_audiovisual_ou_cultura(item):
            return "noticias"

        return "descarte"

    return "descarte"

def validar_feed(itens):
    resultado = {
        "editais": [],
        "oportunidades": [],
        "noticias": [],
        "licitacoes": [],
        "revisao": [],
        "descarte": [],
    }

    itens = remover_duplicados(itens)

    for item in itens:
        if not isinstance(item, dict):
            continue

        categoria = classificar_final(item)
        item["categoria_feed"] = categoria

        if categoria in resultado:
            resultado[categoria].append(item)
        else:
            resultado["revisao"].append(item)

    for chave in ["editais", "oportunidades", "noticias", "licitacoes", "revisao"]:
        resultado[chave] = sorted(
            remover_duplicados(resultado[chave]),
            key=prioridade_temporal
        )

    resultado["descarte"] = remover_duplicados(resultado["descarte"])

    return resultado
