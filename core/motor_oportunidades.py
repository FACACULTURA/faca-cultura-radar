from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, urlunparse

import json
import sys
import pandas as pd

CORE_DIR = Path(__file__).resolve().parent
BASE_DIR = CORE_DIR.parent

sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(CORE_DIR))

from processamento.enriquecedor_pagina import enriquecer_item_com_pagina
from processamento.extrator_semantico_v2 import extrair_item_semantico as extrair_semantica_v2
from processamento.filtro_audiovisual import filtrar_audiovisual
from coleta.validador_final import classificar_final
from radar.curadores_editais import buscar_em_curadores
from coleta.coletor import executar_coleta
from processamento.leitor_semantico import ler_item_semantico
from processamento.memoria_fontes import enriquecer_com_memoria
from processamento.score_semantico import calcular_score_semantico
from processamento.contexto_editorial import analisar_contexto_editorial
from processamento.peneira_diversidade import aplicar_peneira_diversidade


OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR / "data"
INTERMEDIARIO_DIR = DATA_DIR / "intermediario"

JSON_REVISAO = INTERMEDIARIO_DIR / "oportunidades_revisao.json"
JSON_DESCARTADOS = INTERMEDIARIO_DIR / "oportunidades_descartadas.json"


# ==========================
# UTILS
# ==========================

def normalizar_url(url):
    if not url:
        return ""

    url = str(url).split("#")[0]

    parsed = urlparse(url)

    clean = parsed._replace(query="")

    return urlunparse(clean).rstrip("/").lower()


def chave_unica(item):
    link = normalizar_url(item.get("link") or item.get("url"))

    titulo = (
        item.get("titulo")
        or item.get("titulo_principal")
        or ""
    ).lower().strip()

    return f"{link}|{titulo}"


def salvar_json(caminho, dados):
    caminho.parent.mkdir(parents=True, exist_ok=True)

    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


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


def parse_data(item):
    prazo = (
        item.get("prazo")
        or item.get("deadline")
        or item.get("data_publicacao")
    )

    if not prazo:
        return datetime.max

    formatos = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
    ]

    for fmt in formatos:
        try:
            return datetime.strptime(str(prazo), fmt)
        except Exception:
            continue

    return datetime.max


def ordenar_feed(dados):
    hoje = datetime.now()

    def prioridade(item):
        data = parse_data(item)

        status = item.get("status_prazo")

        if status == "aberto" and data >= hoje:
            grupo = 0

        elif status == "previsto":
            grupo = 1

        elif status == "sem_data":
            grupo = 2

        else:
            grupo = 3

        return (
            grupo,
            data,
            (
                item.get("titulo_principal")
                or item.get("titulo")
                or ""
            ).lower()
        )

    return sorted(dados, key=prioridade)


# ==========================
# PIPELINE PRINCIPAL
# ==========================

def etapa_validacao():
    print("\n🧠 Rodando pipeline completo...")

    # ==========================
    # COLETA
    # ==========================

    print("\n📡 Executando coleta...")

    executar_coleta()

    csv_path = OUTPUT_DIR / "tudo.csv"

    if not csv_path.exists():
        print("⚠️ CSV não encontrado após coleta.")

        return {
            "feed": {
                "brasil": {},
                "internacional": {},
            },
            "revisao": [],
            "descartados": [],
        }

    df = pd.read_csv(csv_path)

    dados = df.to_dict(orient="records")

    print(f"📥 Itens coletados: {len(dados)}")

    # ==========================
    # CURADORES
    # ==========================

    try:
        print("\n🔎 Buscando pistas em curadores...")

        pistas_curadores = buscar_em_curadores()

        pistas = []

        pistas.extend(pistas_curadores.get("fortes", []))
        pistas.extend(pistas_curadores.get("medias", []))

        print(f"📌 Curadores adicionaram: {len(pistas)}")

        dados.extend(pistas)

    except Exception as erro:
        print(f"⚠️ Curadores não rodaram: {erro}")

    # ==========================
    # DEDUP INICIAL
    # ==========================

    dados = remover_duplicados(dados)

    print(f"📦 Após deduplicação: {len(dados)}")

    # ==========================
    # FILTRO AUDIOVISUAL
    # ==========================

    dados = filtrar_audiovisual(dados)

    print(f"🎬 Após filtro audiovisual: {len(dados)} itens")

    # ==========================
    # PIPELINE SEMÂNTICO
    # ==========================

    feed = []
    revisao = []
    descartados = []

    total = len(dados)

    for idx, item in enumerate(dados, start=1):

        try:
            item_enriquecido = enriquecer_item_com_pagina(item)

            item_semantico = extrair_semantica_v2(item_enriquecido)

            if not item_semantico:
                descartados.append(item_enriquecido)
                continue

            item_semantico = enriquecer_com_memoria(item_semantico)

            leitura = ler_item_semantico(item_semantico)

            item_semantico["leitura_semantica"] = leitura

            if leitura.get("titulo_semantico"):
                item_semantico["titulo_principal"] = leitura.get(
                    "titulo_semantico"
                )

            item_semantico = calcular_score_semantico(item_semantico)

            categoria = classificar_final(item_semantico)

            item_semantico["categoria_feed"] = categoria

            if categoria in [
                "editais",
                "oportunidades",
                "noticias",
                "licitacoes",
            ]:
                feed.append(item_semantico)

            elif categoria in [
                "revisao",
                "noticia_pista",
            ]:
                revisao.append(item_semantico)

            else:
                descartados.append(item_semantico)

        except Exception as erro:
            print(f"⚠️ Erro {idx}/{total}: {erro}")

            descartados.append(item)

        if idx % 25 == 0:
            print(
                f"… {idx}/{total} | "
                f"feed={len(feed)} "
                f"revisao={len(revisao)} "
                f"descartados={len(descartados)}"
            )

    # ==========================
    # CONTEXTO EDITORIAL
    # ==========================

    for item in feed:
        contexto = analisar_contexto_editorial(item)

        item["destino_principal"] = contexto["destino_principal"]

        item["tags_destino"] = contexto["tags_destino"]

        item["relevancia_estrategica"] = contexto[
            "relevancia_estrategica"
        ]

        item["categoria_feed"] = contexto["destino_principal"]

    # ==========================
    # FINALIZAÇÃO
    # ==========================

    feed = remover_duplicados(feed)
    revisao = remover_duplicados(revisao)
    descartados = remover_duplicados(descartados)

    feed = ordenar_feed(feed)

    from processamento.sintetizador_titulos import sintetizar_feed

    feed = sintetizar_feed(feed)

    # ==========================
    # PENEIRA
    # ==========================

    try:
        feed = aplicar_peneira_diversidade(feed)

    except Exception as e:
        print(
            f"⚠️ Peneira falhou, mantendo feed bruto: {e}"
        )

    # ==========================
    # SEPARADOR DE CATEGORIAS
    # ==========================

    try:
        from processamento.utils import separar_categorias

    except Exception:

        def separar_categorias(x):
            return x

    # ==========================
    # TERRITÓRIOS
    # ==========================

    feed_brasil = []
    feed_internacional = []

    for item in feed:
        pais = str(item.get("pais", "")).strip().lower()

        if pais in ["brasil", "br"]:
            feed_brasil.append(item)

        else:
            feed_internacional.append(item)

    saida_final = {
        "brasil": separar_categorias(feed_brasil),
        "internacional": separar_categorias(feed_internacional),
    }

    # ==========================
    # LOG FINAL
    # ==========================

    print("\n📊 RESULTADO FINAL:")

    print(f"✅ Feed: {len(feed)}")
    print(f"🟡 Revisão: {len(revisao)}")
    print(f"⚫ Descartados: {len(descartados)}")

    # ==========================
    # RETORNO PURO
    # ==========================

    return {
        "feed": saida_final,
        "revisao": revisao,
        "descartados": descartados,
    }


def executar_motor():
    print("\n🚀 F.CULT — MOTOR FINAL")

    print(f"Início: {datetime.now()}")

    resultado = etapa_validacao()

    print("\n🏁 Motor finalizado")

    return resultado


if __name__ == "__main__":
    executar_motor()