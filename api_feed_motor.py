from flask import Flask, jsonify, request
import json
from pathlib import Path
from duckduckgo_search import DDGS

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
FEED_PATH = BASE_DIR / "output" / "feed.json"


def carregar_feed_motor():
    """
    Lê o feed final gerado pelo motor.

    Aceita:
    1) lista direta: [ {...}, {...} ]
    2) objeto agrupado: { meta, oportunidades, editais, noticias, licitacoes }
    """

    if not FEED_PATH.exists():
        return {
            "meta": {},
            "oportunidades": [],
            "editais": [],
            "noticias": [],
            "licitacoes": []
        }

    with open(FEED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        agrupado = {
            "meta": {"total": len(data)},
            "oportunidades": [],
            "editais": [],
            "noticias": [],
            "licitacoes": []
        }

        for item in data:
            categoria = classificar_categoria(item)
            agrupado[categoria].append(item)

        return agrupado

    if isinstance(data, dict):
        return {
            "meta": data.get("meta", {}),
            "oportunidades": data.get("oportunidades", []),
            "editais": data.get("editais", []),
            "noticias": data.get("noticias", []),
            "licitacoes": data.get("licitacoes", [])
        }

    return {
        "meta": {},
        "oportunidades": [],
        "editais": [],
        "noticias": [],
        "licitacoes": []
    }


def texto_item(item):
    partes = [
        str(item.get("titulo") or ""),
        str(item.get("title") or ""),
        str(item.get("titulo_principal") or ""),
        str(item.get("titulo_original") or ""),
        str(item.get("resumo") or ""),
        str(item.get("snippet") or ""),
        str(item.get("descricao") or ""),
        str(item.get("descricao_original") or ""),
        str(item.get("tipo") or ""),
        str(item.get("type") or ""),
        str(item.get("tipo_item") or ""),
        str(item.get("classe") or ""),
        str(item.get("categoria") or ""),
        str(item.get("fonte") or ""),
        str(item.get("instituicao") or ""),
        str(item.get("link") or ""),
        str(item.get("url") or ""),
    ]
    return " ".join(partes).lower()


def classificar_categoria(item):
    texto = texto_item(item)

    tipo_item = (
        str(item.get("tipo_item") or "")
        or str(item.get("tipo") or "")
        or str(item.get("type") or "")
        or str(item.get("classe") or "")
    ).lower().strip()

    classe = str(item.get("classe") or "").lower().strip()

    if tipo_item in ["licitacao", "licitação"] or classe in ["licitacao", "licitação"]:
        return "licitacoes"

    if tipo_item == "edital" or classe == "edital":
        return "editais"

    if tipo_item == "noticia" or classe == "noticia":
        return "noticias"

    if tipo_item == "oportunidade" or classe == "oportunidade":
        return "oportunidades"

    chaves_licitacoes = [
        "licitação", "licitacao", "pregão", "pregao",
        "concorrência", "concorrencia", "tender", "procurement"
    ]
    if any(chave in texto for chave in chaves_licitacoes):
        return "licitacoes"

    chaves_editais = [
        "edital", "editais", "chamada pública", "chamada publica",
        "chamamento público", "chamamento publico",
        "open call", "call for entries", "call for proposals"
    ]
    if any(chave in texto for chave in chaves_editais):
        return "editais"

    chaves_noticias = [
        "notícia", "noticia", "news", "announcement", "update",
        "insights", "lançamento", "lancamento", "divulga", "anuncia"
    ]
    if any(chave in texto for chave in chaves_noticias):
        return "noticias"

    chaves_oportunidades = [
        "curso", "formação", "formacao", "workshop", "laboratório", "laboratorio",
        "grant", "fund", "fellowship", "residency", "mercado", "market",
        "pitch", "lab", "program", "programa", "mentoria", "funding"
    ]
    if any(chave in texto for chave in chaves_oportunidades):
        return "oportunidades"

    return "oportunidades"


def normalizar_item_app(item, categoria_feed):
    titulo = (
        item.get("titulo")
        or item.get("title")
        or item.get("titulo_principal")
        or item.get("titulo_original")
        or "Sem título"
    )

    resumo = (
        item.get("resumo")
        or item.get("snippet")
        or item.get("descricao")
        or item.get("categoria")
        or item.get("descricao_original")
        or ""
    )

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

    link_principal = (
        item.get("link")
        or item.get("url")
        or item.get("origem")
        or item.get("link_edital")
        or ""
    )

    score = (
        item.get("score_final")
        or item.get("score_peneira")
        or item.get("score")
        or 50
    )

    return {
        "id": item.get("id") or f"{link_principal}-{titulo}",
        "titulo": titulo,
        "resumo": resumo,
        "tipo": tipo,
        "classe": classe,
        "fonte": item.get("fonte") or item.get("instituicao") or item.get("sourceMother"),
        "pais": item.get("pais") or item.get("country"),
        "cidade": item.get("cidade"),
        "estado": item.get("estado"),
        "score": score,
        "link": link_principal,
        "prazo": item.get("prazo") or item.get("deadline"),
        "deadline": item.get("deadline") or item.get("prazo"),
        "published_at": item.get("published_at") or item.get("data_publicacao"),
        "data_publicacao": item.get("data_publicacao"),
        "categoria_feed": categoria_feed,
        "link_edital": item.get("link_edital") or item.get("link") or item.get("url"),
        "link_inscricao": item.get("link_inscricao"),
        "tags": item.get("tags") or [],
    }


def montar_feed_app(data):
    agrupado = {
        "oportunidades": [],
        "editais": [],
        "noticias": [],
        "licitacoes": []
    }

    vistos = set()

    for chave in ["oportunidades", "editais", "noticias", "licitacoes"]:
        valor = data.get(chave, [])
        if not isinstance(valor, list):
            continue

        for item in valor:
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

    return {
        "meta": data.get("meta", {}),
        "resumo": {
            "oportunidades": len(agrupado["oportunidades"]),
            "editais": len(agrupado["editais"]),
            "noticias": len(agrupado["noticias"]),
            "licitacoes": len(agrupado["licitacoes"]),
            "total": len(items),
        },
        "items": items,
        "agrupado": agrupado,
    }


@app.route("/feed", methods=["GET"])
def get_feed():
    data = carregar_feed_motor()
    return jsonify(data)


@app.route("/feed_app", methods=["GET"])
def get_feed_app():
    data = carregar_feed_motor()
    return jsonify(montar_feed_app(data))


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "fonte": "motor",
        "feed_path": str(FEED_PATH),
        "feed_exists": FEED_PATH.exists()
    })


@app.route("/search", methods=["GET"])
def search():
    """
    Busca viva continua existindo, mas não alimenta o app diretamente.
    Ela serve para pesquisa manual/radar e pode virar insumo do motor depois.
    """
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
