def classificar_tipo(titulo, link=""):
    base = f"{titulo} {link}".lower()

    if any(t in base for t in [
        "estágio", "estagio", "vaga", "job", "trabalhe conosco",
        "career", "carreira", "seleção de estagiários", "selecao de estagiarios"
    ]):
        return "trabalho"

    mapa = {
        "edital": [
            "edital",
            "chamada pública",
            "chamada publica",
            "call",
            "call for entries",
            "call for proposals",
            "open call",
            "submissions",
            "inscrições",
            "inscricoes",
            "applications open",
            "inscrições abertas",
            "inscricoes abertas",
            "submission deadline",
        ],

        "grant": [
            "grant",
            "grants",
            "funding",
            "financial support",
            "fomento",
            "apoio financeiro",
            "fund",
            "financing",
            "cofinancing",
            "support scheme",
        ],

        "festival": [
            "festival",
            "film festival",
            "fest",
            "cine",
            "festival de cinema",
        ],

        "mostra": [
            "mostra",
            "screening",
            "exibição",
            "exibicao",
            "screenings",
        ],

        "mercado": [
            "market",
            "industry",
            "coproduction",
            "co-production",
            "forum",
            "industry days",
            "film market",
            "co-production market",
            "coproduction market",
        ],

        "lab": [
            "lab",
            "laboratory",
            "laboratório",
            "laboratorio",
            "mentoria",
            "mentorship",
            "development program",
            "writers room",
            "script lab",
        ],

        "formacao": [
            "curso",
            "capacitação",
            "capacitacao",
            "oficina",
            "workshop",
            "training",
            "academy",
            "masterclass",
            "seminário",
            "seminario",
            "program",
        ],

        "premio": [
            "award",
            "prize",
            "prêmio",
            "premio",
        ],

        "residencia": [
            "residency",
            "residencies",
            "residência",
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

    if "film" in base or "cinema" in base:
        return "festival"

    return "outro"