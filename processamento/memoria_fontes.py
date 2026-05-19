# processamento/memoria_fontes.py

from urllib.parse import urlparse


FONTES_MEMORIA = {
    # =========================
    # BRASIL — FEDERAL
    # =========================
    "gov.br/cultura": {
        "peso": 10,
        "tipo": "fonte_mae",
        "pais": "Brasil",
        "estado": None,
        "areas_quentes": [
            "editais",
            "chamadas",
            "fomento",
            "lei-rouanet",
            "pnab",
            "aldir-blanc",
            "audiovisual",
        ],
        "plataformas_externas": [
            "salic.cultura.gov.br",
            "mapas.cultura.gov.br",
        ],
        "sinais_fortes": [
            "lei rouanet",
            "pronac",
            "salic",
            "pnab",
            "aldir blanc",
            "fomento",
            "edital",
            "chamada pública",
            "inscrições",
        ],
        "zonas_frias": [
            "agenda",
            "institucional",
            "galeria",
            "acesso-a-informacao",
        ],
    },

    "ancine.gov.br": {
        "peso": 10,
        "tipo": "fonte_mae",
        "pais": "Brasil",
        "estado": None,
        "areas_quentes": [
            "editais",
            "chamadas-publicas",
            "fsa",
            "fundo-setorial-do-audiovisual",
            "desenvolvimento",
            "producao",
        ],
        "plataformas_externas": [
            "brde.com.br",
            "fsa.brde.com.br",
        ],
        "sinais_fortes": [
            "ancine",
            "fsa",
            "fundo setorial do audiovisual",
            "chamada pública",
            "edital",
            "produção audiovisual",
            "desenvolvimento de projetos",
            "inscrições",
        ],
        "zonas_frias": [
            "transparencia",
            "institucional",
            "agenda",
            "noticias-gerais",
        ],
    },

    "brde.com.br": {
        "peso": 10,
        "tipo": "fonte_mae",
        "pais": "Brasil",
        "estado": None,
        "areas_quentes": [
            "fsa",
            "fundo-setorial-do-audiovisual",
            "editais",
            "chamadas",
            "inscricoes",
        ],
        "plataformas_externas": [],
        "sinais_fortes": [
            "brde",
            "fsa",
            "fundo setorial do audiovisual",
            "audiovisual",
            "edital",
            "chamada pública",
            "inscrição",
            "proposta",
        ],
        "zonas_frias": [
            "institucional",
            "noticias",
            "governanca",
        ],
    },

    # =========================
    # MINAS GERAIS
    # =========================
    "secult.mg.gov.br": {
        "peso": 10,
        "tipo": "fonte_mae",
        "pais": "Brasil",
        "estado": "MG",
        "areas_quentes": [
            "editais",
            "editais-pnab",
            "oportunidades",
            "noticias",
            "lei-paulo-gustavo",
            "aldir-blanc",
        ],
        "plataformas_externas": [
            "descentra.mg.gov.br",
            "mapacultural.mg.gov.br",
        ],
        "sinais_fortes": [
            "secult mg",
            "pnab",
            "aldir blanc",
            "edital",
            "termo de execução cultural",
            "inscrições",
            "descentra",
            "audiovisual",
        ],
        "zonas_frias": [
            "agenda-do-secretario",
            "institucional",
            "galeria",
            "comunicacao",
        ],
    },

    "descentra.mg.gov.br": {
        "peso": 10,
        "tipo": "plataforma_inscricao",
        "pais": "Brasil",
        "estado": "MG",
        "areas_quentes": [
            "editais",
            "inscricoes",
            "menu",
            "oportunidades",
        ],
        "plataformas_externas": [],
        "sinais_fortes": [
            "inscrição",
            "inscrições",
            "formulário",
            "edital",
            "proponente",
            "projeto",
        ],
        "zonas_frias": [
            "login",
            "ajuda",
            "suporte",
        ],
    },

    "cemig.com.br": {
        "peso": 9,
        "tipo": "fonte_mae",
        "pais": "Brasil",
        "estado": "MG",
        "areas_quentes": [
            "cultura",
            "patrocinio",
            "patrocinios",
            "editais",
            "instituto-cultural",
        ],
        "plataformas_externas": [],
        "sinais_fortes": [
            "cemig",
            "patrocínio",
            "patrocinio",
            "cultura",
            "audiovisual",
            "edital",
            "lei estadual de incentivo",
            "lei rouanet",
        ],
        "zonas_frias": [
            "segunda-via",
            "energia",
            "atendimento",
            "sustentabilidade",
        ],
    },

    # =========================
    # ESTADOS
    # =========================
    "cultura.sp.gov.br": {
        "peso": 9,
        "tipo": "fonte_mae",
        "pais": "Brasil",
        "estado": "SP",
        "areas_quentes": ["editais", "proac", "fomento", "audiovisual", "inscricoes"],
        "plataformas_externas": ["proac.sp.gov.br", "spcine.com.br"],
        "sinais_fortes": ["proac", "edital", "fomento", "audiovisual", "inscrição"],
        "zonas_frias": ["agenda", "institucional"],
    },

    "spcine.com.br": {
        "peso": 9,
        "tipo": "fonte_mae",
        "pais": "Brasil",
        "estado": "SP",
        "areas_quentes": ["editais", "chamadas", "programas", "desenvolvimento", "produção"],
        "plataformas_externas": [],
        "sinais_fortes": ["spcine", "edital", "chamada", "audiovisual", "produção", "desenvolvimento"],
        "zonas_frias": ["noticias-gerais", "institucional"],
    },

    "cultura.rj.gov.br": {
        "peso": 9,
        "tipo": "fonte_mae",
        "pais": "Brasil",
        "estado": "RJ",
        "areas_quentes": ["editais", "fomento", "audiovisual", "inscricoes"],
        "plataformas_externas": [],
        "sinais_fortes": ["edital", "fomento", "audiovisual", "cultura rj", "inscrição"],
        "zonas_frias": ["agenda", "institucional"],
    },

    "secult.ba.gov.br": {
        "peso": 8,
        "tipo": "fonte_mae",
        "pais": "Brasil",
        "estado": "BA",
        "areas_quentes": ["editais", "fomento", "audiovisual", "funceb"],
        "plataformas_externas": [],
        "sinais_fortes": ["edital", "funceb", "audiovisual", "fomento", "inscrição"],
        "zonas_frias": ["agenda", "institucional"],
    },

    "secult.ce.gov.br": {
        "peso": 8,
        "tipo": "fonte_mae",
        "pais": "Brasil",
        "estado": "CE",
        "areas_quentes": ["editais", "fomento", "audiovisual", "inscricoes"],
        "plataformas_externas": [],
        "sinais_fortes": ["edital", "audiovisual", "fomento", "inscrição"],
        "zonas_frias": ["agenda", "institucional"],
    },

    "cultura.df.gov.br": {
        "peso": 8,
        "tipo": "fonte_mae",
        "pais": "Brasil",
        "estado": "DF",
        "areas_quentes": ["editais", "fac", "fomento", "audiovisual"],
        "plataformas_externas": [],
        "sinais_fortes": ["fac", "edital", "audiovisual", "fomento", "inscrição"],
        "zonas_frias": ["agenda", "institucional"],
    },

    # =========================
    # CURADORES / PISTAS
    # =========================
    "prosas.com.br": {
        "peso": 6,
        "tipo": "curador",
        "pais": "Brasil",
        "estado": None,
        "areas_quentes": ["editais", "oportunidades", "cultura", "audiovisual"],
        "plataformas_externas": [],
        "sinais_fortes": ["edital", "inscrição", "cultura", "audiovisual", "fomento"],
        "zonas_frias": ["blog", "tag", "categoria", "author"],
    },

    "benfeitoria.com": {
        "peso": 4,
        "tipo": "curador",
        "pais": "Brasil",
        "estado": None,
        "areas_quentes": ["matchfunding", "editais", "cultura"],
        "plataformas_externas": [],
        "sinais_fortes": ["matchfunding", "edital", "cultura", "inscrição"],
        "zonas_frias": ["tag", "blog", "vaquinha", "crowdfunding", "autor"],
    },

    "filmfreeway.com": {
        "peso": 7,
        "tipo": "plataforma_inscricao",
        "pais": "Internacional",
        "estado": None,
        "areas_quentes": ["festival", "submit", "deadline", "film"],
        "plataformas_externas": [],
        "sinais_fortes": ["submit", "deadline", "festival", "film", "short film", "documentary"],
        "zonas_frias": ["browse", "pricing", "help"],
    },
}


SINAIS_GERAIS_QUENTES = [
    "edital",
    "chamada pública",
    "chamada publica",
    "inscrição",
    "inscrições",
    "inscricao",
    "inscricoes",
    "prazo",
    "deadline",
    "formulário",
    "formulario",
    "regulamento",
    "pdf",
    "audiovisual",
    "cinema",
    "documentário",
    "documentario",
    "filme",
    "vídeo",
    "video",
    "licitação",
    "licitacao",
    "pregão",
    "pregao",
    "fomento",
    "lei rouanet",
    "pnab",
    "aldir blanc",
    "fsa",
    "ancine",
    "sav",
]

SINAIS_GERAIS_FRIOS = [
    "agenda-do-secretario",
    "agenda do secretário",
    "agenda do secretario",
    "institucional",
    "quem-somos",
    "quem somos",
    "transparencia",
    "transparência",
    "galeria",
    "fotos",
    "login",
    "privacy",
    "termos",
    "terms",
    "tag/",
    "/tag",
    "author",
    "categoria",
    "category",
    "menu",
    "read more",
]


def normalizar(txt):
    return str(txt or "").lower().strip()


def dominio_da_url(url):
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def caminho_da_url(url):
    try:
        return urlparse(url).path.lower()
    except Exception:
        return ""


def obter_memoria_fonte(url):
    url_baixa = normalizar(url)
    dominio = dominio_da_url(url_baixa)

    for chave, memoria in FONTES_MEMORIA.items():
        if chave in url_baixa or chave in dominio:
            return memoria

    return None


def pontuar_url(url, texto=""):
    """
    Pontua uma URL antes de enriquecer/ler profundamente.
    Serve para o explorador escolher onde gastar tempo.
    """

    url_baixa = normalizar(url)
    texto_baixo = normalizar(texto)
    caminho = caminho_da_url(url_baixa)

    memoria = obter_memoria_fonte(url_baixa)

    score = 0
    motivos = []

    if memoria:
        score += memoria.get("peso", 0) * 10
        motivos.append(f"fonte conhecida: +{memoria.get('peso', 0) * 10}")

        for area in memoria.get("areas_quentes", []):
            if area.lower() in caminho or area.lower() in url_baixa:
                score += 25
                motivos.append(f"area quente: {area}")

        for sinal in memoria.get("sinais_fortes", []):
            if sinal.lower() in url_baixa or sinal.lower() in texto_baixo:
                score += 20
                motivos.append(f"sinal forte: {sinal}")

        for fria in memoria.get("zonas_frias", []):
            if fria.lower() in caminho or fria.lower() in url_baixa:
                score -= 35
                motivos.append(f"zona fria: {fria}")

        if memoria.get("tipo") == "curador":
            score -= 10
            motivos.append("curador: pista, não destino final")

        if memoria.get("tipo") == "plataforma_inscricao":
            score += 15
            motivos.append("plataforma de inscrição")

    for sinal in SINAIS_GERAIS_QUENTES:
        if sinal in url_baixa or sinal in texto_baixo:
            score += 8
            motivos.append(f"sinal geral quente: {sinal}")

    for frio in SINAIS_GERAIS_FRIOS:
        if frio in url_baixa or frio in texto_baixo:
            score -= 20
            motivos.append(f"sinal geral frio: {frio}")

    if url_baixa.endswith(".pdf"):
        score += 12
        motivos.append("pdf")

    if any(x in url_baixa for x in ["anexo", "ata", "resultado", "homologacao", "homologação"]):
        score -= 15
        motivos.append("documento derivado")

    return {
        "score_fonte": score,
        "motivos_fonte": motivos,
        "memoria_fonte": memoria or {},
    }


def enriquecer_com_memoria(item):
    """
    Adiciona score e metadados da fonte ao item.
    Não decide categoria final.
    """

    url = item.get("link") or item.get("url") or item.get("origem") or ""
    texto = " ".join([
        str(item.get("titulo") or ""),
        str(item.get("titulo_pagina") or ""),
        str(item.get("resumo") or ""),
        str(item.get("texto_pagina") or ""),
    ])

    leitura = pontuar_url(url, texto)
    memoria = leitura.get("memoria_fonte") or {}

    item["score_fonte"] = leitura["score_fonte"]
    item["motivos_fonte"] = leitura["motivos_fonte"]

    if memoria:
        item["tipo_fonte"] = memoria.get("tipo")
        item["pais_fonte"] = memoria.get("pais")
        item["estado_fonte"] = memoria.get("estado")

        if not item.get("pais") and memoria.get("pais"):
            item["pais"] = memoria.get("pais")

        if not item.get("estado") and memoria.get("estado"):
            item["estado"] = memoria.get("estado")

    return item


def ordenar_urls_por_prioridade(urls):
    """
    Recebe lista simples de URLs ou lista de dicts com url/link/texto.
    Retorna lista ordenada da mais promissora para a menos promissora.
    """

    itens = []

    for entrada in urls:
        if isinstance(entrada, str):
            url = entrada
            texto = ""
            bruto = entrada
        elif isinstance(entrada, dict):
            url = entrada.get("url") or entrada.get("link") or ""
            texto = entrada.get("texto") or entrada.get("titulo") or ""
            bruto = entrada
        else:
            continue

        leitura = pontuar_url(url, texto)
        itens.append({
            "entrada": bruto,
            "score": leitura["score_fonte"],
            "motivos": leitura["motivos_fonte"],
        })

    itens.sort(key=lambda x: x["score"], reverse=True)

    return [i["entrada"] for i in itens]


def filtrar_urls_promissoras(urls, limite=800, score_minimo=5):
    """
    Reduz a lista de URLs antes de enriquecer páginas.
    """

    itens = []

    for entrada in urls:
        if isinstance(entrada, str):
            url = entrada
            texto = ""
            bruto = entrada
        elif isinstance(entrada, dict):
            url = entrada.get("url") or entrada.get("link") or ""
            texto = entrada.get("texto") or entrada.get("titulo") or ""
            bruto = entrada
        else:
            continue

        leitura = pontuar_url(url, texto)

        if leitura["score_fonte"] >= score_minimo:
            itens.append({
                "entrada": bruto,
                "score": leitura["score_fonte"],
            })

    itens.sort(key=lambda x: x["score"], reverse=True)

    return [i["entrada"] for i in itens[:limite]]