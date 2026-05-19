import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

# =========================
# CONFIG
# =========================

SCORE_MINIMO_DESCOBERTA = 8
SCORE_MINIMO_CURADORIA = 12

LIMITE_TOTAL_POR_DOMINIO = 8
LIMITE_FONTES_MAE_POR_ENTIDADE = 2
LIMITE_PROGRAMAS_POR_ENTIDADE = 4
LIMITE_APOIO_POR_ENTIDADE = 3

NEGATIVOS_FORTES = [
    "tutorial",
    "inscricao",
    "inscrições",
    "resultado",
    "resultado final",
    "formulario",
    "formulário",
    "videoaula",
    "vídeo aula",
    "como fazer",
    "como elaborar",
    "como preencher",
    "leia mais",
    "detalhada",
    "pagina",
    "página",
    "home",
    "inicio",
    "início",
    "membership",
    "protocol",
    "documentos",
    "sei",
    "newsletter",
    "privacy",
    "cookie",
    "press",
    "media",
    "contact",
    "login",
    "search",
    "noticia",
    "notícias",
    "news",
    "post",
    "blog",
    "acervo",
    "lista de titulos",
    "lista de títulos",
    "governo anuncia",
    "processo seletivo simplificado",
]

NEGATIVOS_URL = [
    "/noticia",
    "/noticias",
    "/news",
    "/post",
    "/blog",
    "/acervo",
    "/search",
    "/tag/",
    "/author/",
    "/privacy",
    "/cookie",
    "/login",
    "/newsletter",
]

PALAVRAS_FONTE_FORTE = [
    "fund",
    "fundo",
    "funding",
    "grant",
    "grants",
    "agency",
    "instituto",
    "institute",
    "commission",
    "film commission",
    "festival",
    "lab",
    "labs",
    "residency",
    "market",
    "coproduction",
    "co-production",
    "coproducao",
    "coprodução",
    "screen",
    "cinema",
    "audiovisual",
    "ministry",
    "ministerio",
    "ministério",
    "secretaria",
    "fundacao",
    "fundação",
    "board",
    "council",
    "program",
    "programme",
    "apply",
    "applications",
    "call",
    "open call",
]

TERMOS_FONTE_MAE = [
    "agency",
    "instituto",
    "institute",
    "ministry",
    "ministerio",
    "ministério",
    "commission",
    "screen",
    "secretaria",
    "fundacao",
    "fundação",
    "board",
    "council",
    "film institute",
    "film agency",
    "arts council",
    "national film",
    "film board",
    "fundo",
    "fund",
]

TERMOS_PROGRAMA = [
    "funding",
    "grant",
    "grants",
    "apply",
    "application",
    "applications",
    "fellowship",
    "fellowships",
    "lab",
    "labs",
    "residency",
    "market",
    "call",
    "open call",
    "program",
    "programme",
    "qumra",
    "audience testing",
    "submissions",
    "submission",
    "funding opportunities",
    "microprojeto",
    "microprojetos",
    "edital",
    "convocatoria",
]

TERMOS_APOIO = [
    "updates",
    "what’s happening",
    "what's happening",
    "calendar",
    "programme ebook",
    "program ebook",
    "view programme",
    "view program",
    "festival 2025",
    "festival 2026",
    "assets",
    "profile",
    "profiles",
    "learn more",
    "saiba mais",
]

TRADUCOES_SIMPLES = {
    "film fund": "fundo de cinema",
    "audiovisual fund": "fundo audiovisual",
    "film agency": "agencia de cinema",
    "film commission": "film commission",
    "film institute": "instituto de cinema",
    "cinema institute": "instituto de cinema",
    "open call": "chamada aberta",
    "call for entries": "chamada para inscricoes",
    "call for applications": "chamada para inscricoes",
    "funding": "financiamento",
    "grants": "bolsas e apoios",
    "grant": "bolsa ou apoio",
    "festival": "festival",
    "film festival": "festival de cinema",
    "lab": "laboratorio",
    "labs": "laboratorios",
    "residency": "residencia",
    "market": "mercado",
    "development": "desenvolvimento",
    "production": "producao",
    "co-production": "coproducao",
    "coproduction": "coproducao",
    "documentary": "documentario",
    "animation": "animacao",
    "short film": "curta-metragem",
    "feature film": "longa-metragem",
    "industry": "industria",
    "screen institute": "instituto audiovisual",
    "arts council": "conselho de artes",
    "ministry of culture": "ministerio da cultura",
    "programs": "programas",
    "fellowships": "bolsas",
    "apply": "inscricoes",
}

REGIAO_OVERRIDE = {
    "dohafilminstitute.com": "Oriente Medio",
    "showmethefund.co": "Internacional",
    "redseafilmfest.com": "Oriente Medio",
    "iksv.org": "Turquia",
    "trt.net.tr": "Turquia",
    "creativebc.com": "America do Norte",
    "telefilm.ca": "America do Norte",
    "canadacouncil.ca": "America do Norte",
    "nfb.ca": "America do Norte",
    "sodec.gouv.qc.ca": "America do Norte",
    "ontariocreates.ca": "America do Norte",
    "nzfilm.co.nz": "Oceania",
    "docedge.nz": "Oceania",
    "miff.com.au": "Oceania",
    "screenaustralia.gov.au": "Oceania",
    "nfvf.co.za": "Africa",
    "realness.institute": "Africa",
    "durbanfilmmart.co.za": "Africa",
    "fespaco.org": "Africa",
    "fespaco.bf": "Africa",
    "marrakech-festival.com": "Africa",
    "programaibermedia.com": "America Latina",
    "imcine.gob.mx": "America Latina",
    "incaa.gob.ar": "America Latina",
    "proimagenescolombia.com": "America Latina",
    "bogotamarket.com": "America Latina",
    "sanfic.com": "America Latina",
    "sundance.org": "America do Norte",
    "festival.sundance.org": "America do Norte",
    "filmindependent.org": "America do Norte",
    "tribecafilm.com": "America do Norte",
    "sffilm.org": "America do Norte",
    "catapultfilmfund.org": "America do Norte",
    "chickeneggfilms.org": "America do Norte",
    "firelightmedia.org": "America do Norte",
    "itvs.org": "America do Norte",
    "jeromefdn.org": "America do Norte",
    "cinereach.org": "America do Norte",
    "pointsnorthinstitute.org": "America do Norte",
    "coe.int": "Europa",
    "filmfreeway.com": "Internacional",
    "fdcp.ph": "Asia",
    "nfdcindia.com": "Asia",
}


CORRECOES_SEED_URL = {
    "https://www.eurimages.coe.int": "https://www.coe.int/en/web/eurimages",
    "https://eurimages.coe.int": "https://www.coe.int/en/web/eurimages",
    "https://www.coe.int/en/web/eurimages": "https://www.coe.int/en/web/eurimages",
    "https://www.festivalmarrakech.info": "https://marrakech-festival.com/",
    "https://festivalmarrakech.info": "https://marrakech-festival.com/",
    "https://www.asianfilmcommissions.org": "https://fdcp.ph/",
    "https://asianfilmcommissions.org": "https://fdcp.ph/",
    "https://www.sundance.org": "https://festival.sundance.org/",
    "https://sundance.org": "https://festival.sundance.org/",
    "https://www.aen.pr.gov.br/Cultura": "https://www.cultura.pr.gov.br/",
    "https://www.cultura.pr.gov.br": "https://www.cultura.pr.gov.br/",
    "https://paraiba.pb.gov.br/diretas/secretaria-de-estado-da-cultura": "https://paraiba.pb.gov.br/diretas/secretaria-da-cultura",
    "https://www.firelightmedia.org": "https://firelightmedia.tv",
    "https://firelightmedia.org": "https://firelightmedia.tv",
    "https://fespaco.org": "https://fespaco.bf",
    "https://www.fespaco.org": "https://fespaco.bf",
}

TIMEOUTS_DOMINIO = {
    "cultura.df.gov.br": 30,
    "cultura.pe.gov.br": 30,
    "secult.mg.gov.br": 25,
    "fcc.sc.gov.br": 25,
    "coe.int": 25,
    "marrakech-festival.com": 25,
    "durbanfilmmart.co.za": 25,
    "filmfreeway.com": 20,
    "showmethefund.co": 20,
    "festival.sundance.org": 25,
    "nfdcindia.com": 25,
}

# =========================
# UTILITÁRIOS
# =========================

def carregar_seeds(caminho="fontes_semente.json"):
    path = Path(caminho)
    if not path.exists():
        return {"fontes": []}

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)



def corrigir_seed_url(url):
    if not url:
        return url
    bruto = url.strip()
    sem_barra = bruto.rstrip("/")
    return CORRECOES_SEED_URL.get(bruto, CORRECOES_SEED_URL.get(sem_barra, bruto))


def limpar_texto(texto):
    return re.sub(r"\s+", " ", texto or "").strip()


def traduzir_para_portugues(texto):
    if not texto:
        return ""

    saida = texto
    texto_lower = texto.lower()

    for origem, destino in TRADUCOES_SIMPLES.items():
        if origem in texto_lower:
            pattern = re.compile(re.escape(origem), re.IGNORECASE)
            saida = pattern.sub(destino, saida)

    return saida


def link_absoluto(base, href):
    if not href:
        return None
    return urljoin(base, href)


def dominio(url):
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def normalizar_fonte(url):
    try:
        parsed = urlparse(url)
        dom = parsed.netloc.lower().replace("www.", "")
        path = [p for p in parsed.path.strip("/").split("/") if p]

        ignorados = {
            "pt-br", "pt", "en", "es", "fr", "de", "it", "tr", "jp",
            "inicio", "home", "index"
        }

        if "gov.br" in dom:
            if path:
                primeiro = path[0].lower()
                if primeiro not in ignorados and len(primeiro) > 2:
                    return f"https://{dom}/{primeiro}"
            return f"https://{dom}"

        if "prefeitura" in dom:
            if path:
                primeiro = path[0].lower()
                if primeiro not in ignorados and len(primeiro) > 2:
                    return f"https://{dom}/{primeiro}"

        return f"https://{dom}"

    except Exception:
        return url


def chave_entidade(url):
    try:
        return normalizar_fonte(url).replace("https://", "").replace("http://", "").strip("/").lower()
    except Exception:
        return (url or "").strip("/").lower()


def nome_canonico_fonte(url, titulo_site="", texto_link=""):
    url_lower = (url or "").lower()

    nomes_especiais = {
        "gov.br/ancine": "ANCINE",
        "gov.br/cultura": "MinC",
        "gov.br/ctav": "CTAV",
        "spcine.com.br": "SPCine",
        "riofilme.com.br": "RioFilme",
        "secult.mg.gov.br": "Secult MG",
        "cultura.pe.gov.br": "Secult PE",
        "ba.gov.br/cultura": "Secult BA",
        "secult.ce.gov.br": "Secult CE",
        "cultura.rs.gov.br": "Sedac RS",
        "fcc.sc.gov.br": "Fundação Catarinense de Cultura",
        "secult.es.gov.br": "Secult ES",
        "cultura.df.gov.br": "Secec DF",
        "goias.gov.br/cultura": "Secult GO",
        "cultura.am.gov.br": "Secult AM",
        "secult.pa.gov.br": "Secult PA",
        "cultura.rn.gov.br": "Secult RN",
        "programaibermedia.com": "Ibermedia",
        "berlinale-talents.de": "Berlinale Talents",
        "torinofilmlab.it": "TorinoFilmLab",
        "sundance.org": "Sundance",
        "festival.sundance.org": "Sundance Festival",
        "dohafilminstitute.com": "Doha Film Institute",
        "europeanfilmagencies.eu": "EFAD",
        "coe.int": "Eurimages",
        "filmfreeway.com": "FilmFreeway",
        "showmethefund.co": "Show Me The Fund",
        "telefilm.ca": "Telefilm Canada",
        "screenaustralia.gov.au": "Screen Australia",
        "nzfilm.co.nz": "New Zealand Film Commission",
        "biff.kr": "Busan International Film Festival",
        "fdcp.ph": "FDCP Philippines",
        "nfdcindia.com": "NFDC India",
        "jpf.go.jp": "Japan Foundation",
        "nfvf.co.za": "NFVF",
        "durbanfilmmart.co.za": "Durban FilmMart",
        "realness.institute": "Realness Institute",
        "fespaco.org": "FESPACO",
        "fespaco.bf": "FESPACO",
        "redseafilmfest.com": "Red Sea Film Festival",
        "iksv.org": "IKSV",
        "trt.net.tr": "TRT",
        "bfi.org.uk": "BFI",
        "cnc.fr": "CNC",
        "vaf.be": "VAF",
        "sodec.gouv.qc.ca": "SODEC",
        "filmindependent.org": "Film Independent",
        "tribecafilm.com": "Tribeca",
        "nfb.ca": "National Film Board of Canada",
        "incaa.gob.ar": "INCAA",
        "imcine.gob.mx": "IMCINE",
        "catapultfilmfund.org": "Catapult Film Fund",
        "chickeneggfilms.org": "Chicken & Egg Films",
        "firelightmedia.org": "Firelight Media",
        "firelightmedia.tv": "Firelight Media",
        "itvs.org": "ITVS",
        "jeromefdn.org": "Jerome Foundation",
        "cinereach.org": "Cinereach",
        "pointsnorthinstitute.org": "Points North Institute",
        "sffilm.org": "SFFILM",
        "proimagenescolombia.com": "Proimágenes Colombia",
        "bogotamarket.com": "BAM Colombia",
        "sanfic.com": "SANFIC",
        "miff.com.au": "MIFF",
        "docedge.nz": "Doc Edge",
        "marrakech-festival.com": "Marrakech Festival",
    }

    for chave, nome in nomes_especiais.items():
        if chave in url_lower:
            return nome

    termos_ruins = {
        "home", "about", "members", "projects", "dashboard",
        "our partners", "our members", "accessibility statement",
        "accept all cookies", "cookie settings", "inicio", "membership",
        "protocol", "documentos", "sei", "search", "media",
        "press", "contact", "login",
    }

    for candidato in [titulo_site, texto_link]:
        if candidato:
            t = candidato.strip()
            if t and t.lower() not in termos_ruins and len(t) > 4:
                return traduzir_para_portugues(t)

    return dominio(url)


# =========================
# ACESSO ROBUSTO
# =========================

def fetch_url(url, timeout=15, tentativas=3):
    ultimo_erro = None
    url = corrigir_seed_url(url)

    candidatos = [url]
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme or "https"
        netloc = parsed.netloc
        path = parsed.path or ""
        query = f"?{parsed.query}" if parsed.query else ""

        if netloc.startswith("www."):
            candidatos.append(f"{scheme}://{netloc[4:]}{path}{query}")
        else:
            candidatos.append(f"{scheme}://www.{netloc}{path}{query}")
    except Exception:
        pass

    vistos = set()
    candidatos = [u for u in candidatos if not (u in vistos or vistos.add(u))]

    for tentativa_url in candidatos:
        dom = dominio(tentativa_url)
        timeout_real = TIMEOUTS_DOMINIO.get(dom, timeout)

        for _ in range(tentativas):
            try:
                resp = requests.get(
                    tentativa_url,
                    headers=HEADERS,
                    timeout=timeout_real,
                    verify=False,
                    allow_redirects=True,
                )
                resp.encoding = resp.apparent_encoding
                return resp
            except requests.exceptions.SSLError as e:
                ultimo_erro = f"[SSL ERROR] {tentativa_url} | {e}"
            except requests.exceptions.ConnectionError as e:
                ultimo_erro = f"[CONNECTION ERROR] {tentativa_url} | {e}"
            except requests.exceptions.Timeout as e:
                ultimo_erro = f"[TIMEOUT] {tentativa_url} | {e}"
            except Exception as e:
                ultimo_erro = f"[ERRO GERAL] {tentativa_url} | {e}"

    if ultimo_erro:
        print(ultimo_erro)
    return None


# =========================
# FILTROS
# =========================

def texto_link_valido(texto):
    if not texto:
        return False

    texto = texto.strip()
    if len(texto) < 3:
        return False

    lixo = [
        "home", "menu", "login", "contact", "privacy", "cookies",
        "search", "newsletter", "read more", "about",
        "skip to main content", "cookie settings",
        "learn more", "saiba mais",
    ]

    return texto.lower() not in lixo


def url_candidata_valida(url):
    if not url:
        return False

    u = url.lower()

    if any(x in u for x in NEGATIVOS_URL):
        return False

    if u.startswith("javascript:") or u.startswith("mailto:"):
        return False

    return True


def lixo_institucional(texto, url):
    base = f"{texto} {url}".lower()
    return any(x in base for x in NEGATIVOS_FORTES)


# =========================
# SCORE / CLASSIFICAÇÃO
# =========================

def score_fonte(texto, url):
    base = f"{texto} {url}".lower()
    score = 0

    for termo in PALAVRAS_FONTE_FORTE:
        if termo in base:
            score += 4

    if any(x in url for x in [".gov", ".gov.br", ".org", ".eu"]):
        score += 3

    if "list" in base or "directory" in base or "members" in base:
        score += 3

    for neg in NEGATIVOS_FORTES:
        if neg in base:
            score -= 6

    return score


def score_fonte_mae(item):
    base = f"{item['nome']} {item['url']} {item['tipo']}".lower()
    url = item["url"].lower().rstrip("/")
    url_norm = normalizar_fonte(url).lower().rstrip("/")

    score = 0

    if item["tipo"] in ["agencia", "film_commission", "organizacao_publica"]:
        score += 5

    if item["tipo"] == "fundo":
        score += 3

    if any(t in base for t in [
        "film commission", "council", "institute", "instituto", "cinema",
        "audiovisual", "ministry", "ministerio", "ministério",
        "secretaria", "cultura", "screen", "fund", "fundo", "board"
    ]):
        score += 3

    if url == url_norm:
        score += 4
    elif url.count("/") <= 6:
        score += 2

    if any(t in base for t in [
        "apply", "application", "applications", "grant", "grants",
        "lab", "labs", "residency", "calendar", "events",
        "programme", "program", "market", "festival 202", "ebook",
        "updates", "what's happening", "what’s happening",
        "view programme", "view program", "submissions", "submission", "qumra",
    ]):
        score -= 3

    return score


def classificar_tipo(texto, url):
    base = f"{texto} {url}".lower()

    if any(x in base for x in ["film fund", "audiovisual fund", "funding", "fonds", "grant", "grants", "fondo", "fundo"]):
        return "fundo"
    if any(x in base for x in ["film agency", "institute", "instituto", "screen institute", "arts council", "board", "council"]):
        return "agencia"
    if "film commission" in base:
        return "film_commission"
    if "festival" in base:
        return "festival"
    if any(x in base for x in ["lab", "residency", "labs"]):
        return "lab"
    if "market" in base:
        return "mercado"
    if any(x in base for x in ["secretaria", "cultura", "fundacao", "fundação", "ministry", "ministerio", "ministério"]):
        return "organizacao_publica"
    return "organizacao"


def classificar_grupo(nome, url, tipo):
    item_fake = {"nome": nome, "url": url, "tipo": tipo}
    base = f"{nome} {url} {tipo}".lower()
    url_low = url.lower()

    if "filmfreeway.com" in url_low or "showmethefund.co" in url_low:
        return "paginas_apoio"

    if any(t in base for t in TERMOS_APOIO):
        return "paginas_apoio"

    score_mae = score_fonte_mae(item_fake)
    if score_mae >= 6:
        return "fontes_mae"
    if score_mae >= 3 and tipo in ["agencia", "film_commission", "organizacao_publica"]:
        return "fontes_mae"

    if any(t in base for t in TERMOS_PROGRAMA):
        return "programas"

    if tipo in ["lab", "mercado", "festival", "fundo"]:
        return "programas"

    return "paginas_apoio"

    score_mae = score_fonte_mae(item_fake)
    if score_mae >= 6:
        return "fontes_mae"
    if score_mae >= 3 and tipo in ["agencia", "film_commission", "organizacao_publica", "fundo"]:
        return "fontes_mae"

    if any(t in base for t in TERMOS_PROGRAMA):
        return "programas"

    if tipo in ["lab", "mercado", "festival", "fundo"]:
        return "programas"

    return "paginas_apoio"


def detectar_regiao(url):
    dom = dominio(url)

    for chave, regiao in REGIAO_OVERRIDE.items():
        if chave in dom:
            return regiao

    u = url.lower()

    if ".br" in u or "gov.br" in u:
        return "Brasil"
    if any(t in u for t in [".ar", ".cl", ".co", ".mx", ".uy", ".pe", ".ec"]):
        return "America Latina"
    if any(t in u for t in [".fr", ".de", ".es", ".it", ".pt", ".eu", ".be", ".nl", ".lu", ".se", ".no", ".dk", ".pl", ".uk"]):
        return "Europa"
    if any(t in u for t in [".za", ".sn", ".ma", ".tn", ".ng", ".ke"]):
        return "Africa"
    if any(t in u for t in [".qa", ".ae", ".sa", ".eg"]):
        return "Oriente Medio"
    if ".tr" in u:
        return "Turquia"
    if any(t in u for t in [".jp", ".kr", ".in", ".sg", ".hk", ".cn", ".ph"]):
        return "Asia"
    if any(t in u for t in [".au", ".nz"]):
        return "Oceania"
    if any(t in u for t in [".ca", ".us"]):
        return "America do Norte"
    return "Internacional"


# =========================
# EXTRAÇÃO
# =========================

def extrair_links(nome_seed, url_seed):
    print(f"\nExplorando: {nome_seed}")
    candidatos = []

    resp = fetch_url(url_seed)
    if not resp:
        return candidatos

    if resp.status_code != 200:
        print(f"[HTTP {resp.status_code}] {url_seed}")
        return candidatos

    try:
        soup = BeautifulSoup(resp.text, "lxml")
        links = soup.select("a[href]")

        contagem_dominio = defaultdict(int)

        for link in links:
            texto = limpar_texto(link.get_text())
            href = link.get("href")

            if not texto or not href:
                continue

            href = link_absoluto(url_seed, href)
            dom = dominio(href)

            if not url_candidata_valida(href):
                continue
            if not texto_link_valido(texto):
                continue
            if lixo_institucional(texto, href):
                continue

            score = score_fonte(texto, href)
            if score < SCORE_MINIMO_DESCOBERTA:
                continue

            contagem_dominio[dom] += 1
            if contagem_dominio[dom] > LIMITE_TOTAL_POR_DOMINIO:
                continue

            tipo = classificar_tipo(texto, href)
            grupo = classificar_grupo(texto, href, tipo)
            nome_pt = traduzir_para_portugues(texto)

            candidatos.append({
                "nome": nome_pt,
                "nome_original": texto,
                "url": href.rstrip("/"),
                "dominio": dom,
                "entidade": chave_entidade(href),
                "tipo": tipo,
                "grupo": grupo,
                "regiao": detectar_regiao(href),
                "score": score,
                "score_fonte_mae": score_fonte_mae({
                    "nome": nome_pt,
                    "url": href.rstrip("/"),
                    "tipo": tipo,
                }),
                "origem_seed": nome_seed,
            })

        print(f"{len(candidatos)} candidatos úteis")
    except Exception as e:
        print(f"[ERRO PARSE] {url_seed} | {e}")

    return candidatos


# =========================
# CURADORIA
# =========================

def chave_item(item):
    nome = limpar_texto(item["nome"]).lower().strip()
    url = item["url"].lower().strip().rstrip("/")
    return f"{nome}|{url}"


def eh_fonte_mae_forte(item):
    url = item["url"].lower()
    path = urlparse(url).path.strip("/")

    # 🔥 REGRA 1: URL raiz ou quase raiz
    if path == "" or len(path.split("/")) <= 1:
        return True

    # 🔥 REGRA 2: termos institucionais fortes
    base = f"{item['nome']} {item['tipo']}".lower()

    if any(t in base for t in TERMOS_FONTE_MAE):
        return True

    # 🔥 REGRA 3: tipo forte + caminho curto
    if item["tipo"] in ["agencia", "film_commission", "organizacao_publica"]:
        if len(path.split("/")) <= 2:
            return True

    return False

def eh_programa_forte(item):
    base = f"{item['nome']} {item['url']} {item['tipo']}".lower()
    url = item["url"].lower()
    path = urlparse(url).path.strip("/")

    termos_programa = [
        "fund", "funding", "grant", "grants",
        "program", "programme", "programs", "programmes",
        "apply", "application", "call", "deadline",
        "submission", "submissions",
        "lab", "labs", "residency",
        "market", "festival", "competition",
        "training", "workshop",
        "convocatoria", "edital"
    ]

    termos_genericos = [
        "home", "about", "learn more", "read more",
        "see more", "updates", "portal",
        "what's happening", "what’s happening",
        "profile", "profiles", "ebook",
        "cookie", "privacy", "contact", "login"
    ]

    if any(t in base for t in termos_genericos):
        return False

    if path == "":
        return False

    if any(t in base for t in termos_programa):
        return True

    if item["tipo"] in ["lab", "mercado", "festival"]:
        return True

    if any(t in path for t in [
        "fund", "funding", "grant", "program", "programme",
        "apply", "festival", "market", "lab", "residency",
        "call", "submission", "training"
    ]):
        return True

    return False


def curar_fontes(candidatos):
    agrupados = defaultdict(list)
    for c in candidatos:
        agrupados[c["entidade"]].append(c)

    fontes_mae = []
    programas = []
    paginas_apoio = []

    for entidade, itens in agrupados.items():
        itens_unicos = []
        vistos = set()

        for item in sorted(itens, key=lambda x: (x.get("score_fonte_mae", 0), x["score"]), reverse=True):
            ch = chave_item(item)
            if ch in vistos:
                continue
            vistos.add(ch)
            itens_unicos.append(item)

        fontes_entidade = []
        programas_entidade = []
        apoio_entidade = []

        for item in itens_unicos:
            if item["score"] < SCORE_MINIMO_CURADORIA:
                continue

            if item["grupo"] == "fontes_mae" and eh_fonte_mae_forte(item):
                fontes_entidade.append(item)
            elif item["grupo"] == "programas" and eh_programa_forte(item):
                programas_entidade.append(item)
            else:
                apoio_entidade.append(item)

        fontes_mae.extend(fontes_entidade[:LIMITE_FONTES_MAE_POR_ENTIDADE])
        programas.extend(programas_entidade[:LIMITE_PROGRAMAS_POR_ENTIDADE])
        paginas_apoio.extend(apoio_entidade[:LIMITE_APOIO_POR_ENTIDADE])

    def dedup(lista):
        final = []
        vistos = set()
        for item in lista:
            ch = chave_item(item)
            if ch in vistos:
                continue
            vistos.add(ch)
            final.append(item)
        return final

    # segunda passada: sobe apoios com cara forte de programa
    apoio_reclassificado = []
    programas_extra = []

    for item in paginas_apoio:
        base = f"{item['nome']} {item['url']}".lower()
        path = urlparse(item["url"]).path.strip("/").lower()

        if any(t in base for t in [
            "program", "programme", "programs", "programmes",
            "fund", "funding", "grant", "grants",
            "festival", "lab", "labs", "market",
            "residency", "call", "submission", "edital", "convocatoria"
        ]):
            programas_extra.append(item)
        elif any(t in path for t in [
            "program", "programme", "fund", "funding",
            "festival", "lab", "market", "residency"
        ]):
            programas_extra.append(item)
        else:
            apoio_reclassificado.append(item)

    fontes_mae = dedup(fontes_mae)
    programas = dedup(programas + programas_extra)
    paginas_apoio = dedup(apoio_reclassificado)

    return fontes_mae, programas, paginas_apoio


# =========================
# SEEDS
# =========================

def seeds_brasil():
    return [
        ("ANCINE", "https://www.gov.br/ancine/pt-br"),
        ("MinC", "https://www.gov.br/cultura/pt-br"),
        ("CTAV", "https://www.gov.br/ctav/pt-br"),
        ("SPCine", "https://spcine.com.br"),
        ("RioFilme", "https://riofilme.com.br"),
        ("Secult MG", "https://www.secult.mg.gov.br"),
        ("FMC BH", "https://prefeitura.pbh.gov.br/fundacao-municipal-de-cultura"),
        ("Secult PE", "https://www.cultura.pe.gov.br"),
        ("Secult BA", "https://www.ba.gov.br/cultura"),
        ("Secult CE", "https://www.secult.ce.gov.br"),
        ("Sedac RS", "https://cultura.rs.gov.br"),
        ("FCC SC", "https://www.fcc.sc.gov.br"),
        ("Secult ES", "https://secult.es.gov.br"),
        ("Secec DF", "https://www.cultura.df.gov.br"),
        ("Secult GO", "https://www.goias.gov.br/cultura"),
        ("Secult AM", "https://www.cultura.am.gov.br"),
        ("Secult PA", "https://www.secult.pa.gov.br"),
        ("Secult PB", "https://paraiba.pb.gov.br/diretas/secretaria-da-cultura"),
        ("Secult RN", "https://cultura.rn.gov.br"),
        ("Cultura PR", "https://www.cultura.pr.gov.br/"),
    ]


def seeds_usa():
    return [
        ("Sundance", "https://festival.sundance.org/"),
        ("Film Independent", "https://www.filmindependent.org"),
        ("Tribeca", "https://tribecafilm.com"),
        ("SFFILM", "https://www.sffilm.org"),
        ("Catapult Film Fund", "https://catapultfilmfund.org"),
        ("Chicken & Egg Films", "https://chickeneggfilms.org"),
        ("Firelight Media", "https://firelightmedia.tv"),
        ("ITVS", "https://itvs.org"),
        ("Jerome Foundation", "https://www.jeromefdn.org"),
        ("Cinereach", "https://www.cinereach.org"),
        ("Points North Institute", "https://pointsnorthinstitute.org"),
        ("FilmFreeway", "https://filmfreeway.com/"),
        ("Show Me The Fund", "https://showmethefund.co/"),
    ]


def seeds_canada():
    return [
        ("Telefilm Canada", "https://telefilm.ca"),
        ("NFB", "https://www.nfb.ca"),
        ("SODEC", "https://sodec.gouv.qc.ca"),
        ("Canada Council", "https://canadacouncil.ca"),
        ("Ontario Creates", "https://ontariocreates.ca"),
        ("Creative BC", "https://creativebc.com"),
    ]


def seeds_latam():
    return [
        ("Ibermedia", "https://www.programaibermedia.com"),
        ("IMCINE", "https://www.imcine.gob.mx"),
        ("INCAA", "https://www.incaa.gob.ar"),
        ("Proimágenes Colombia", "https://www.proimagenescolombia.com"),
        ("BAM Colombia", "https://www.bogotamarket.com"),
        ("SANFIC", "https://sanfic.com"),
    ]


def seeds_europa():
    return [
        ("EFAD", "https://www.europeanfilmagencies.eu"),
        ("Eurimages", "https://www.coe.int/en/web/eurimages"),
        ("TorinoFilmLab", "https://www.torinofilmlab.it"),
        ("Berlinale Talents", "https://www.berlinale-talents.de"),
        ("BFI", "https://www.bfi.org.uk"),
        ("CNC", "https://www.cnc.fr"),
        ("Film Fund Luxembourg", "https://www.filmfund.lu"),
        ("VAF", "https://www.vaf.be"),
        ("EFM Berlinale", "https://www.efm-berlinale.de"),
    ]


def seeds_africa():
    return [
        ("NFVF", "https://www.nfvf.co.za"),
        ("Durban FilmMart", "https://durbanfilmmart.co.za"),
        ("Realness Institute", "https://www.realness.institute"),
        ("FESPACO", "https://fespaco.bf"),
        ("Marrakech", "https://marrakech-festival.com/"),
    ]


def seeds_asia():
    return [
        ("Busan IFF", "https://www.biff.kr"),
        ("FDCP Philippines", "https://fdcp.ph/"),
        ("NFDC India", "https://www.nfdcindia.com"),
        ("Japan Foundation", "https://www.jpf.go.jp"),
        ("UniJapan", "https://www.unijapan.org"),
    ]


def seeds_oriente_medio_turquia():
    return [
        ("Doha Film Institute", "https://www.dohafilminstitute.com"),
        ("Red Sea Film Festival", "https://redseafilmfest.com"),
        ("IKSV", "https://www.iksv.org"),
        ("TRT", "https://www.trt.net.tr"),
    ]


def seeds_oceania():
    return [
        ("Screen Australia", "https://www.screenaustralia.gov.au"),
        ("NZ Film Commission", "https://www.nzfilm.co.nz"),
        ("MIFF", "https://miff.com.au"),
        ("Doc Edge", "https://docedge.nz"),
    ]


# =========================
# PIPELINE
# =========================

def executar():
    seeds_custom = []
    arquivo_seeds = Path("fontes_semente.json")

    if arquivo_seeds.exists():
        dados = carregar_seeds("fontes_semente.json")
        for item in dados.get("fontes", []):
            nome = item.get("nome")
            url = item.get("url")
            if nome and url:
                seeds_custom.append((nome, corrigir_seed_url(url)))

    print(f"Seeds custom carregadas: {len(seeds_custom)}")

    seeds = (
        seeds_custom
        + seeds_brasil()
        + seeds_usa()
        + seeds_canada()
        + seeds_latam()
        + seeds_europa()
        + seeds_africa()
        + seeds_asia()
        + seeds_oriente_medio_turquia()
        + seeds_oceania()
    )

    seeds = [(nome, corrigir_seed_url(url)) for nome, url in seeds]

    todos = []
    for nome, url in seeds:
        todos.extend(extrair_links(nome, url))

    print(f"\nTotal bruto: {len(todos)}")

    fontes_mae, programas, paginas_apoio = curar_fontes(todos)

    print(f"\nTotal FINAL (curado): {len(fontes_mae) + len(programas) + len(paginas_apoio)}")
    print(f"Fontes-mãe: {len(fontes_mae)}")
    print(f"Programas: {len(programas)}")
    print(f"Páginas de apoio: {len(paginas_apoio)}\n")

    print("=== FONTES-MÃE ===")
    for f in fontes_mae:
        print(
            f"- {f['nome']} | {f['url']} | {f['tipo']} | {f['regiao']} | "
            f"score={f['score']} | score_fonte_mae={f['score_fonte_mae']}"
        )

    print("\n=== PROGRAMAS ===")
    for p in programas:
        print(f"- {p['nome']} | {p['url']} | {p['tipo']} | {p['regiao']} | score={p['score']}")

    print("\n=== PÁGINAS DE APOIO ===")
    for a in paginas_apoio:
        print(f"- {a['nome']} | {a['url']} | {a['tipo']} | {a['regiao']} | score={a['score']}")

    with open("candidatos_amplos.json", "w", encoding="utf-8") as f:
        json.dump({"candidatos_amplos": todos}, f, ensure_ascii=False, indent=2)

    with open("fontes_mae.json", "w", encoding="utf-8") as f:
        json.dump({"fontes_mae": fontes_mae}, f, ensure_ascii=False, indent=2)

    with open("programas.json", "w", encoding="utf-8") as f:
        json.dump({"programas": programas}, f, ensure_ascii=False, indent=2)

    with open("paginas_apoio.json", "w", encoding="utf-8") as f:
        json.dump({"paginas_apoio": paginas_apoio}, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    executar()
