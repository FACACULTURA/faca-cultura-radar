
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
            "secult-mg", "fcs", "belotur", "bdmg cultural",
        ],
    },
    "brasil": {
        "brasil": [
            "brasil", "brazil", "nacional", "ancine", "minc",
            "funarte", "spcine", "riofilme", "pnab",
        ],
    },
    "latam": {
        "america_latina": [
            "latin america", "latam", "américa latina",
            "ibermedia", "ventana sur",
        ],
    },
    "internacional": {
        "global": [
            "international", "global", "open call", "submission",
            "grant", "fund", "residency", "lab", "market",
            "pitching", "co-production",
        ],
    },
    "mercado_audiovisual": {
        "audiovisual": [
            "cinema", "audiovisual", "film", "filme", "documentary",
            "documentário", "series", "série", "tv", "streaming",
            "curta", "curta-metragem", "longa", "longa-metragem",
            "festival", "mostra", "mercado", "pitch", "coprodução",
        ],
        "animacao": [
            "animação", "animacao", "animation", "animated",
            "animated series", "série animada", "series",
            "infantil", "infantojuvenil", "kids", "children",
            "kids content", "children content", "family audience",
            "personagem", "character", "character design",
            "storyboard", "roteiro", "script", "screenplay",
            "desenvolvimento", "development", "animation lab",
            "audiovisual", "cinema", "film", "festival", "mostra",
            "lab", "laboratory", "pitching", "market",
            "coproduction", "co-production",
        ],
        "roteiro": [
            "roteiro", "screenplay", "script",
            "screenwriting", "development", "desenvolvimento",
            "sala de roteiro", "writers room", "laboratório de roteiro",
        ],
    },
    "formatos": {
        "oportunidade": [
            "edital", "chamada", "chamada pública", "open call",
            "call for projects", "call for entries", "inscrição",
            "submission", "submissions", "grant", "fund",
            "lab", "laboratory", "residency", "fellowship",
            "pitching", "market", "festival", "mostra",
            "prêmio", "award", "competition",
        ],
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
        item.get("titulo"),
        item.get("resumo"),
        item.get("descricao_original"),
        item.get("descricao"),
        item.get("conteudo"),
        item.get("texto"),
        item.get("instituicao"),
        item.get("fonte"),
        item.get("origem"),
        item.get("cidade"),
        item.get("estado"),
        item.get("pais"),
        " ".join(item.get("tags") or []),
        " ".join(item.get("oferta") or []),
    ]

    return normalizar(" ".join([str(p) for p in partes if p]))


def detectar_camadas(consulta):
    consulta_norm = normalizar(consulta)
    termos = set(tokens(consulta_norm))
    camadas = defaultdict(list)

    for camada, grupos in CAMADAS_SEMANTICAS.items():
        for grupo, palavras in grupos.items():
            for palavra in palavras:
                if normalizar(palavra) in consulta_norm:
                    if grupo not in camadas[camada]:
                        camadas[camada].append(grupo)
                    termos.update(palavras)

    if any(t in consulta_norm for t in ["animação", "animacao", "animation", "animated"]):
        if "animacao" not in camadas["mercado_audiovisual"]:
            camadas["mercado_audiovisual"].append("animacao")

        termos.update(CAMADAS_SEMANTICAS["mercado_audiovisual"]["animacao"])
        termos.update(CAMADAS_SEMANTICAS["formatos"]["oportunidade"])

    if any(t in consulta_norm for t in ["cinema", "filme", "audiovisual"]):
        if "audiovisual" not in camadas["mercado_audiovisual"]:
            camadas["mercado_audiovisual"].append("audiovisual")

        termos.update(CAMADAS_SEMANTICAS["mercado_audiovisual"]["audiovisual"])
        termos.update(CAMADAS_SEMANTICAS["formatos"]["oportunidade"])

    if any(t in consulta_norm for t in ["roteiro", "script", "screenplay"]):
        if "roteiro" not in camadas["mercado_audiovisual"]:
            camadas["mercado_audiovisual"].append("roteiro")

        termos.update(CAMADAS_SEMANTICAS["mercado_audiovisual"]["roteiro"])
        termos.update(CAMADAS_SEMANTICAS["formatos"]["oportunidade"])

    if any(t in consulta_norm for t in ["minas", "mg", "belo horizonte", "bh"]):
        if "minas" not in camadas["regional"]:
            camadas["regional"].append("minas")

        termos.update(CAMADAS_SEMANTICAS["regional"]["minas"])

    if any(t in consulta_norm for t in ["brasil", "brazil", "nacional"]):
        if "brasil" not in camadas["brasil"]:
            camadas["brasil"].append("brasil")

        termos.update(CAMADAS_SEMANTICAS["brasil"]["brasil"])

    if any(t in consulta_norm for t in ["internacional", "global", "mundial", "international"]):
        if "global" not in camadas["internacional"]:
            camadas["internacional"].append("global")

        termos.update(CAMADAS_SEMANTICAS["internacional"]["global"])
        termos.update(CAMADAS_SEMANTICAS["formatos"]["oportunidade"])

    if any(t in consulta_norm for t in ["latam", "américa latina", "america latina", "ibero"]):
        if "america_latina" not in camadas["latam"]:
            camadas["latam"].append("america_latina")

        termos.update(CAMADAS_SEMANTICAS["latam"]["america_latina"])
        termos.update(CAMADAS_SEMANTICAS["formatos"]["oportunidade"])

    return sorted(termos), dict(camadas)


def calcular_score_item(item, termos):
    texto = texto_item(item)
    score = 0

    for termo in termos:
        termo_norm = normalizar(termo)
        if termo_norm and termo_norm in texto:
            score += 10

    tipo = item.get("tipo_item") or item.get("tipo") or item.get("produto")
    tipo = normalizar(tipo)

    if tipo in ["edital", "oportunidade", "licitacao", "licitação"]:
        score += 10

    if item.get("status_prazo") in ["aberto", "quase_fechando"]:
        score += 10

    if item.get("prazo"):
        score += 5

    if item.get("link") or item.get("url"):
        score += 5

    if item.get("score"):
        try:
            score += min(float(item.get("score") or 0), 100) * 0.2
        except Exception:
            pass

    return round(score, 2)


def extrair_fonte(item):
    return (
        item.get("instituicao")
        or item.get("fonte")
        or item.get("origem")
        or item.get("link")
        or item.get("url")
        or "desconhecida"
    )


def carregar_base():
    historico = carregar_json(HISTORICO_FILE)
    feed = carregar_json(FEED_FILE)

    if historico or feed:
        return historico + feed, "historico/feed"

    print("⚠️ Sem histórico/feed → usando CSV bruto")

    csv_path = BASE_DIR / "output" / "oportunidades.csv"
    base = []

    if csv_path.exists():
        import csv
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            base = list(reader)

    return base, "csv_bruto"


def montar_bolha(consulta_usuario):
    base, origem_base = carregar_base()
    termos, camadas = detectar_camadas(consulta_usuario)

    itens_relevantes = []
    fontes = Counter()
    fontes_por_score = defaultdict(float)
    tipos = Counter()
    paises = Counter()
    estados = Counter()
    termos_fortes = Counter()

    for item in base:
        score = calcular_score_item(item, termos)

        if score <= 0:
            continue

        item_bolha = dict(item)
        item_bolha["score_bolha"] = score

        itens_relevantes.append(item_bolha)

        fonte = extrair_fonte(item)
        fontes[fonte] += 1
        fontes_por_score[fonte] += score

        tipo = item.get("tipo_item") or item.get("tipo") or item.get("produto")
        if tipo:
            tipos[tipo] += 1

        if item.get("pais"):
            paises[item.get("pais")] += 1

        if item.get("estado"):
            estados[item.get("estado")] += 1

        texto = texto_item(item)
        for termo in termos:
            termo_norm = normalizar(termo)
            if termo_norm and termo_norm in texto:
                termos_fortes[termo] += 1

    itens_relevantes = sorted(
        itens_relevantes,
        key=lambda x: x.get("score_bolha", 0),
        reverse=True
    )

    fontes_prioritarias = []
    for fonte, qtd in fontes.most_common(40):
        fontes_prioritarias.append({
            "fonte": fonte,
            "ocorrencias": qtd,
            "score_total": round(fontes_por_score[fonte], 2),
            "score_medio": round(fontes_por_score[fonte] / max(qtd, 1), 2),
        })

    bolha = {
        "consulta_usuario": consulta_usuario,
        "origem_base": origem_base,
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "termos_expandidos": termos,
        "camadas_detectadas": camadas,
        "fontes_prioritarias": fontes_prioritarias,
        "tipos_frequentes": dict(tipos.most_common(20)),
        "paises_frequentes": dict(paises.most_common(20)),
        "estados_frequentes": dict(estados.most_common(20)),
        "termos_mais_fortes": dict(termos_fortes.most_common(40)),
        "itens_relevantes": itens_relevantes[:150],
        "total_itens_analisados": len(base),
        "total_itens_relevantes": len(itens_relevantes),
    }

    salvar_json(BOLHA_FILE, bolha)

    print("✅ Bolha semântica gerada")
    print(f"Consulta: {consulta_usuario}")
    print(f"Base usada: {origem_base}")
    print(f"Itens analisados: {len(base)}")
    print(f"Itens relevantes: {len(itens_relevantes)}")
    print(f"Fontes prioritárias: {len(fontes_prioritarias)}")
    print(f"Arquivo: {BOLHA_FILE}")

    print("\n🔥 TOP 10 RESULTADOS:")
    for i, item in enumerate(itens_relevantes[:10], start=1):
        titulo = (
            item.get("titulo_principal")
            or item.get("titulo")
            or item.get("titulo_original")
            or "Sem título"
        )
        score = item.get("score_bolha")
        fonte = extrair_fonte(item)
        print(f"{i}. [{score}] {titulo} — {fonte}")

    return bolha


if __name__ == "__main__":
    consulta = input("Digite a consulta do usuário: ")
    montar_bolha(consulta)
