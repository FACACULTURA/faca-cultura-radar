from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import json
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
RADAR_BASE_FILE = BASE_DIR / "radar_base.json"
RADAR_INGESTADO_FILE = BASE_DIR / "radar_ingestado.json"

EDITAL_TERMS = [
    "edital", "chamada", "chamamento", "convocatória", "convocatoria",
    "inscrições abertas", "inscricoes abertas", "regulamento",
    "formulário", "formulario", "pdf", "seleção", "selecao"
]

OPORTUNIDADE_TERMS = [
    "open call", "grant", "grants", "fund", "funding", "fellowship",
    "residency", "lab", "laboratório", "laboratorio", "market",
    "pitching", "development", "workshop", "program", "programme",
    "application", "apply", "festival", "mostra", "videoarte"
]

NOTICIA_TERMS = [
    "notícia", "noticia", "news", "matéria", "materia", "reportagem",
    "abriu inscrições", "abre inscrições", "abre inscricoes", "abriu inscricoes"
]

LICITACAO_TERMS = [
    "licitação", "licitacao", "pregão", "pregao", "concorrência",
    "concorrencia", "tomada de preços", "tomada de precos",
    "contratação", "contratacao", "compras públicas", "compras publicas"
]

NEGATIVE_TERMS = [
    "opinião", "opiniao", "blog", "artigo"
]

OFFICIAL_HINTS = [
    ".gov.br", ".org.br", ".org", ".gov", ".edu"
]


def ensure_file(path: Path):
    if not path.exists():
        path.write_text(json.dumps({"results": []}, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json_results(path: Path) -> List[Dict[str, Any]]:
    ensure_file(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("results", [])
    except Exception:
        return []


def save_json_results(path: Path, results: List[Dict[str, Any]]):
    path.write_text(
        json.dumps({"results": results}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def get_domain(url: str):
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return None


def clean_duckduckgo_url(url: str):
    try:
        if "duckduckgo.com/l/?" in url:
            parsed = urlparse(url)
            qs = parse_qs(parsed.query)
            uddg = qs.get("uddg")
            if uddg:
                return unquote(uddg[0])
        return url
    except Exception:
        return url


def normalize_text(title: str, url: str, snippet: str = ""):
    return f"{title} {url} {snippet}".lower()


def extrair_data_do_link(url: str):
    if not url:
        return None

    padroes = [
        r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})",
        r"(20\d{2})/(\d{1,2})/",
        r"(20\d{2})",
    ]

    for padrao in padroes:
        match = re.search(padrao, url)
        if match:
            partes = match.groups()
            try:
                if len(partes) == 3:
                    ano, mes, dia = partes
                    return f"{ano}-{int(mes):02d}-{int(dia):02d}"
                if len(partes) == 2:
                    ano, mes = partes
                    return f"{ano}-{int(mes):02d}-01"
                if len(partes) == 1:
                    return f"{partes[0]}-01-01"
            except Exception:
                return None

    return None


def detectar_modo_oportunidade(item: Dict[str, Any]):
    texto = " ".join([
        str(item.get("titulo", "")),
        str(item.get("title", "")),
        str(item.get("resumo", "")),
        str(item.get("snippet", "")),
        str(item.get("descricao", "")),
        str(item.get("link", "")),
        str(item.get("url", "")),
        " ".join(item.get("tags", []) if isinstance(item.get("tags"), list) else []),
    ]).lower()

    tem_prazo = bool(item.get("prazo") or item.get("deadline"))

    termos_submissao = [
        "festival", "mostra", "call for entries", "submissão", "submission",
        "inscrição de obra", "envio de filme", "envio de projeto",
        "videoarte", "curta", "longa", "pitching", "laboratório",
        "residência", "residency", "open call"
    ]

    tem_submissao = any(t in texto for t in termos_submissao)
    return "composta" if tem_prazo and tem_submissao else "simples"


def chave_data_ordenacao(item: Dict[str, Any]):
    data = (
        item.get("prazo")
        or item.get("deadline")
        or item.get("published_at")
        or item.get("data_publicacao")
        or item.get("data_link")
        or item.get("data_detectada")
    )

    if not data:
        return datetime.max

    try:
        return datetime.fromisoformat(str(data))
    except Exception:
        return datetime.max


def infer_type(title: str, url: str, snippet: str = ""):
    text = normalize_text(title, url, snippet)

    edital_score = sum(1 for t in EDITAL_TERMS if t in text)
    oportunidade_score = sum(1 for t in OPORTUNIDADE_TERMS if t in text)
    noticia_score = sum(1 for t in NOTICIA_TERMS if t in text)
    licitacao_score = sum(1 for t in LICITACAO_TERMS if t in text)

    scores = {
        "edital": edital_score,
        "oportunidade": oportunidade_score,
        "noticia": noticia_score,
        "licitacao": licitacao_score,
    }

    best_type = max(scores, key=scores.get)
    if scores[best_type] == 0:
        return "noticia"
    return best_type


def classify_result(title: str, url: str, snippet: str = ""):
    text = normalize_text(title, url, snippet)

    positive_score = 0
    for term in EDITAL_TERMS + OPORTUNIDADE_TERMS + LICITACAO_TERMS:
        if term in text:
            positive_score += 2

    bridge_score = 0
    for term in NOTICIA_TERMS:
        if term in text:
            bridge_score += 1

    negative_score = 0
    for term in NEGATIVE_TERMS:
        if term in text:
            negative_score += 2

    is_pdf = ".pdf" in url.lower() or "pdf" in text
    has_apply = any(x in text for x in ["apply", "inscr", "formul", "regulamento"])
    is_official = any(x in url.lower() for x in OFFICIAL_HINTS)
    is_bridge = bridge_score > 0
    item_type = infer_type(title, url, snippet)

    raw_score = positive_score + bridge_score - negative_score

    if is_pdf or (is_official and has_apply):
        color = "green"
    elif item_type in ["edital", "oportunidade", "licitacao"] and raw_score >= 2:
        color = "green"
    elif is_bridge or item_type == "noticia":
        color = "yellow"
    else:
        color = "red"

    return color, raw_score, {
        "is_pdf": is_pdf,
        "has_apply": has_apply,
        "is_official": is_official,
        "is_bridge": is_bridge,
        "type": item_type,
    }


def result_priority(item: Dict[str, Any]):
    item_type = item.get("type")

    base = 0
    if item["color"] == "green" and item.get("signals", {}).get("is_pdf"):
        base = 100
    elif item["color"] == "green":
        base = 80
    elif item["color"] == "yellow":
        base = 50
    else:
        base = 10

    if item_type == "edital":
        base += 10
    elif item_type == "oportunidade":
        base += 8
    elif item_type == "licitacao":
        base += 7
    elif item_type == "noticia":
        base += 3

    return base


def dedupe_results(results: List[Dict[str, Any]]):
    seen = set()
    cleaned = []

    for item in results:
        key = (
            (item.get("url") or "").strip().lower(),
            (item.get("type") or "").strip().lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(item)

    return cleaned


def load_radar_base():
    return load_json_results(RADAR_BASE_FILE)


def load_radar_ingestado():
    return load_json_results(RADAR_INGESTADO_FILE)


def save_radar_ingestado(results: List[Dict[str, Any]]):
    save_json_results(RADAR_INGESTADO_FILE, results)


def get_radar_unificado():
    base = load_radar_base()
    ingestado = load_radar_ingestado()
    all_items = dedupe_results(base + ingestado)
    all_items.sort(key=result_priority, reverse=True)
    return all_items


def ingest_item(item: Dict[str, Any]):
    if not item.get("url"):
        return False

    current = load_radar_ingestado()
    merged = dedupe_results(current + [item])

    if len(merged) == len(current):
        return False

    save_radar_ingestado(merged)
    return True


def auto_ingest(results: List[Dict[str, Any]]):
    added = 0
    for item in results:
        if item["color"] in ["green", "yellow"]:
            enriched = {
                **item,
                "origin": "search_ingested",
            }
            if ingest_item(enriched):
                added += 1
    return added


def search_web(query: str):
    url = "https://duckduckgo.com/html/"
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, params={"q": query}, headers=headers, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for result in soup.select(".result"):
        a = result.select_one(".result__a")
        snippet_el = result.select_one(".result__snippet")

        if not a:
            continue

        title = a.get_text(" ", strip=True)
        raw_url = a.get("href")
        clean_url = clean_duckduckgo_url(raw_url)
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

        color, score, signals = classify_result(title, clean_url, snippet)
        item_type = signals["type"]

        results.append({
            "title": title,
            "url": clean_url,
            "sourceMother": get_domain(clean_url),
            "snippet": snippet,
            "color": color,
            "score": score,
            "signals": signals,
            "type": item_type,
        })

    results = dedupe_results(results)
    results.sort(key=result_priority, reverse=True)
    return results[:15]


def normalizar_item_app(item: Dict[str, Any], categoria: str) -> Dict[str, Any]:
    link = item.get("url") or item.get("link") or item.get("link_edital") or ""
    data_link = extrair_data_do_link(link)

    data_detectada = (
        item.get("deadline")
        or item.get("prazo")
        or item.get("published_at")
        or item.get("data_publicacao")
        or data_link
    )

    return {
        "id": item.get("id") or link or item.get("title") or item.get("titulo"),
        "titulo": item.get("title") or item.get("titulo") or item.get("titulo_principal") or "Sem título",
        "resumo": item.get("snippet") or item.get("resumo") or item.get("descricao") or "Sem resumo disponível.",
        "descricao": item.get("descricao") or item.get("snippet") or item.get("resumo") or "",
        "fonte": item.get("sourceMother") or item.get("fonte") or item.get("instituicao") or "",
        "pais": item.get("pais") or item.get("country") or "",
        "cidade": item.get("cidade") or "",
        "estado": item.get("estado") or "",
        "score": item.get("score") or item.get("score_final") or 50,
        "link": link,
        "link_edital": item.get("link_edital") or link,
        "link_inscricao": item.get("link_inscricao"),
        "prazo": item.get("deadline") or item.get("prazo"),
        "deadline": item.get("deadline"),
        "published_at": item.get("published_at") or item.get("data_publicacao"),
        "data_link": data_link,
        "data_detectada": data_detectada,
        "tipo": item.get("type") or item.get("tipo"),
        "classe": item.get("type") or item.get("tipo"),
        "categoria_feed": categoria,
        "tags": item.get("tags") or [],
        "modo_oportunidade": detectar_modo_oportunidade(item) if categoria == "oportunidades" else None,
    }


@app.get("/")
def root():
    return {"status": "F.Cult backend rodando"}


@app.get("/search")
def search(q: str):
    results = search_web(q)
    added = auto_ingest(results)

    return {
        "query": q,
        "ingested": added,
        "results": results
    }


@app.get("/radar")
def radar(tipo: str | None = None):
    results = get_radar_unificado()

    if tipo:
        tipo = tipo.lower().strip()
        results = [item for item in results if item.get("type") == tipo]

    return {
        "count": len(results),
        "results": results
    }


@app.post("/ingest")
def ingest(item: Dict[str, Any]):
    enriched = {
        **item,
        "origin": item.get("origin", "manual_ingest"),
    }
    ok = ingest_item(enriched)

    return {
        "status": "ok" if ok else "duplicate",
        "item": enriched
    }


@app.get("/feed")
def feed():
    items = get_radar_unificado()

    grouped = {
        "editais": [],
        "oportunidades": [],
        "noticias": [],
        "licitacoes": [],
    }

    for item in items:
        item_type = item.get("type")

        if item_type == "edital":
            grouped["editais"].append(item)
        elif item_type == "oportunidade":
            grouped["oportunidades"].append(item)
        elif item_type == "noticia":
            grouped["noticias"].append(item)
        elif item_type == "licitacao":
            grouped["licitacoes"].append(item)

    return grouped


@app.get("/feed_app")
def feed_app():
    grouped = feed()

    items = []
    agrupado_app = {
        "editais": [],
        "oportunidades": [],
        "noticias": [],
        "licitacoes": [],
    }

    for key in ["editais", "oportunidades", "noticias", "licitacoes"]:
        for item in grouped.get(key, []):
            item_normalizado = normalizar_item_app(item, key)
            items.append(item_normalizado)
            agrupado_app[key].append(item_normalizado)

    items = sorted(items, key=chave_data_ordenacao)

    for key in agrupado_app:
        agrupado_app[key] = sorted(agrupado_app[key], key=chave_data_ordenacao)

    return {
        "items": items,
        "agrupado": agrupado_app,
        "resumo": {
            "editais": len(agrupado_app.get("editais", [])),
            "oportunidades": len(agrupado_app.get("oportunidades", [])),
            "noticias": len(agrupado_app.get("noticias", [])),
            "licitacoes": len(agrupado_app.get("licitacoes", [])),
            "total": len(items),
        },
    }


if __name__ == "__main__":
    print("🚀 Subindo API...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
