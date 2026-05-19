# peneiras_v3.py
# F.CULT — Peneiras semânticas v3
#
# Ideia central:
# - Não jogar fora cedo demais.
# - Separar o que vai para o app do que serve como pista.
# - Notícias continuam notícias.
# - Páginas institucionais, termos, PDFs, políticas e resultados podem virar fonte_contexto
#   quando vierem de domínio relevante ou indicarem uma instituição/fomentador importante.

import re
import unicodedata
from urllib.parse import urlparse


TERMOS_FOMENTO_ESTRUTURAL = [
    "lei rouanet",
    "lei federal de incentivo a cultura",
    "lei federal de incentivo à cultura",
    "pronac",
    "salic",
    "incentivo fiscal",
    "renuncia fiscal",
    "renúncia fiscal",
    "mecenato",
    "sefic",
    "cnic",
    "proponente",
    "projeto cultural",
    "captacao de recursos",
    "captação de recursos",
    "autorizacao para captacao",
    "autorização para captação",
    "fundo nacional de cultura",
    "fundo estadual de cultura",
    "fundo municipal de cultura",
    "fomento a cultura",
    "fomento à cultura",
    "fundo setorial do audiovisual",
    "fsa",
    "brde",
    "funcultura",
    "profice",
    "proac",
    "fazcultura",
    "fundo de cultura",
]

TERMOS_CULTURA_AMPLA = [
    "cultura",
    "cultural",
    "artes",
    "arte",
    "linguagens artisticas",
    "linguagens artísticas",
    "economia criativa",
    "producao cultural",
    "produção cultural",
    "difusao cultural",
    "difusão cultural",
    "circulacao cultural",
    "circulação cultural",
    "formacao cultural",
    "formação cultural",
    "territorios culturais",
    "territórios culturais",
    "patrimonio cultural",
    "patrimônio cultural",
    "memoria",
    "memória",
    "diversidade cultural",
    "industria criativa",
    "indústria criativa",
]

TERMOS_LINGUAGENS_ARTISTICAS = [
    "teatro",
    "danca",
    "dança",
    "circo",
    "musica",
    "música",
    "literatura",
    "artes visuais",
    "fotografia",
    "performance",
    "arte digital",
    "games",
    "animacao",
    "animação",
    "novas midias",
    "novas mídias",
    "multimidia",
    "multimídia",
]

TERMOS_AUDIOVISUAL_DIRETO = [
    "audiovisual",
    "cinema",
    "filme",
    "film",
    "documentario",
    "documentário",
    "curta-metragem",
    "curta metragem",
    "longa-metragem",
    "longa metragem",
    "serie",
    "série",
    "roteiro",
    "screenplay",
    "animacao",
    "animação",
    "video",
    "vídeo",
    "videoclipe",
    "producao audiovisual",
    "produção audiovisual",
    "obra audiovisual",
    "filmagem",
    "captacao de imagem",
    "captação de imagem",
    "cinematografico",
    "cinematográfico",
    "audiovisual market",
    "mercado audiovisual",
]

TERMOS_AUDIOVISUAL_INDIRETO = [
    "memoria audiovisual",
    "memória audiovisual",
    "arquivo audiovisual",
    "registro audiovisual",
    "documentacao audiovisual",
    "documentação audiovisual",
    "formacao em audiovisual",
    "formação em audiovisual",
    "oficina de video",
    "oficina de vídeo",
    "producao de conteudo",
    "produção de conteúdo",
    "midias digitais",
    "mídias digitais",
    "narrativas digitais",
    "imersivo",
    "realidade virtual",
    "realidade aumentada",
    "xr",
    "vr",
    "ar",
    "storytelling",
]

TERMOS_OPORTUNIDADE_REAL = [
    "edital",
    "editais",
    "chamada",
    "chamada publica",
    "chamada pública",
    "chamamento",
    "chamamento publico",
    "chamamento público",
    "selecao",
    "seleção",
    "selecao publica",
    "seleção pública",
    "inscricao",
    "inscrição",
    "inscricoes",
    "inscrições",
    "prazo",
    "deadline",
    "submissao",
    "submissão",
    "submissoes",
    "submissões",
    "apply",
    "submit",
    "application",
    "applications",
    "call for entries",
    "open call",
    "call for proposals",
    "call for applications",
    "regulamento",
    "convocatoria",
    "convocatória",
    "credenciamento",
    "financiamento",
    "funding",
    "grant",
    "grants",
    "fellowship",
    "residency",
    "residencia",
    "residência",
    "lab",
    "laboratorio",
    "laboratório",
    "market",
    "mercado",
    "pitching",
    "coproduction",
    "coproducao",
    "coprodução",
]

TERMOS_EDITAL = [
    "edital",
    "chamada publica",
    "chamada pública",
    "chamamento publico",
    "chamamento público",
    "selecao publica",
    "seleção pública",
    "convocatoria",
    "convocatória",
    "regulamento",
]

TERMOS_LICITACAO = [
    "licitacao",
    "licitação",
    "pregao",
    "pregão",
    "concorrencia",
    "concorrência",
    "contratacao",
    "contratação",
    "compras publicas",
    "compras públicas",
    "termo de referencia",
    "termo de referência",
    "registro de precos",
    "registro de preços",
]

TERMOS_LICITACAO_AUDIOVISUAL = [
    "producao audiovisual",
    "produção audiovisual",
    "servico audiovisual",
    "serviço audiovisual",
    "servicos audiovisuais",
    "serviços audiovisuais",
    "filmagem",
    "captacao de imagem",
    "captação de imagem",
    "captacao de audio",
    "captação de áudio",
    "edicao de video",
    "edição de vídeo",
    "video institucional",
    "vídeo institucional",
    "cobertura audiovisual",
    "conteudo audiovisual",
    "conteúdo audiovisual",
    "documentario institucional",
    "documentário institucional",
    "motion graphics",
]

TERMOS_NOTICIA = [
    "noticia",
    "notícia",
    "news",
    "anuncia",
    "anunciado",
    "anunciada",
    "divulga",
    "divulgado",
    "divulgada",
    "lanca",
    "lança",
    "lancamento",
    "lançamento",
    "informa",
    "publica",
    "publicado",
    "publicada",
    "estreia",
    "celebra",
    "reabre",
    "recebe",
    "promove",
    "realiza",
    "exibe",
    "programacao",
    "programação",
    "agenda",
]

TERMOS_RESULTADO = [
    "resultado final",
    "resultado preliminar",
    "resultado da analise",
    "resultado da análise",
    "analise documental",
    "análise documental",
    "lista de aprovados",
    "lista de selecionados",
    "homologacao",
    "homologação",
    "ata de sorteio",
    "ata",
]

TERMOS_INSTITUCIONAL_FRACO = [
    "termos e condicoes",
    "termos e condições",
    "terminos y condiciones",
    "términos y condiciones",
    "politica de privacidade",
    "política de privacidade",
    "politica de proteccion",
    "política de protección",
    "privacy policy",
    "terms of use",
    "data protection",
    "cookies",
    "uso do site",
    "quem somos",
    "about us",
    "contact",
    "contato",
    "newsletter",
    "login",
]

TERMOS_RUIDO_FORTE = [
    "captcha",
    "verify you are human",
    "page not found",
    "404",
    "erro 404",
    "acesso negado",
    "access denied",
]

TERMOS_RUIDO_COMPRAS_GENERICAS = [
    "generos alimenticios",
    "gêneros alimentícios",
    "limpeza",
    "papelaria",
    "fralda",
    "descartaveis",
    "descartáveis",
    "agua mineral",
    "água mineral",
    "acucar",
    "açúcar",
    "leite em po",
    "leite em pó",
    "material eletrico",
    "material elétrico",
    "saneantes",
    "locacao de veiculos",
    "locação de veículos",
]

DOMINIOS_RELEVANTES = [
    "gov.br",
    "ancine",
    "cultura",
    "secult",
    "spcine",
    "riofilme",
    "brde",
    "bogotamarket.com",
    "programaibermedia.com",
    "filmfreeway.com",
    "showmethefund",
    "sundance.org",
    "filmindependent.org",
    "telefilm.ca",
    "canadacouncil.ca",
    "bfi.org.uk",
    "cnc.fr",
    "coe.int",
    "eurimages",
    "berlinale",
    "efm-berlinale",
    "torinofilmlab",
    "dohafilminstitute",
    "screenaustralia",
    "nzfilm",
    "nfvf",
    "fdcp.ph",
    "biff.kr",
    "proimagenescolombia",
    "imcine",
    "incaa",
    "sanfic",
    "marrakech",
    "durbanfilmmart",
    "realness",
]


def normalizar(texto):
    if not texto:
        return ""

    texto = unicodedata.normalize("NFKD", str(texto))
    texto = texto.encode("ASCII", "ignore").decode("ASCII")
    texto = texto.lower()
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def dominio(link):
    try:
        return urlparse(link).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def contar_termos(texto, termos):
    base = normalizar(texto)
    termos_norm = [normalizar(t) for t in termos]
    return sum(1 for termo in termos_norm if termo and termo in base)


def dominio_relevante(link):
    base = normalizar(link)
    dom = normalizar(dominio(link))
    alvo = f"{base} {dom}"
    return any(normalizar(d) in alvo for d in DOMINIOS_RELEVANTES)


def eh_pdf(link):
    return ".pdf" in normalizar(link)


def eh_doc(link):
    base = normalizar(link)
    return any(ext in base for ext in [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".odt", ".ods"])


def clamp(valor, minimo=0, maximo=100):
    return max(minimo, min(maximo, valor))


def resposta(classe, score, deve_vasculhar=False, tipo_pista="", sinais=None, motivo=""):
    return {
        "classe": classe,
        "score_peneira": clamp(score),
        "deve_vasculhar": bool(deve_vasculhar),
        "tipo_pista": tipo_pista,
        "motivo": motivo,
        "sinais": sinais or {},
    }


def peneirar_item(texto, link=""):
    base = normalizar(f"{texto} {link}")

    cultura = contar_termos(base, TERMOS_CULTURA_AMPLA)
    linguagens = contar_termos(base, TERMOS_LINGUAGENS_ARTISTICAS)
    fomento = contar_termos(base, TERMOS_FOMENTO_ESTRUTURAL)
    oportunidade = contar_termos(base, TERMOS_OPORTUNIDADE_REAL)
    edital = contar_termos(base, TERMOS_EDITAL)
    audiovisual_direto = contar_termos(base, TERMOS_AUDIOVISUAL_DIRETO)
    audiovisual_indireto = contar_termos(base, TERMOS_AUDIOVISUAL_INDIRETO)
    licitacao = contar_termos(base, TERMOS_LICITACAO)
    licitacao_av = contar_termos(base, TERMOS_LICITACAO_AUDIOVISUAL)
    noticia = contar_termos(base, TERMOS_NOTICIA)
    resultado = contar_termos(base, TERMOS_RESULTADO)
    institucional_fraco = contar_termos(base, TERMOS_INSTITUCIONAL_FRACO)
    ruido_forte = contar_termos(base, TERMOS_RUIDO_FORTE)
    compras_genericas = contar_termos(base, TERMOS_RUIDO_COMPRAS_GENERICAS)

    relevante_dom = dominio_relevante(link)
    documento = eh_doc(link)
    pdf = eh_pdf(link)

    sinais = {
        "cultura": cultura,
        "linguagens_artisticas": linguagens,
        "fomento": fomento,
        "oportunidade": oportunidade,
        "edital": edital,
        "audiovisual_direto": audiovisual_direto,
        "audiovisual_indireto": audiovisual_indireto,
        "licitacao": licitacao,
        "licitacao_audiovisual": licitacao_av,
        "noticia": noticia,
        "resultado": resultado,
        "institucional_fraco": institucional_fraco,
        "ruido_forte": ruido_forte,
        "compras_genericas": compras_genericas,
        "dominio_relevante": int(relevante_dom),
        "documento": int(documento),
        "pdf": int(pdf),
    }

    tem_cultura = cultura > 0 or linguagens > 0
    tem_fomento = fomento > 0
    tem_oportunidade = oportunidade > 0
    tem_edital = edital > 0
    tem_audiovisual = audiovisual_direto > 0 or audiovisual_indireto > 0
    tem_licitacao = licitacao > 0
    tem_licitacao_av = licitacao_av > 0
    tem_noticia = noticia > 0
    tem_resultado = resultado > 0

    score = 0
    score += min(cultura * 6, 18)
    score += min(linguagens * 5, 15)
    score += min(fomento * 12, 30)
    score += min(oportunidade * 12, 36)
    score += min(edital * 14, 30)
    score += min(audiovisual_direto * 14, 34)
    score += min(audiovisual_indireto * 7, 18)
    score += min(licitacao * 8, 16)
    score += min(licitacao_av * 18, 36)
    score += min(noticia * 3, 9)

    if relevante_dom:
        score += 15

    if documento and (relevante_dom or tem_audiovisual or tem_cultura or tem_fomento):
        score += 8

    if compras_genericas > 0 and not tem_licitacao_av:
        score -= 35

    if ruido_forte > 0:
        score -= 60

    if tem_resultado:
        score -= 10

    if institucional_fraco > 0:
        score -= 15

    score = clamp(score)

    if ruido_forte > 0:
        return resposta("descartar", score, False, "ruido_forte", sinais, "Ruído técnico forte.")

    if compras_genericas > 0 and tem_licitacao and not tem_licitacao_av:
        return resposta("descartar", score, False, "licitacao_generica", sinais, "Licitação genérica sem sinal audiovisual.")

    if tem_licitacao and tem_licitacao_av:
        return resposta("licitacao", max(score, 60), True, "licitacao_audiovisual", sinais, "Licitação audiovisual detectada.")

    if tem_licitacao and (tem_audiovisual or relevante_dom):
        return resposta("revisao", max(score, 45), True, "licitacao_possivel", sinais, "Licitação possivelmente relevante.")

    if tem_edital and (tem_audiovisual or tem_cultura or tem_fomento):
        return resposta("edital", max(score, 65), True, "edital_detectado", sinais, "Edital/chamada com contexto relevante.")

    if tem_oportunidade and tem_audiovisual:
        return resposta("oportunidade", max(score, 62), True, "oportunidade_audiovisual", sinais, "Oportunidade audiovisual.")

    if tem_oportunidade and (tem_cultura or tem_fomento) and score >= 45:
        return resposta("oportunidade", max(score, 55), True, "oportunidade_cultural", sinais, "Oportunidade cultural/fomento.")

    if tem_fomento and (tem_cultura or tem_audiovisual or relevante_dom):
        return resposta("fonte_contexto", max(score, 50), True, "mecanismo_de_fomento", sinais, "Mecanismo/fonte de fomento.")

    if tem_noticia and tem_audiovisual and not tem_oportunidade:
        return resposta("noticia", max(score, 40), True, "noticia_audiovisual", sinais, "Notícia audiovisual.")

    if tem_noticia and tem_cultura and not tem_oportunidade:
        return resposta("noticia", max(score, 35), True, "noticia_cultural", sinais, "Notícia cultural.")

    if tem_resultado and (tem_audiovisual or tem_cultura or relevante_dom):
        return resposta("fonte_contexto", max(score, 35), True, "historico_de_edital", sinais, "Histórico útil de edital/fomentador.")

    if institucional_fraco > 0 and relevante_dom:
        return resposta("fonte_contexto", max(score, 30), True, "dominio_relevante_contexto", sinais, "Página institucional fraca, mas domínio relevante.")

    if relevante_dom and (tem_audiovisual or tem_cultura or documento):
        return resposta("fonte_contexto", max(score, 35), True, "dominio_relevante", sinais, "Domínio relevante com sinal útil.")

    if score >= 40:
        return resposta("revisao", score, True, "score_medio", sinais, "Sinal médio; revisar.")

    if tem_cultura or tem_audiovisual or tem_fomento:
        return resposta("revisao", max(score, 25), True, "sinal_fraco", sinais, "Sinal fraco, mas relacionado ao campo.")

    return resposta("descartar", score, False, "sem_sinal_util", sinais, "Sem sinal útil.")


def classificar_item(texto, link=""):
    return peneirar_item(texto, link).get("classe", "descartar")


def score_peneira(texto, link=""):
    return peneirar_item(texto, link).get("score_peneira", 0)


def deve_vasculhar(texto, link=""):
    return peneirar_item(texto, link).get("deve_vasculhar", False)


def tipo_pista(texto, link=""):
    return peneirar_item(texto, link).get("tipo_pista", "")
