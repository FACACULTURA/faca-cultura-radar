import json
import re
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"

HISTORICO_FILE = OUTPUT_DIR / "historico.json"
FEED_FILE = OUTPUT_DIR / "feed.json"
BOLHA_FILE = OUTPUT_DIR / "bolha_semantica.json"


CAMADAS_SEMANTICAS = {
    "regional": {
        "minas": [
            "minas", "minas gerais", "mg", "belo horizonte", "bh",
            "secult-mg", "secult mg", "fcs", "fundação clóvis salgado",
            "belotur", "filme em minas", "bdmg cultural",
        ],
    },

    "brasil": {
        "brasil": [
            "brasil", "brazil", "brasileiro", "brasileira", "nacional",
            "minc", "ministerio da cultura", "ministério da cultura",
            "ancine", "funarte", "sesc", "sesc", "spcine", "riofilme",
            "pnab", "lei paulo gustavo", "rouanet", "fsa",
            "fundo setorial do audiovisual",
        ],
    },

    "latam": {
        "america_latina": [
            "latin america", "latam", "américa latina", "iberoamérica",
            "iberoamerica", "mercosur", "mercosul", "ibermedia",
            "cinelatino", "ficg", "ventana sur", "sanfic", "bafici",
            "guadalajara", "cartagena", "ficci",
        ],
    },

    "internacional": {
        "global": [
            "international", "global", "worldwide", "world cinema",
            "global south", "open call", "call for projects",
            "call for entries", "submission", "submissions",
            "grant", "fund", "film fund", "development fund",
            "production fund", "post-production fund",
            "residency", "fellowship", "lab", "laboratory",
            "market", "pitching", "pitch forum", "co-production",
            "coproduction", "co-production market",
            "talent campus", "workshop",
        ],
        "europa": [
            "europe", "european", "creative europe", "eurimages",
            "berlinale talents", "idfa", "rotterdam", "cannes",
            "venice", "locarno", "sheffield docfest",
        ],
        "eua": [
            "usa", "united states", "sundance", "tribeca",
            "film independent", "ifp", "gotham", "sxsw",
        ],
        "africa_asia": [
            "africa", "asian", "asia", "marrakech", "doha",
            "red sea", "busan", "tokyo", "hong kong",
        ],
    },

    "mercado_audiovisual": {
        "audiovisual": [
            "audiovisual", "cinema", "film", "filmmaking",
            "curta", "short film", "longa", "feature film",
            "documentário", "documentary", "doc",
            "ficção", "fiction", "series", "série", "tv",
            "streaming", "webseries", "new media",
        ],
        "animacao": [
            "animação", "animacao", "animation", "animated",
            "animated series", "kids content", "children content",
            "family audience", "young audience", "infantil",
            "infantojuvenil", "personagem", "character design",
            "storyboard", "animation lab",
        ],
        "roteiro": [
            "roteiro", "screenplay", "script", "screenwriting",
            "script development", "development", "sala de roteiro",
            "writers room", "screenwriting lab", "story development",
        ],
        "producao": [
            "produção", "production", "development", "financing",
            "distribution", "sales agent", "film market",
            "industry program", "project market",
        ],
    },

    "formatos_oportunidade": {
        "formatos": [
            "edital", "chamada", "chamada pública", "open call",
            "call", "call for projects", "call for entries",
            "inscrição", "submission", "submissions",
            "grant", "fund", "fellowship", "residency",
            "lab", "laboratory", "workshop", "mentorship",
            "pitching", "market", "festival", "mostra",
            "prêmio", "award", "competition", "incubator",
            "accelerator", "coproduction", "co-production",
            "licitação", "procurement", "public tender",
        ],
    },

    "idiomas": {
        "portugues": ["português", "portugues", "brazil", "brasil"],
        "ingles": ["english", "international", "global", "open call"],
        "espanhol": ["spanish", "español", "latam", "iberoamerica"],
        "frances": ["french", "français", "francophone"],
    },
}


def carregar_json(caminho):
    if not caminho.exists():
        return []
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def normalizar(texto):
    return str(texto or "").lower().strip()


def tokens(texto):
    texto = normalizar(texto)
    texto = re.sub(r"[^a-záàâãéèêíïóôõöúçñ0-9\s/-]", " ", texto)
    return [p for p in texto.split() if len(p) >= 4]


def texto_item(item):
    partes = [
        item.get("titulo_principal"),
        item.get("titulo_original"),
        item.get("resumo"),
        item.get("descricao_original"),
        item.get("instituicao"),
        item.get("fonte"),
        item.get("cidade"),
        item.get("estado"),
        item.get("pais"),
        " ".join(item.get("tags") or []),
        " ".join(item.get("oferta") or []),
    ]
    return normalizar(" ".join([str(p) for p in partes if p]))


def detectar_camadas(consulta):
    consulta_norm = normalizar(consulta)
    camadas_detectadas = defaultdict(list)
    termos = set(tokens(consulta_norm))

    for camada, grupos in CAMADAS_SEMANTICAS.items():
        for grupo, palavras in grupos.items():
            for palavra in palavras:
                if normalizar(palavra) in consulta_norm:
                    camadas_detectadas[camada].append(grupo)
                    termos.update(palavras)

    if any(t in consulta_norm for t in ["animação", "animacao", "animation"]):
        termos.update(CAMADAS_SEMANTICAS["mercado_audiovisual"]["animacao"])

    if any(t in consulta_norm for t in ["roteiro", "script", "screenplay"]):
        termos.update(CAMADAS_SEMANTICAS["mercado_audiovisual"]["roteiro"])

    if any(t in consulta_norm for t in ["cinema", "filme", "audiovisual"]):
        termos.update(CAMADAS_SEMANTICAS["mercado_audiovisual"]["audiovisual"])
        termos.update(CAMADAS_SEMANTICAS["formatos_oportunidade"]["formatos"])

    if any(t in consulta_norm for t in ["minas", "mg", "belo horizonte", "bh"]):
        termos.update(CAMADAS_SEMANTICAS["regional"]["minas"])

    if any(t in consulta_norm for t in ["internacional", "global", "mundial", "fora do brasil"]):
        termos.update(CAMADAS_SEMANTICAS["internacional"]["global"])
        termos.update(CAMADAS_SEMANTICAS["idiomas"]["ingles"])

    if any(t in consulta_norm for t in ["latam", "américa latina", "america latina", "ibero"]):
        termos.update(CAMADAS_SEMANTICAS["latam"]["america_latina"])
        termos.update(CAMADAS_SEMANTICAS["idiomas"]["espanhol"])

    return sorted(termos), dict(camadas_detectadas)


def calcular_score_item(item, termos_expandidos):
    texto = texto_item(item)
    score = 0

    for termo in termos_expandidos:
        termo_norm = normalizar(termo)
        if termo_norm and termo_norm in texto:
            score += 10

    if item.get("tipo_item") in ["edital", "oportunidade", "licitacao"]:
        score += 10

    if item.get("status_prazo") in ["aberto", "quase_fechando"]:
        score += 15

    if item.get("cor_status") == "verde":
        score += 8

    if item.get("cor_status") == "amarelo":
        score += 5

    if item.get("instituicao"):
        score += 5

    if item.get("prazo"):
        score += 5

    if item.get("score"):
        try:
            score += min(float(item.get("score") or 0), 100) * 0.2
        except Exception:
            pass

    return round(score, 2)


def extrair_fonte(item):
    return (
        item.get("fonte")
        or item.get("instituicao")
        or item.get("origem")
        or item.get("link")
        or "fonte_desconhecida"
    )


def sugerir_idiomas(consulta, camadas_detectadas):
    consulta_norm = normalizar(consulta)
    idiomas = set(["português"])

    if "internacional" in camadas_detectadas or any(
        t in consulta_norm for t in ["global", "mundial", "international"]
    ):
        idiomas.add("inglês")

    if "latam" in camadas_detectadas or any(
        t in consulta_norm for t in ["latam", "ibero", "américa latina", "america latina"]
    ):
        idiomas.add("espanhol")

    return sorted(idiomas)


def montar_bolha(consulta_usuario, projetos_usuario=None):
    historico = carregar_json(HISTORICO_FILE)
    feed = carregar_json(FEED_FILE)

    base = historico + feed

    termos_expandidos, camadas_detectadas = detectar_camadas(consulta_usuario)
    idiomas_sugeridos = sugerir_idiomas(consulta_usuario, camadas_detectadas)

    itens_relevantes = []
    fontes_counter = Counter()
    tipos_counter = Counter()
    paises_counter = Counter()
    estados_counter = Counter()
    termos_counter = Counter()
    fontes_por_score = defaultdict(float)

    for item in base:
        score = calcular_score_item(item, termos_expandidos)

        if score <= 0:
            continue

        item_bolha = {
            **item,
            "score_bolha": score,
        }

        itens_relevantes.append(item_bolha)

        fonte = extrair_fonte(item)
        fontes_counter[fonte] += 1
        fontes_por_score[fonte] += score

        if item.get("tipo_item"):
            tipos_counter[item.get("tipo_item")] += 1

        if item.get("pais"):
            paises_counter[item.get("pais")] += 1

        if item.get("estado"):
            estados_counter[item.get("estado")] += 1

        texto = texto_item(item)
        for termo in termos_expandidos:
            if normalizar(termo) in texto:
                termos_counter[termo] += 1

    itens_relevantes = sorted(
        itens_relevantes,
        key=lambda x: x.get("score_bolha", 0),
        reverse=True,
    )

    fontes_prioritarias = []
    for fonte, qtd in fontes_counter.most_common():
        fontes_prioritarias.append({
            "fonte": fonte,
            "ocorrencias": qtd,
            "score_total": round(fontes_por_score[fonte], 2),
            "score_medio": round(fontes_por_score[fonte] / max(qtd, 1), 2),
        })

    bolha = {
        "consulta_usuario": consulta_usuario,
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "camadas_detectadas": camadas_detectadas,
        "idiomas_sugeridos": idiomas_sugeridos,
        "termos_expandidos": termos_expandidos,
        "fontes_prioritarias": fontes_prioritarias[:40],
        "tipos_frequentes": dict(tipos_counter.most_common(20)),
        "paises_frequentes": dict(paises_counter.most_common(20)),
        "estados_frequentes": dict(estados_counter.most_common(20)),
        "termos_mais_fortes": dict(termos_counter.most_common(40)),
        "itens_relevantes": itens_relevantes[:150],
        "total_itens_analisados": len(base),
        "total_itens_relevantes": len(itens_relevantes),
    }

    salvar_json(BOLHA_FILE, bolha)

    print("✅ Bolha semântica gerada")
    print(f"Consulta: {consulta_usuario}")
    print(f"Itens analisados: {len(base)}")
    print(f"Itens relevantes: {len(itens_relevantes)}")
    print(f"Fontes prioritárias: {len(fontes_prioritarias)}")
    print(f"Idiomas sugeridos: {', '.join(idiomas_sugeridos)}")
    print(f"Arquivo: {BOLHA_FILE}")

    return bolha


if __name__ == "__main__":
    consulta = input("Digite a consulta do usuário: ")
    montar_bolha(consulta)