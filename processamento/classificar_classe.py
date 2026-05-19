def classificar_classe(titulo, link="", tipo="", score=0):
    base = f"{titulo} {link}".lower()

    termos_noticia = [
        "notícia",
        "noticia",
        "news",
        "anuncia",
        "anunciado",
        "anunciada",
        "lança",
        "lançamento",
        "resultado",
        "resultados",
        "divulga",
        "publica",
        "publicado",
        "publicada",
        "estreia",
        "programação",
        "programacao",
        "informa",
        "debate",
        "evento realizado",
        "foi realizado",
        "promove ações",
        "promove acoes",
        "celebra",
        "premiação",
        "premiacao",
        "homenagem",
    ]

    if tipo == "trabalho":
        return "noticia"

    # notícia só vale se NÃO parecer oportunidade explícita
    if any(t in base for t in termos_noticia) and not any(t in base for t in TERMOS_OPORTUNIDADE):
        return "noticia"

    tipos_fortes = {"edital", "grant", "lab", "residencia", "pitching", "mercado"}
    tipos_ambiguos = {"festival", "mostra", "formacao", "premio", "bolsa"}

    if tipo in tipos_fortes:
        return "oportunidade"

    if tipo in tipos_ambiguos and score >= 65:
        return "oportunidade"

    if score >= 80:
        return "oportunidade"

    return "indefinido"