# validador_final.py
# F.CULT — Validador Final
# Decide: FEED, REVISÃO ou DESCARTE antes de gerar o feed.json

import json
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "output"

INPUT_FILE = DATA_DIR / "oportunidades_brutas.json"
FEED_FILE = DATA_DIR / "feed_aprovado.json"
REVISAO_FILE = DATA_DIR / "revisao_humana.json"
DESCARTE_FILE = DATA_DIR / "descartados.json"


PALAVRAS_FORTES = [
    "edital",
    "chamada",
    "inscrição",
    "inscrições",
    "seleção",
    "fomento",
    "prêmio",
    "bolsa",
    "festival",
    "mostra",
    "laboratório",
    "residência",
    "pitching",
    "licitação",
    "audiovisual",
    "cinema",
    "curta",
    "longa",
    "documentário",
    "animação",
    "roteiro",
]

PALAVRAS_RUIDO = [
    "notícia",
    "resultado final",
    "resultado preliminar",
    "homologação",
    "nomeados",
    "posse",
    "agenda",
    "evento realizado",
    "release",
    "matéria",
    "entrevista",
]


def carregar_json(caminho):
    if not caminho.exists():
        print(f"Arquivo não encontrado: {caminho}")
        return []

    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def normalizar_texto(valor):
    if not valor:
        return ""
    return str(valor).lower().strip()


def calcular_score_validacao(item):
    score = 0

    titulo = normalizar_texto(item.get("titulo"))
    descricao = normalizar_texto(item.get("descricao"))
    url = normalizar_texto(item.get("url"))
    tipo = normalizar_texto(item.get("tipo"))
    prazo = normalizar_texto(item.get("prazo"))

    texto = f"{titulo} {descricao} {url} {tipo} {prazo}"

    for palavra in PALAVRAS_FORTES:
        if palavra in texto:
            score += 8

    for palavra in PALAVRAS_RUIDO:
        if palavra in texto:
            score -= 12

    if url:
        score += 10

    if titulo and len(titulo) > 12:
        score += 10

    if descricao and len(descricao) > 40:
        score += 10

    if prazo:
        score += 15

    if ".gov.br" in url:
        score += 10

    if any(ext in url for ext in [".pdf", "edital", "chamada", "inscricao", "inscrição"]):
        score += 10

    return max(score, 0)


def motivo_validacao(item, score):
    titulo = normalizar_texto(item.get("titulo"))
    descricao = normalizar_texto(item.get("descricao"))
    url = normalizar_texto(item.get("url"))
    prazo = normalizar_texto(item.get("prazo"))

    motivos = []

    if score >= 70:
        motivos.append("alta confiança semântica")

    if not titulo:
        motivos.append("sem título")

    if not url:
        motivos.append("sem URL")

    if not descricao:
        motivos.append("sem descrição")

    if not prazo:
        motivos.append("sem prazo identificado")

    texto = f"{titulo} {descricao} {url}"

    if any(p in texto for p in PALAVRAS_RUIDO):
        motivos.append("possível notícia/resultado/ruído")

    if not motivos:
        motivos.append("classificação automática")

    return motivos


def classificar_item(item):
    score = calcular_score_validacao(item)

    item_validado = {
        **item,
        "score_validacao": score,
        "motivos_validacao": motivo_validacao(item, score),
        "validado_em": datetime.now().isoformat(timespec="seconds"),
    }

    if score >= 70:
        item_validado["status_validacao"] = "feed"
        return "feed", item_validado

    if score >= 40:
        item_validado["status_validacao"] = "revisao"
        return "revisao", item_validado

    item_validado["status_validacao"] = "descartado"
    return "descartado", item_validado


def validar_oportunidades(itens):
    feed = []
    revisao = []
    descartados = []

    urls_vistas = set()

    for item in itens:
        url = item.get("url")

        if url and url in urls_vistas:
            item["status_validacao"] = "descartado"
            item["motivos_validacao"] = ["URL duplicada"]
            descartados.append(item)
            continue

        if url:
            urls_vistas.add(url)

        destino, item_validado = classificar_item(item)

        if destino == "feed":
            feed.append(item_validado)
        elif destino == "revisao":
            revisao.append(item_validado)
        else:
            descartados.append(item_validado)

    return feed, revisao, descartados


def main():
    itens = carregar_json(INPUT_FILE)

    feed, revisao, descartados = validar_oportunidades(itens)

    salvar_json(FEED_FILE, feed)
    salvar_json(REVISAO_FILE, revisao)
    salvar_json(DESCARTE_FILE, descartados)

    print("Validação final concluída.")
    print(f"Entram no feed: {len(feed)}")
    print(f"Vão para revisão: {len(revisao)}")
    print(f"Descartados: {len(descartados)}")


if __name__ == "__main__":
    main()
# Alias esperado pelo core/motor_oportunidades.py
def validar_feed(oportunidades):
    return validar_oportunidades(oportunidades)
