# core/motor_oportunidades.py

from pathlib import Path
from datetime import datetime
import json
import sys

CORE_DIR = Path(__file__).resolve().parent
BASE_DIR = CORE_DIR.parent

sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(CORE_DIR))

from processamento.enriquecedor_pagina import enriquecer_item_com_pagina
from processamento.extrator_semantico_v2 import extrair_semantica_v2


DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
INTERMEDIARIO_DIR = DATA_DIR / "intermediario"

JSON_SEMANTICO = INTERMEDIARIO_DIR / "oportunidades_semanticas.json"
JSON_REVISAO = INTERMEDIARIO_DIR / "oportunidades_revisao.json"
JSON_DESCARTADOS = INTERMEDIARIO_DIR / "oportunidades_descartadas.json"
FEED_FINAL = OUTPUT_DIR / "feed.json"


def carregar_json(caminho, padrao=None):
    if padrao is None:
        padrao = []

    if not caminho.exists():
        return padrao

    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def salvar_json(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def ordenar_por_prazo(item):
    prazo = item.get("prazo") or item.get("prazo_final") or item.get("deadline")

    if not prazo:
        return datetime.max

    formatos = ["%d/%m/%Y", "%Y-%m-%d"]

    for formato in formatos:
        try:
            return datetime.strptime(str(prazo), formato)
        except Exception:
            pass

    return datetime.max


def ordenar_feed(feed):
    return sorted(
        feed,
        key=lambda item: (
            ordenar_por_prazo(item),
            str(item.get("titulo") or item.get("titulo_principal") or "").lower()
        )
    )

def chave_unica(item):
    link = (item.get("link") or "").split("#")[0].rstrip("/")
    titulo = (item.get("titulo") or item.get("titulo_principal") or "").lower().strip()
    return f"{link}|{titulo}"


def remover_duplicados(dados):
    vistos = set()
    limpos = []

    for item in dados:
        chave = chave_unica(item)
        if chave in vistos:
            continue
        vistos.add(chave)
        limpos.append(item)

    return limpos

def etapa_validacao():
    print("\n🧠 Rodando validação final...")

    dados = carregar_json(JSON_SEMANTICO, [])



    # LIMITE TEMPORÁRIO PARA TESTE
    # Depois que aprovarmos a lógica, remova esta linha.
    # dados = dados[:100]

    feed = []
    revisao = []
    descartados = []

    total = len(dados)
    print(f"📥 Itens semânticos carregados: {total}")

    for idx, item in enumerate(dados, start=1):
        try:
            # 1. Abre página real e pega h1/title/data/parágrafos/links
            item_enriquecido = enriquecer_item_com_pagina(item)

            # 2. Exploração profunda desligada por enquanto
            item_explorado = item_enriquecido

            # 3. Teste puro do extrator semântico v2
            item_semantico = extrair_semantica_v2(item_explorado)

            if not item_semantico:
                descartados.append(item_explorado)
                continue

            feed.append(item_semantico)

        except Exception as erro:
            print(f"⚠️ Erro ao processar item {idx}/{total}: {erro}")
            descartados.append({
                "erro": str(erro),
                "item_original": item,
            })

        if idx % 25 == 0:
            print(
                f"… processados {idx}/{total} | "
                f"feed={len(feed)} descartados={len(descartados)}"
            )

    feed = ordenar_feed(feed)

    salvar_json(FEED_FINAL, feed)
    salvar_json(JSON_REVISAO, revisao)
    salvar_json(JSON_DESCARTADOS, descartados)

    print(f"✅ Feed: {len(feed)}")
    print(f"🟡 Revisão: {len(revisao)}")
    print(f"⚫ Descartados: {len(descartados)}")
    print(f"📁 Feed final: {FEED_FINAL}")

    return feed


def executar_motor():
    inicio = datetime.now()

    print("\n🚀 F.CULT — MOTOR FINAL / TESTE EXTRATOR V2")
    print(f"Início: {inicio.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"Base: {BASE_DIR}")

    etapa_validacao()

    fim = datetime.now()
    print(f"\n⏱️ Tempo: {fim - inicio}")
    print("✅ Motor finalizado")


if __name__ == "__main__":
    executar_motor()
