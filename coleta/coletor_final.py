import re
import json
import unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlsplit, urlunsplit

import pandas as pd
import requests
from bs4 import BeautifulSoup

from config.config_loader import carregar_fontes
from processamento.vocabulary import (
    TERMOS_SETOR_AUDIOVISUAL,
    TERMOS_OPORTUNIDADE,
    TERMOS_RUIDO,
)

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

URLS_CANDIDATAS_PATH = Path("data/bruto/urls_candidatas.json")

COLUNAS_CSV = [
    "fonte",
    "origem_tipo",
    "pais",
    "classe",
    "titulo",
    "tipo",
    "fase_produto",
    "produto",
    "categoria",
    "valor",
    "score",
    "ano",
    "link",
    "origem",
]


def limpar_texto(texto):
    return re.sub(r"\s+", " ", texto or "").strip()


def normalizar(texto):
    if texto is None:
        return ""
    return (
        unicodedata.normalize("NFKD", str(texto))
        .encode("ASCII", "ignore")
        .decode("ASCII")
        .lower()
    )


def link_absoluto(base_url, href):
    if not href:
        return None
    return urljoin(base_url, href)


def normalizar_link(link):
    if not link:
        return ""
    partes = urlsplit(link)
    return urlunsplit((partes.scheme, partes.netloc, partes.path, "", ""))


def extrair_ano_de_titulo_ou_link(titulo, link=""):
    texto = f"{titulo} {link}"
    match = re.search(r"\b(19\d{2}|20\d{2})\b", texto)
    return match.group(1) if match else ""


def extrair_valor(titulo, link=""):
    texto = f"{titulo} {link}"

    padroes = [
        r"(R\$\s?\d[\d\.\,]*)",
        r"(US\$\s?\d[\d\.\,]*)",
        r"(€\s?\d[\d\.\,]*)",
        r"(\$\s?\d[\d\.\,]*)",
    ]

    for padrao in padroes:
        match = re.search(padrao, texto, flags=re.IGNORECASE)
        if match:
            return match.group(1)

    return ""


def detectar_pais(link, nome_fonte=""):
    base = normalizar(f"{link} {nome_fonte}")
    dominio = urlparse(link).netloc.lower() if link else ""

    if "pbh" in base or "prefeitura" in base or "gov.br" in dominio or dominio.endswith(".br"):
        return "Brasil"
    if dominio.endswith(".pt"):
        return "Portugal"
    if dominio.endswith(".fr"):
        return "França"
    if dominio.endswith(".es"):
        return "Espanha"
    if dominio.endswith(".it"):
        return "Itália"
    if dominio.endswith(".de"):
        return "Alemanha"
    if dominio.endswith(".eu"):
        return "União Europeia"
    if dominio.endswith(".uk") or dominio.endswith(".co.uk"):
        return "Reino Unido"
    if "unesco" in dominio:
        return "Internacional"
    if dominio.endswith(".org") or dominio.endswith(".com"):
        return "Internacional"

    return "Não identificado"


def classificar_origem(nome_fonte, link):
    base = normalizar(f"{nome_fonte} {link}")

    if any(t in base for t in ["prefeitura", "municipal", "cidade"]):
        return "municipal"

    if any(t in base for t in ["secult", "secretaria", "estadual", "estado"]):
        return "estadual"

    if any(t in base for t in ["gov.br", "ancine", "minc", "ministerio", "ministry"]):
        return "federal"

    if any(t in base for t in ["unesco", "europa", "europe", ".eu", "international"]):
        return "internacional"

    return "outro"


def extrair_contexto_link(a_tag):
    textos = []

    try:
        texto_link = limpar_texto(a_tag.get_text(" ", strip=True))
        if texto_link:
            textos.append(texto_link[:180])

        pai = a_tag.parent
        if pai:
            texto_pai = limpar_texto(pai.get_text(" ", strip=True))
            if texto_pai and texto_pai not in textos:
                textos.append(texto_pai[:280])

        container = a_tag.find_parent(["article", "li"])
        if container:
            texto_container = limpar_texto(container.get_text(" ", strip=True))
            if texto_container and texto_container not in textos:
                textos.append(texto_container[:420])

    except Exception:
        pass

    texto_final = " ".join(t for t in textos if t)
    return limpar_texto(texto_final[:520])


def texto_valido(texto):
    if not texto:
        return False

    texto_limpo = normalizar(texto)

    lixos = [
        "acesse",
        "clique aqui",
        "leia mais",
        "saiba mais",
        "edital - acesse",
        "ver mais",
    ]

    if any(lixo in texto_limpo for lixo in lixos):
        return False

    if len(texto_limpo) < 10:
        return False

    if texto_limpo.startswith("edital") and len(texto_limpo) < 25:
        return False

    return True


def titulo_generico(texto):
    if not texto:
        return False

    base = normalizar(texto)

    termos = [
        "servicos",
        "consulta",
        "acesso",
        "portal",
        "sistemas",
        "informacoes",
        "dados",
        "publicacoes",
    ]

    return len(base) < 40 and any(t in base for t in termos)


def lixo_licitacao(texto):
    if not texto:
        return False

    texto = normalizar(texto)

    termos_lixo_fortes = [
        "pregao",
        "pregao eletronico",
        "licitacao",
        "registro de precos",
        "ata de registro",
        "menor preco",
        "fornecedor",
        "compras",
        "suprimentos",
        "contratacao de empresa",
        "material",
        "generos alimenticios",
        "limpeza",
        "papelaria",
        "descartaveis",
        "fralda",
        "utensilios",
        "fornecimento",
        "aquisicao",
        "acucar",
        "carnes",
        "feijoes",
        "leite em po",
        "agua mineral",
        "sabonetes",
        "absorventes higienicos",
        "locacao de veiculos",
        "material eletrico",
        "artigos para escritorio",
        "produtos saneantes",
    ]

    termos_suspeitos = [
        "edital",
        "concorrencia",
        "credenciamento",
    ]

    if any(t in texto for t in termos_lixo_fortes):
        return True

    if any(t in texto for t in termos_suspeitos):
        if not any(x in texto for x in [
            "filme",
            "cinema",
            "audiovisual",
            "documentario",
            "serie",
            "roteiro",
            "video",
            "filmagem",
            "animacao",
        ]):
            return True

    return False


def eh_licitacao_audiovisual(texto):
    if not texto:
        return False

    base = normalizar(texto)

    termos_bons = [
        "producao audiovisual",
        "servico audiovisual",
        "servicos de filmagem",
        "filmagem",
        "captacao de imagem",
        "captacao de audio",
        "edicao de video",
        "video institucional",
        "producao de video",
        "cobertura audiovisual",
        "conteudo audiovisual",
        "documentario",
        "animacao",
        "motion graphics",
        "audiovisual",
        "cinema",
        "serie",
        "roteiro",
        "video",
    ]

    return any(t in base for t in termos_bons)


def link_valido(href):
    if not href:
        return False

    href_lower = href.lower()

    bloqueados = [
        "#",
        "javascript:void",
        "mailto:",
        "tel:",
        "/search",
        "/login",
        "/contact",
        "/newsletter",
        "/cookie",
        "/privacy",
        "/terms",
        "/termos",
    ]

    return not any(item in href_lower for item in bloqueados)


def url_idioma_espelho(link):
    if not link:
        return False

    padroes = [
        "/bg/", "/cs/", "/da/", "/de/", "/el/", "/es/", "/et/",
        "/fi/", "/fr/", "/hr/", "/hu/", "/it/", "/lt/", "/lv/",
        "/mt/", "/nl/", "/pl/", "/pt/", "/ro/", "/sk/", "/sl/", "/sv/"
    ]

    link_lower = link.lower()
    return any(p in link_lower for p in padroes)


def pagina_generica_ruim(titulo, link=""):
    base = normalizar(f"{titulo} {link}")

    termos = [
        "feedback",
        "funding guide",
        "guide",
        "case studies",
        "get inspired",
        "about this page",
        "how it works",
        "learn more",
        "discover more",
        "estrutura organizacional",
        "aplicacao da logomarca",
        "demonstracoes contabeis",
        "governanca",
        "relatorio",
        "coordenacao",
        "gerencia",
        "execucao orcamentaria",
        "artigos",
    ]

    return any(t in base for t in termos)


def pagina_ruim_institucional_ou_sistema(titulo, link=""):
    base = normalizar(f"{titulo} {link}")

    termos_ruins = [
        "publicacoes",
        "publicacao",
        "painel interativo",
        "paineis interativos",
        "anuario",
        "observatorio",
        "mapa de complexos cinematograficos",
        "mapa de mostras e festivais",
        "consulta processual",
        "consulta de roe",
        "consulta de projetos",
        "sistema de controle",
        "sistema de apoio",
        "usuarios externos",
        "outros sistemas",
        "savi",
        "sicav",
        "sad sei",
        "protocolo digital",
        "captcha",
        "verify you are human",
        "what code is in the image",
        "audio is not supported",
        "your support id",
        "agencia nacional do cinema",
        "entidades vinculadas",
        "gabinete da ministra",
        "secretaria secretaria",
        "comites de cultura",
        "estrutura organizacional",
        "governanca",
        "demonstracoes contabeis",
        "coordenacao",
        "gerencia",
        "relatorio",
        "revista",
        "noticias editais editais abertos editais em andamento editais encerrados",
    ]

    return any(t in base for t in termos_ruins)


def falso_positivo_institucional(texto, link=""):
    base = normalizar(f"{texto} {link}")

    termos = [
        "jornada do patrimonio",
        "cada olhar, uma historia",
        "programa vocacional",
        "cursos gratuitos",
        "programacao",
        "abre e fecha",
        "feriado tiradentes",
        "equipamentos municipais",
        "confira o funcionamento",
        "inscricoes presenciais",
        "casas de cultura",
        "ceus",
        "emias",
        "mais noticias",
        "newsletter",
        "inscreva-se na nossa newsletter",
        "circuito spcine",
        "cinema de graca",
        "noticias sobre",
    ]

    return any(t in base for t in termos)


def pagina_estrutural_governo(titulo, link=""):
    base = normalizar(f"{titulo} {link}")

    termos_estruturais = [
        "servicos",
        "buscar servicos",
        "categorias",
        "orgaos",
        "entidades publicas",
        "servidor publico",
        "publico alvo",
        "gov.br",
        "portal da transparencia",
        "consulta",
        "consulta de",
        "sistema de",
        "sistemas",
        "protocolo",
        "acesso",
        "usuarios",
        "passo a passo",
        "como consultar",
        "planejamento institucional",
        "portarias",
        "legislacao",
        "decretos",
        "resolucoes",
        "instrucoes normativas",
        "audiencias publicas",
        "canais de atendimento",
        "ouvidoria",
        "horario de atendimento",
        "prestacao de contas",
        "transparencia",
        "contratacoes anuais",
        "orgao",
    ]

    return any(t in base for t in termos_estruturais)


def classificar_tipo(titulo, link=""):
    base = normalizar(f"{titulo} {link}")

    if any(t in base for t in [
        "estagio",
        "vaga",
        "job",
        "trabalhe conosco",
        "career",
        "carreira",
        "selecao de estagiarios",
    ]):
        return "trabalho"

    mapa = {
        "edital": [
            "edital",
            "chamada publica",
            "call for proposals",
            "open call",
            "inscricoes",
            "inscricoes abertas",
            "submission deadline",
            "applications open",
            "credenciamento",
            "chamamento publico",
            "selecao publica",
            "submit",
            "submissao",
            "submissoes",
            "convocacao",
        ],
        "grant": [
            "grant",
            "grants",
            "financial support",
            "funding opportunity",
            "fomento internacional",
            "scholarship fund",
            "research grant",
        ],
        "festival": [
            "festival",
            "film festival",
            "festival de cinema",
            "call for entries",
            "accepting submissions",
            "entries open",
            "submit your film",
        ],
        "mostra": [
            "mostra",
            "screening",
            "screenings",
            "exibicao",
            "exibicoes",
            "sessao",
            "sessoes",
        ],
        "mercado": [
            "market",
            "film market",
            "industry",
            "industry days",
            "industry forum",
            "coproduction",
            "co-production",
            "coproduction market",
            "co-production market",
            "forum",
            "rodada de negocios",
            "mercado",
        ],
        "lab": [
            "script lab",
            "lab",
            "laboratory",
            "laboratorio",
            "mentoria",
            "mentorship",
            "development program",
            "writers room",
            "incubadora",
            "residence lab",
        ],
        "formacao": [
            "curso",
            "capacitacao",
            "oficina",
            "workshop",
            "training",
            "academy",
            "masterclass",
            "seminario",
            "webinario",
            "programa de formacao",
            "formacao",
            "capacitar",
        ],
        "premio": [
            "award",
            "prize",
            "premio",
            "premiacao",
        ],
        "residencia": [
            "residency",
            "residencies",
            "residencia",
        ],
        "bolsa": [
            "fellowship",
            "scholarship",
            "bolsa",
        ],
    }

    for tipo, termos in mapa.items():
        if any(t in base for t in termos):
            return tipo

    return "outro"


def classificar_categoria(titulo, link=""):
    base = normalizar(f"{titulo} {link}")

    categorias = {
        "audiovisual": [
            "audiovisual", "cinema", "film", "movie", "screen",
            "screenplay", "roteiro", "documentario",
            "animation", "animacao", "series", "serie", "tv", "video",
            "equipamentos audiovisual", "equipamento audiovisual"
        ],
        "cultura": [
            "culture", "cultural", "cultura", "arte", "arts", "creative",
            "patrimonio"
        ],
        "inovacao": [
            "innovation", "innovative", "tech", "technology", "startup",
            "immersive", "xr", "vr", "ar", "games"
        ]
    }

    for categoria, termos in categorias.items():
        if any(t in base for t in termos):
            return categoria

    return "geral"


def classificar_fase_produto(titulo, link=""):
    base = normalizar(f"{titulo} {link}")

    if any(t in base for t in [
        "development", "desenvolvimento", "roteiro", "screenplay",
        "project development", "concept"
    ]):
        return "desenvolvimento"

    if any(t in base for t in [
        "production", "producao", "shooting", "filming", "realizacao"
    ]):
        return "producao"

    if any(t in base for t in [
        "post-production", "postproduction", "pos-producao",
        "editing", "finalization", "finalizacao", "montagem"
    ]):
        return "pos_producao"

    if any(t in base for t in [
        "distribution", "distribuicao", "circulation", "sales"
    ]):
        return "distribuicao"

    if any(t in base for t in [
        "festival", "mostra", "screening", "exhibition", "exibicao"
    ]):
        return "exibicao"

    if any(t in base for t in [
        "market", "pitch", "pitching", "industry", "coproduction",
        "co-production", "forum", "rodada de negocios"
    ]):
        return "mercado"
    
    if "edital" in base:
        return "desenvolvimento_roteiro"

    if "inscricao" in base or "inscricoes" in base:
        return "festival_inscricao"

    return "nao identificado"


def classificar_produto(titulo, link=""):
    base = normalizar(f"{titulo} {link}")

    mapa = {
        "desenvolvimento_roteiro": [
            "roteiro", "screenplay", "script", "script lab",
            "story development", "project development",
            "desenvolvimento", "writers room", "writing"
        ],
        "producao_obra": [
            "production", "producao", "shooting", "filming",
            "realizacao", "principal photography"
        ],
        "finalizacao": [
            "post-production", "postproduction", "pos-producao",
            "finalization", "finalizacao", "editing",
            "montagem", "color grading", "sound design"
        ],
        "distribuicao_circulacao": [
            "distribution", "distribuicao", "circulation",
            "sales", "audience design", "exhibition",
            "exibicao", "screening"
        ],
        "festival_inscricao": [
            "festival",
            "film festival",
            "call for entries",
            "submission",
            "submit your film",
            "submissoes",
            "inscricoes abertas",
            "official selection",
            "festival de cinema",
            "entries open",
            "now accepting submissions",
            "accepting submissions",
            "submit",
        ],
        "mercado_pitch_coproducao": [
            "market", "pitch", "pitching", "coproduction",
            "co-production", "forum", "rodada de negocios",
            "industry days", "industry forum", "one-to-one"
        ],
        "formacao_mentoria": [
            "lab", "laboratory", "laboratorio", "mentoria",
            "mentorship", "workshop", "training", "academy",
            "masterclass", "residency", "residencia",
            "curso", "oficina", "capacitacao", "capacitar"
        ],
        "aquisicao_servico_audiovisual": [
            "contratacao de empresa para producao audiovisual",
            "servico audiovisual", "servicos de filmagem",
            "filmagem", "captacao de imagem", "captacao de audio",
            "edicao de video", "video institucional",
            "producao de video", "cobertura audiovisual",
            "conteudo audiovisual", "documentario institucional",
            "campanha audiovisual"
        ]
    }

    pontuacoes = {}

    for produto, termos in mapa.items():
        pontos = sum(1 for t in termos if t in base)
        if pontos > 0:
            pontuacoes[produto] = pontos

    if pontuacoes:
        return max(pontuacoes, key=pontuacoes.get)

    return "nao identificado"


def ajustar_produto_por_tipo(produto, tipo, titulo):
    base = normalizar(titulo)

    if produto != "nao identificado":
        return produto

    if tipo == "mercado":
        return "mercado_pitch_coproducao"

    if tipo == "lab":
        return "formacao_mentoria"

    if tipo == "festival":
        return "festival_inscricao"

    if tipo == "mostra":
        return "festival_inscricao"

    if tipo == "formacao":
        if any(t in base for t in ["roteiro", "screenplay", "script", "writing"]):
            return "desenvolvimento_roteiro"
        return "formacao_mentoria"

    if tipo == "edital":
        if any(t in base for t in ["roteiro", "screenplay", "development", "script"]):
            return "desenvolvimento_roteiro"
        if any(t in base for t in ["producao", "production", "filming", "shooting"]):
            return "producao_obra"
        if any(t in base for t in ["finalizacao", "post-production", "editing", "montagem"]):
            return "finalizacao"
        if any(t in base for t in ["distribuicao", "distribution", "circulation", "sales"]):
            return "distribuicao_circulacao"

    if tipo == "grant":
        if any(t in base for t in ["roteiro", "screenplay", "development", "script"]):
            return "desenvolvimento_roteiro"
        if any(t in base for t in ["producao", "production", "filming", "shooting"]):
            return "producao_obra"
        if any(t in base for t in ["finalizacao", "post-production", "editing"]):
            return "finalizacao"
        if any(t in base for t in ["distribution", "distribuicao", "circulation", "sales"]):
            return "distribuicao_circulacao"

    return produto


def classificar_classe(titulo, link="", tipo="", score=0):
    base = normalizar(f"{titulo} {link}")

    if pagina_ruim_institucional_ou_sistema(titulo, link):
        return "noticia"

    if falso_positivo_institucional(titulo, link):
        return "noticia"

    termos_noticia = [
        "noticia",
        "news",
        "anuncia",
        "anunciado",
        "anunciada",
        "divulga",
        "divulgam",
        "lanca",
        "lancamento",
        "estreia",
        "celebra",
        "homenagem",
        "debate",
        "evento realizado",
        "foi realizado",
        "resultado",
        "resultados",
        "informa",
        "promove acoes",
        "sessao especial",
        "mostra especial",
    ]

    termos_abertura = [
        "inscricoes abertas",
        "inscricao aberta",
        "open call",
        "call open",
        "apply now",
        "deadline",
        "prazo",
        "submissao",
        "submissoes",
        "credenciamento",
        "chamamento publico",
        "selecao publica",
        "call for entries",
        "call for proposals",
        "applications open",
        "convocacao",
    ]

    termos_setor = [
        "audiovisual",
        "cinema",
        "film",
        "documentario",
        "roteiro",
        "serie",
        "video",
        "animacao",
    ]

    if tipo == "trabalho":
        return "noticia"

    if eh_licitacao_audiovisual(titulo):
        return "oportunidade"

    tem_abertura = any(t in base for t in termos_abertura)
    tem_noticia = any(t in base for t in termos_noticia)
    tem_setor = any(t in base for t in termos_setor)

    if tem_abertura and tem_setor:
        return "oportunidade"

    tipos_fortes = {"edital", "grant", "lab", "residencia", "mercado", "bolsa"}
    if tipo in tipos_fortes and score >= 20:
        return "oportunidade"

    tipos_medios = {"festival", "mostra", "formacao", "premio"}
    if tipo in tipos_medios:
        if tem_abertura:
            return "oportunidade"
        if score >= 45:
            return "oportunidade"

    if tem_noticia and not tem_abertura:
        return "noticia"

    if score >= 70:
        return "oportunidade"

    if any(t in base for t in TERMOS_OPORTUNIDADE) and score >= 35:
        return "oportunidade"

    if score >= 25 and tem_setor:
        return "oportunidade"

    return "noticia"


def score_relevancia(titulo, link):
    base = normalizar(f"{titulo} {link}")
    score = 0

    fortes_abertura = [
        "edital",
        "open call",
        "call for proposals",
        "call for entries",
        "inscricoes abertas",
        "submission",
        "deadline",
        "prazo final",
        "applications open",
        "chamamento publico",
        "selecao publica",
        "credenciamento",
        "convocacao",
    ]

    setor_av = [
        "audiovisual",
        "cinema",
        "film",
        "documentario",
        "serie",
        "animacao",
        "roteiro",
        "screenplay",
        "video",
        "filmagem",
    ]

    sinais_ruins = [
        "noticia",
        "news",
        "agenda",
        "relatorio",
        "governanca",
        "estrutura organizacional",
        "artigos",
        "apresentacao institucional",
        "demonstracoes contabeis",
        "coordenacao",
        "gerencia",
    ]

    for termo in TERMOS_OPORTUNIDADE:
        if normalizar(termo) in base:
            score += 12

    for termo in TERMOS_SETOR_AUDIOVISUAL:
        if normalizar(termo) in base:
            score += 10

    for termo in TERMOS_RUIDO:
        if normalizar(termo) in base:
            score -= 25

    for termo in fortes_abertura:
        if termo in base:
            score += 40

    for termo in setor_av:
        if termo in base:
            score += 20

    for termo in sinais_ruins:
        if termo in base:
            score -= 35

    if pagina_ruim_institucional_ou_sistema(titulo, link):
        score -= 120

    if pagina_estrutural_governo(titulo, link):
        score -= 30

    if falso_positivo_institucional(titulo, link):
        score -= 150

    if eh_licitacao_audiovisual(titulo):
        score += 25

    if lixo_licitacao(titulo) and not eh_licitacao_audiovisual(titulo):
        score -= 80

    if "festival" in base:
        score += 10

    if "pitching" in base or "pitch" in base:
        score += 15

    if "lab" in base or "laboratory" in base or "laboratorio" in base:
        score += 15

    if "residency" in base or "residencia" in base:
        score += 15

    return score


def score_oportunidade(item):
    score = item.get("score", 0)
    titulo = normalizar(item.get("titulo") or "")
    produto = normalizar(item.get("produto") or "")
    tipo = normalizar(item.get("tipo") or "")

    if "edital" in titulo:
        score += 40

    if any(p in titulo for p in [
        "inscricoes abertas",
        "open call",
        "call for",
        "apply now",
        "submissao",
        "deadline",
        "prazo",
        "convocacao",
    ]):
        score += 30

    if item.get("pais") not in ["Brasil", "", None]:
        score += 10

    if produto == "aquisicao_servico_audiovisual":
        score += 25

    if tipo in ["grant", "edital", "lab", "mercado", "residencia"]:
        score += 10

    if any(p in titulo for p in [
        "acesse",
        "clique aqui",
        "saiba mais",
        "leia mais",
    ]):
        score -= 80

    if any(p in titulo for p in [
        "anuncia",
        "divulga",
        "lanca",
        "evento",
        "seminario",
        "webinario",
        "debate",
    ]):
        score -= 60

    return score


def parece_oportunidade_audiovisual(texto, link):
    base = normalizar(f"{texto} {link}")

    sinais_abertura = [
        "edital",
        "open call",
        "call for proposals",
        "call for entries",
        "inscricoes abertas",
        "applications open",
        "submission",
        "deadline",
        "prazo",
        "chamamento publico",
        "selecao publica",
        "credenciamento",
        "convocacao",
    ]

    sinais_setor = [
        "audiovisual",
        "cinema",
        "film",
        "documentario",
        "serie",
        "roteiro",
        "screenplay",
        "video",
        "animacao",
        "filmagem",
    ]

    if eh_licitacao_audiovisual(texto):
        return True

    tem_abertura = any(t in base for t in sinais_abertura)
    tem_setor = any(t in base for t in sinais_setor)

    return tem_abertura and tem_setor


def parece_noticia_audiovisual(texto, link):
    base = normalizar(f"{texto} {link}")

    termos_noticia = [
        "noticia",
        "news",
        "anuncia",
        "anunciado",
        "anunciada",
        "lanca",
        "lancamento",
        "resultado",
        "resultados",
        "divulga",
        "publica",
        "publicado",
        "publicada",
        "estreia",
        "programacao",
        "informa",
        "debate",
        "promove acoes",
        "celebra",
        "premiacao",
    ]

    termos_setor = [normalizar(t) for t in TERMOS_SETOR_AUDIOVISUAL] + [
        "culture",
        "cultural",
        "cultura",
        "creative",
        "arte",
        "arts",
        "video",
    ]

    tem_noticia = any(t in base for t in termos_noticia)
    tem_setor = any(t in base for t in termos_setor)

    return tem_noticia and tem_setor and not any(
        p in base for p in [
            "inscricoes abertas",
            "edital aberto",
            "call open",
            "open call",
            "submissoes abertas",
            "apply now",
            "deadline",
            "prazo",
            "convocacao",
        ]
    )


def parece_item_audiovisual(texto, link):
    return (
        parece_oportunidade_audiovisual(texto, link)
        or parece_noticia_audiovisual(texto, link)
    )


def baixar_html(url):
    resp = requests.get(url, headers=HEADERS, timeout=(10, 40))
    resp.raise_for_status()
    return resp.text


def extrair_links_fonte(nome_fonte, url):
    print(f"\n🔎 Coletando: {nome_fonte}")
    resultados = []

    try:
        html = baixar_html(url)
        soup = BeautifulSoup(html, "html.parser")
        links = soup.find_all("a")

        print(f"Total de links encontrados na página: {len(links)}")

        for a in links:
            titulo = limpar_texto(a.get_text(" ", strip=True))
            href = a.get("href")
            href = link_absoluto(url, href)

            if not href or not link_valido(href):
                continue

            if url_idioma_espelho(href):
                continue

            contexto = extrair_contexto_link(a)
            texto_base = contexto if contexto else titulo

            if len(texto_base) < 10:
                continue

            if not texto_valido(texto_base):
                continue

            if titulo_generico(texto_base):
                continue

            if pagina_generica_ruim(texto_base, href):
                continue

            if pagina_ruim_institucional_ou_sistema(texto_base, href):
                continue

            if falso_positivo_institucional(texto_base, href):
                continue

            if lixo_licitacao(texto_base):
                if not eh_licitacao_audiovisual(texto_base):
                    continue

            if not parece_item_audiovisual(texto_base, href):
                continue

            tipo_item = classificar_tipo(texto_base, href)
            score = score_relevancia(texto_base, href)
            classe_prevista = classificar_classe(texto_base, href, tipo_item, score)

            produto_item = classificar_produto(texto_base, href)
            produto_item = ajustar_produto_por_tipo(produto_item, tipo_item, texto_base)

            if classe_prevista == "oportunidade" and score < 12 and not eh_licitacao_audiovisual(texto_base):
                continue

            resultados.append({
                "fonte": nome_fonte,
                "origem_tipo": classificar_origem(nome_fonte, href),
                "pais": detectar_pais(href, nome_fonte),
                "classe": classe_prevista,
                "titulo": texto_base,
                "tipo": tipo_item,
                "fase_produto": classificar_fase_produto(texto_base, href),
                "produto": produto_item,
                "categoria": classificar_categoria(texto_base, href),
                "valor": extrair_valor(texto_base, href),
                "score": score,
                "ano": extrair_ano_de_titulo_ou_link(texto_base, href),
                "link": href,
                "origem": url,
            })

        print(f"{len(resultados)} resultados relevantes encontrados.")

    except Exception as e:
        print(f"Erro na fonte {nome_fonte}: {e}")

    return resultados


def deduplicar_resultados(resultados):
    vistos = set()
    limpos = []

    for item in resultados:
        titulo = normalizar(item.get("titulo") or "")
        link = normalizar_link(item.get("link") or "")
        chave = (titulo, link)

        if chave in vistos:
            continue

        vistos.add(chave)
        limpos.append(item)

    return limpos


def ordenar_resultados(resultados):
    return sorted(
        resultados,
        key=lambda x: (
            -(x.get("score", 0) or 0),
            x.get("fonte", ""),
            x.get("tipo", ""),
            x.get("titulo", ""),
        )
    )


def salvar_csv_incremental(resultados, oportunidades_ordenadas=None):
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(resultados)

    if df.empty:
        for nome in ["tudo.csv", "oportunidades.csv", "noticias.csv"]:
            caminho = output_dir / nome
            pd.DataFrame(columns=COLUNAS_CSV).to_csv(
                caminho,
                index=False,
                encoding="utf-8-sig"
            )
        print("\nNenhum resultado para salvar.")
        return

    for coluna in COLUNAS_CSV:
        if coluna not in df.columns:
            df[coluna] = ""

    df = df[COLUNAS_CSV]

    print("\nDistribuição de classe:")
    print(df["classe"].value_counts(dropna=False))

    print("\nDistribuição de tipo:")
    print(df["tipo"].value_counts(dropna=False))

    print("\nDistribuição de produto:")
    print(df["produto"].value_counts(dropna=False))

    df_tudo = df.copy()
    df_tudo.to_csv(output_dir / "tudo.csv", index=False, encoding="utf-8-sig")

    if oportunidades_ordenadas is not None:
        df_oportunidades = pd.DataFrame(oportunidades_ordenadas)
        for coluna in COLUNAS_CSV:
            if coluna not in df_oportunidades.columns:
                df_oportunidades[coluna] = ""
        if "score_final" in df_oportunidades.columns:
            df_oportunidades = df_oportunidades[COLUNAS_CSV + ["score_final"]]
        else:
            df_oportunidades = df_oportunidades[COLUNAS_CSV]
    else:
        df_oportunidades = df[df["classe"] == "oportunidade"].copy()

    df_oportunidades.to_csv(
        output_dir / "oportunidades.csv",
        index=False,
        encoding="utf-8-sig"
    )

    df_noticias = df[df["classe"] == "noticia"].copy()
    df_noticias.to_csv(
        output_dir / "noticias.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\nCSVs salvos em output/")
    print(f"tudo.csv: {len(df_tudo)} linhas")
    print(f"oportunidades.csv: {len(df_oportunidades)} linhas")
    print(f"noticias.csv: {len(df_noticias)} linhas")


def carregar_urls_candidatas():
    """
    Lê as URLs profundas geradas pelo explorador_inteligente.py.

    Entrada esperada:
    data/bruto/urls_candidatas.json

    Saída:
    lista no mesmo formato usado pelo coletor:
    [
        {"nome": "SECULT MG", "url": "https://...", "origem_explorador": True}
    ]
    """

    if not URLS_CANDIDATAS_PATH.exists():
        print("\n⚠️ Nenhum arquivo de URLs candidatas encontrado.")
        print(f"Esperado em: {URLS_CANDIDATAS_PATH}")
        return []

    try:
        with open(URLS_CANDIDATAS_PATH, "r", encoding="utf-8") as f:
            dados = json.load(f)

        urls = []

        if not isinstance(dados, list):
            print("⚠️ urls_candidatas.json existe, mas não é uma lista.")
            return []

        for item in dados:
            if isinstance(item, str):
                url = item
                nome = "Explorador"
            elif isinstance(item, dict):
                url = item.get("url") or item.get("link")
                nome = item.get("fonte") or item.get("nome") or "Explorador"
            else:
                continue

            if not url:
                continue

            urls.append({
                "nome": nome,
                "url": url,
                "origem_explorador": True,
            })

        print(f"\n🔗 URLs candidatas carregadas: {len(urls)}")
        return urls

    except Exception as e:
        print("⚠️ Erro ao carregar URLs candidatas:", e)
        return []


def preparar_fontes_para_coleta():
    """
    Junta:
    1. fontes configuradas no config_loader
    2. urls candidatas do explorador_inteligente

    Remove duplicadas e preserva o formato esperado pelo coletor.
    """

    config = carregar_fontes()
    fontes_base = config.get("fontes", [])

    fontes_formatadas = []

    for fonte in fontes_base:
        if not isinstance(fonte, dict):
            continue

        if not fonte.get("ativo", True):
            continue

        url = fonte.get("url")
        if not url:
            continue

        fontes_formatadas.append({
            "nome": fonte.get("nome", "Fonte sem nome"),
            "url": url,
            "ativo": fonte.get("ativo", True),
            "origem_explorador": False,
        })

    urls_candidatas = carregar_urls_candidatas()

    fontes = fontes_formatadas + urls_candidatas

    vistos = set()
    fontes_unicas = []

    for fonte in fontes:
        url = fonte.get("url")
        if not url:
            continue

        url_norm = normalizar_link(url)

        if not url_norm or url_norm in vistos:
            continue

        vistos.add(url_norm)
        fontes_unicas.append(fonte)

    print(f"\n🌐 Fontes base carregadas: {len(fontes_formatadas)}")
    print(f"🕷️ URLs do explorador adicionadas: {len(urls_candidatas)}")
    print(f"✅ Total para coleta após deduplicação: {len(fontes_unicas)}")

    return fontes_unicas


def executar_coleta():
    print("Coleta iniciada...")

    fontes = preparar_fontes_para_coleta()

    todos_resultados = []

    for fonte in fontes:
        nome = fonte.get("nome", "Fonte sem nome")
        url = fonte.get("url")

        if not url:
            continue

        resultados = extrair_links_fonte(nome, url)
        todos_resultados.extend(resultados)

    print("\nTOTAL COLETADO ANTES DA DEDUPLICAÇÃO:", len(todos_resultados))

    todos_resultados = deduplicar_resultados(todos_resultados)
    print("TOTAL APÓS DEDUPLICAÇÃO:", len(todos_resultados))

    todos_resultados = ordenar_resultados(todos_resultados)

    oportunidades = [i for i in todos_resultados if i.get("classe") == "oportunidade"]

    for item in oportunidades:
        item["score_final"] = score_oportunidade(item)

    oportunidades_ordenadas = sorted(
        oportunidades,
        key=lambda x: x.get("score_final", 0),
        reverse=True
    )

    print(f"\nTotal final após ordenação: {len(todos_resultados)}")

    for item in todos_resultados[:5]:
        print(
            "EXEMPLO:",
            item.get("titulo"),
            "| tipo:", item.get("tipo"),
            "| produto:", item.get("produto"),
            "| score:", item.get("score")
        )

    salvar_csv_incremental(todos_resultados, oportunidades_ordenadas)


if __name__ == "__main__":
    executar_coleta()