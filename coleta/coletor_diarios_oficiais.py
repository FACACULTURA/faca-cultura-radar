import json
import re
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent.parent
FONTES_PATH = BASE_DIR / "data" / "input" / "fontes_diarios_oficiais.json"
SAIDA_PATH = BASE_DIR / "output" / "diarios_oficiais.csv"


TERMOS_FORTES = [
    "aviso de seleção",
    "seleção de projetos",
    "edital",
    "chamada pública",
    "chamamento público",
    "licitação",
    "pregão",
    "contratação",
    "audiovisual",
    "cinema",
    "vídeo",
    "video",
    "produção cultural",
    "setor cultural",
    "secult",
    "fundação cultural",
    "termo de fomento",
    "termo de colaboração",
]


def carregar_fontes():
    if not FONTES_PATH.exists():
        print(f"Arquivo não encontrado: {FONTES_PATH}")
        return []

    with open(FONTES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def limpar_texto(txt):
    return re.sub(r"\s+", " ", str(txt or "")).strip()


def contem_termo_forte(texto):
    texto = texto.lower()
    return any(t in texto for t in TERMOS_FORTES)


def coletar_links_da_fonte(fonte):
    url = fonte["url"]

    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
    except Exception as e:
        print(f"Erro ao acessar {url}: {e}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    links = []

    for a in soup.find_all("a", href=True):
        texto = limpar_texto(a.get_text())
        href = a.get("href")

        if not href:
            continue

        if href.startswith("/"):
            base = url.rstrip("/")
            href = base + href

        bruto = f"{texto} {href}"

        if contem_termo_forte(bruto) or ".pdf" in href.lower():
            links.append({
                "fonte": fonte["nome"],
                "estado": fonte.get("estado"),
                "cidade": fonte.get("cidade"),
                "tipo_fonte": fonte.get("tipo"),
                "titulo": texto or fonte["nome"],
                "link": href,
                "origem": url,
                "classe": "fonte_contexto",
                "tipo": "diario_oficial",
                "categoria": "cultura",
                "data_coleta": datetime.now().isoformat(),
            })

    return links


def executar_coleta_diarios():
    fontes = carregar_fontes()

    todos = []

    for fonte in fontes:
        print(f"🔎 Lendo diário oficial: {fonte['nome']}")
        itens = coletar_links_da_fonte(fonte)
        print(f"   encontrados: {len(itens)}")
        todos.extend(itens)

    SAIDA_PATH.parent.mkdir(parents=True, exist_ok=True)

    if todos:
        import pandas as pd
        pd.DataFrame(todos).to_csv(SAIDA_PATH, index=False, encoding="utf-8")
        print(f"✅ CSV salvo em: {SAIDA_PATH}")
    else:
        print("⚠️ Nenhum item encontrado.")

    return todos


if __name__ == "__main__":
    executar_coleta_diarios()