from bolha_semantica import montar_bolha
from detector_call_aberto import processar_lista
import json
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"
PIPELINE_FILE = OUTPUT_DIR / "bolha_processada.json"


def executar_pipeline(consulta):
    print("\n🚀 PIPELINE BOLHA → DETECTOR\n")

    # 1. gera bolha
    bolha = montar_bolha(consulta)
    itens = bolha.get("itens_relevantes", [])

    print(f"\n🔍 Classificando {len(itens)} itens...\n")

    # 2. classifica sinais
    classificados = processar_lista(itens)

    # 3. salva resultado
    PIPELINE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(PIPELINE_FILE, "w", encoding="utf-8") as f:
        json.dump(classificados, f, ensure_ascii=False, indent=2)

    # ============================
    # RESUMO
    # ============================

    resumo = {}
    for item in classificados:
        tipo = item.get("sinal_detectado")
        resumo[tipo] = resumo.get(tipo, 0) + 1

    print("📊 RESUMO:")
    for k, v in resumo.items():
        print(f"{k}: {v}")

    # ============================
    # TOP OPORTUNIDADES
    # ============================

    print("\n🔥 TOP OPORTUNIDADES:")
    top_oportunidades = [
        i for i in classificados if i.get("sinal_detectado") == "call_forte"
    ]

    for i, item in enumerate(top_oportunidades[:10], start=1):
        titulo = item.get("titulo") or item.get("titulo_principal") or "Sem título"
        score = item.get("score_bolha")
        print(f"{i}. [{score}] {titulo}")

    # ============================
    # TOP PARA VASCULHAR
    # ============================

    print("\n🧭 TOP PARA VASCULHAR:")
    top_vasculhar = [
        i for i in classificados if i.get("deve_vasculhar") is True
    ]

    for i, item in enumerate(top_vasculhar[:10], start=1):
        titulo = item.get("titulo") or item.get("titulo_principal") or "Sem título"
        tipo = item.get("sinal_detectado")
        print(f"{i}. [{tipo}] {titulo}")

    print(f"\n📁 Salvo em: {PIPELINE_FILE}")

    return classificados


if __name__ == "__main__":
    consulta = input("Digite a consulta: ")
    executar_pipeline(consulta)