from flask import Flask, jsonify, request
import json
from pathlib import Path
from duckduckgo_search import DDGS

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
FEED_PATH = BASE_DIR / "output" / "feed.json"


def texto_item(item):
    partes = [
        str(item.get("titulo") or ""),
        str(item.get("titulo_principal") or ""),
        str(item.get("titulo_original") or ""),
        str(item.get("resumo") or ""),
        str(item.get("descricao_original") or ""),
        str(item.get("tipo") or ""),
        str(item.get("tipo_item") or ""),
        str(item.get("classe") or ""),
        str(item.get("categoria") or ""),
        str(item.get("fonte") or ""),
    ]
    return " ".join(partes).lower()


def classificar_categoria(item):
    texto = texto_item(item)

    chaves_licitacoes = [
        "licitação", "licitacao", "pregão", "pregao",
        "concorrência", "concorrencia", "tender", "procurement"
    ]
    if any(chave in texto for chave in chaves_licitacoes):
        return "licitacoes"

    chaves_editais = [
        "edital", "editais", "chamada pública", "chamada publica",
        "open call", "call for entries", "call for proposals"
    ]
    if any(chave in texto for chave in chaves_editais):
        return "editais"

    chaves_noticias = [
        "notícia", "noticia", "news", "announcement", "update", "insights", "lançamento",
    ]
    if any(chave in texto for chave in chaves_noticias):
        return "noticias"

    chaves_oportunidades = [
        "curso", "formação", "formacao", "workshop", "laboratório", "laboratorio",
        "grant", "fund", "fellowship", "residency", "mercado", "market",
        "pitch", "lab", "program", "programa", "mentoria"
    ]
    if any(chave in texto for chave in chaves_oportunidades):
        return "oportunidades"

    classe = str(item.get("classe") or "").lower().strip()
    if classe == "noticia":
        return "noticias"
    if classe == "oportunidade":
        return "oportunidades"

    return "oportunidades"


def normalizar_item_app(item, categoria_feed):
    titulo = (
        item.get("titulo")
        or item.get("titulo_principal")
        or item.get("titulo_original")
        or "Sem título"
    )

    resumo = (
        item.get("resumo")
        or item.get("categoria")
        or item.get("descricao_original")
        or ""
    )

    # força consistência com a categoria final
    if categoria_feed == "editais":
        tipo = "edital"
        classe = "edital"

    elif categoria_feed == "licitacoes":
        tipo = "licitacao"
        classe = "licitacao"

    elif categoria_feed == "oportunidades":
        tipo = "oportunidade"
        classe = "oportunidade"

    else:
        tipo = "noticia"
        classe = "noticia"

    link_principal = item.get("link") or item.get("origem") or ""

    score = item.get("score_final", item.get("score", 0))
    if not score:
        score = 50

    return {
        "id": item.get("id") or f"{link_principal}-{titulo}",
        "titulo": titulo,
        "resumo": resumo,
        "tipo": tipo,
        "classe": classe,
        "fonte": item.get("fonte"),
        "pais": item.get("pais"),
        "score": score,
        "link": link_principal,
        "prazo": item.get("prazo"),
        "categoria_feed": categoria_feed,
        "link_edital": item.get("link_edital") or item.get("link"),
        "link_inscricao": item.get("link_inscricao"),
    }

@app.route("/feed", methods=["GET"])
def get_feed():
    if not FEED_PATH.exists():
        return jsonify({"error": "feed.json não encontrado"}), 404

    with open(FEED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return jsonify(data)


@app.route("/feed_app", methods=["GET"])
def get_feed_app():
    if not FEED_PATH.exists():
        return jsonify({
            "meta": {},
            "items": [],
            "agrupado": {
                "oportunidades": [],
                "editais": [],
                "noticias": [],
                "licitacoes": []
            }
        })

    with open(FEED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    agrupado = {
        "oportunidades": [],
        "editais": [],
        "noticias": [],
        "licitacoes": []
    }

    fontes_base = []
    for chave in ["oportunidades", "editais", "noticias", "licitacoes"]:
        valor = data.get(chave, [])
        if isinstance(valor, list):
            fontes_base.extend(valor)

    vistos = set()

    for item in fontes_base:
        categoria = classificar_categoria(item)
        item_normalizado = normalizar_item_app(item, categoria)

        chave_unica = f"{item_normalizado['link']}-{item_normalizado['titulo']}"
        if chave_unica in vistos:
            continue
        vistos.add(chave_unica)

        agrupado[categoria].append(item_normalizado)

    items = (
        agrupado["oportunidades"]
        + agrupado["editais"]
        + agrupado["noticias"]
        + agrupado["licitacoes"]
    )

    return jsonify({
        "meta": data.get("meta", {}),
        "resumo": {
            "oportunidades": len(agrupado["oportunidades"]),
            "editais": len(agrupado["editais"]),
            "noticias": len(agrupado["noticias"]),
            "licitacoes": len(agrupado["licitacoes"]),
        },
        "items": items,
        "agrupado": agrupado,
    })


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/search", methods=["GET"])
def search():
    q = (request.args.get("q") or "").strip()

    if not q:
        return jsonify({"results": []})

    results = []

    try:
        with DDGS() as ddgs:
            ddg_results = list(ddgs.text(q, max_results=20))

        for r in ddg_results:
            results.append({
                "title": r.get("title"),
                "url": r.get("href"),
                "sourceMother": r.get("source"),
                "snippet": r.get("body"),
                "color": "yellow",
                "score": 50,
                "signals": {
                    "is_pdf": str(r.get("href", "")).endswith(".pdf"),
                    "has_apply": False,
                    "is_official": False,
                    "is_bridge": True,
                },
            })

    except Exception as e:
        return jsonify({"results": [], "error": str(e)})

    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)