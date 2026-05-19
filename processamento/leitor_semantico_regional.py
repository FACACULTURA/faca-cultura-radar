from bs4 import BeautifulSoup
import re


def limpar_texto(txt):
    if not txt:
        return ""
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()


def remover_blocos_ruido(soup):
    seletores_ruido = [
        "script",
        "style",
        "noscript",
        "header",
        "footer",
        "nav",
        "aside",
        "form",
        "iframe",
        ".menu",
        ".navbar",
        ".nav",
        ".footer",
        ".sidebar",
        ".breadcrumb",
        ".breadcrumbs",
        ".cookie",
        ".cookies",
        ".share",
        ".social",
        ".widget",
        ".related",
        ".relacionados",
        ".tags",
        ".pagination",
        ".acessibilidade",
        "#menu",
        "#footer",
        "#header",
        "#sidebar",
    ]

    for seletor in seletores_ruido:
        for bloco in soup.select(seletor):
            bloco.decompose()

    return soup


def extrair_primeiro(soup, seletores):
    for seletor in seletores:
        el = soup.select_one(seletor)
        if el:
            texto = limpar_texto(el.get_text(" ", strip=True))
            if texto:
                return texto
    return ""


def extrair_titulo(soup):
    h1 = extrair_primeiro(soup, ["h1", ".titulo", ".title", ".entry-title", ".page-title"])
    title = ""

    if soup.title:
        title = limpar_texto(soup.title.get_text(" ", strip=True))

    return h1 or title


def extrair_subtitulo(soup):
    return extrair_primeiro(
        soup,
        [
            "h2",
            ".subtitulo",
            ".subtitle",
            ".lead",
            ".summary",
            ".resumo",
            ".linha-fina",
            ".description",
        ],
    )


def encontrar_bloco_principal(soup):
    candidatos = []

    seletores = [
        "main",
        "article",
        ".content",
        ".conteudo",
        ".main-content",
        ".entry-content",
        ".post-content",
        ".news-content",
        ".corpo",
        ".texto",
        ".materia",
        ".page-content",
    ]

    for seletor in seletores:
        for el in soup.select(seletor):
            texto = limpar_texto(el.get_text(" ", strip=True))
            if len(texto) > 120:
                candidatos.append((len(texto), texto))

    if candidatos:
        candidatos.sort(reverse=True, key=lambda x: x[0])
        return candidatos[0][1]

    body = soup.body or soup
    texto = limpar_texto(body.get_text(" ", strip=True))
    return texto


def extrair_primeiro_paragrafo(soup):
    for p in soup.find_all("p"):
        texto = limpar_texto(p.get_text(" ", strip=True))
        if len(texto) > 60:
            return texto
    return ""


def leitura_por_regiao_semantica(html):
    """
    Recebe HTML bruto.
    Devolve núcleo editorial limpo, com pesos semânticos.
    """

    if not html:
        return {
            "titulo": "",
            "subtitulo": "",
            "primeiro_paragrafo": "",
            "bloco_principal": "",
            "texto_semantico": "",
            "texto_completo_limpo": "",
        }

    soup = BeautifulSoup(html, "html.parser")
    soup = remover_blocos_ruido(soup)

    titulo = extrair_titulo(soup)
    subtitulo = extrair_subtitulo(soup)
    primeiro_paragrafo = extrair_primeiro_paragrafo(soup)
    bloco_principal = encontrar_bloco_principal(soup)

    partes_pesadas = []

    if titulo:
        partes_pesadas.extend([titulo] * 5)

    if subtitulo:
        partes_pesadas.extend([subtitulo] * 3)

    if primeiro_paragrafo:
        partes_pesadas.extend([primeiro_paragrafo] * 3)

    if bloco_principal:
        partes_pesadas.append(bloco_principal[:5000])

    texto_semantico = limpar_texto(" ".join(partes_pesadas))
    texto_completo_limpo = limpar_texto(soup.get_text(" ", strip=True))

    return {
        "titulo": titulo,
        "subtitulo": subtitulo,
        "primeiro_paragrafo": primeiro_paragrafo,
        "bloco_principal": bloco_principal,
        "texto_semantico": texto_semantico,
        "texto_completo_limpo": texto_completo_limpo,
    }