# processamento/sintetizador_titulos.py

import re


MAX_TITULO = 95


TERMOS_REMOVER = [
    "torna público",
    "torna publico",
    "secretaria municipal",
    "secretaria de cultura",
    "comissão julgadora",
    "comissao julgadora",
    "resultado preliminar",
    "resultado final",
    "diário oficial",
    "diario oficial",
    "publicação",
    "publicacao",
    "chamamento público",
    "chamamento publico",
    "processo seletivo",
    "ata da",
    "homologação",
    "homologacao",
    "retificação",
    "retificacao",
]


MAPA_PREFIXOS = {
    "edital": "Edital",
    "festival": "Festival",
    "mostra": "Mostra",
    "laboratório": "Laboratório",
    "laboratorio": "Laboratório",
    "residência": "Residência",
    "residencia": "Residência",
    "bolsa": "Bolsa",
    "mercado": "Mercado",
    "pitching": "Pitching",
    "rodada": "Rodada",
    "licitação": "Licitação",
    "licitacao": "Licitação",
    "notícia": "Notícia",
    "noticia": "Notícia",
    "resultado": "Resultado",
}


def limpar_texto(txt):

    txt = str(txt or "")

    txt = re.sub(r"\s+", " ", txt)

    return txt.strip()


def detectar_prefixo(item, titulo):

    base = f"""
    {titulo}
    {item.get('classe', '')}
    {item.get('tipo', '')}
    """

    base = base.lower()

    for termo, prefixo in MAPA_PREFIXOS.items():

        if termo in base:
            return prefixo

    return None


def remover_ruido(titulo):

    t = titulo

    for termo in TERMOS_REMOVER:

        t = re.sub(
            termo,
            "",
            t,
            flags=re.IGNORECASE
        )

    t = re.sub(r"\s+", " ", t)

    t = t.strip(" -–|:")

    return t.strip()


def reduzir_tamanho(txt, limite=MAX_TITULO):

    if len(txt) <= limite:
        return txt

    corte = txt[:limite]

    if " " in corte:
        corte = corte.rsplit(" ", 1)[0]

    return corte.strip() + "..."


def sintetizar_titulo_item(item):

    titulo_original = limpar_texto(
        item.get("titulo", "")
    )

    if not titulo_original:
        return item

    titulo_limpo = remover_ruido(
        titulo_original
    )

    prefixo = detectar_prefixo(
        item,
        titulo_limpo
    )

    final = titulo_limpo

    if prefixo:

        if not titulo_limpo.lower().startswith(
            prefixo.lower()
        ):

            final = f"{prefixo} • {titulo_limpo}"

    final = reduzir_tamanho(final)

    item["titulo_original"] = titulo_original
    item["titulo_curado"] = final

    return item


def sintetizar_feed(feed):

    saida = []

    for item in feed:

        try:
            item = sintetizar_titulo_item(item)
        except Exception as e:
            print("⚠️ erro sintetizando título:", e)

        saida.append(item)

    return saida