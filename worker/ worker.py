import time
import json
from pathlib import Path
from datetime import datetime

# aqui você importa seu motor real
from motor import gerar_feed

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "output" / "feed.json"


def salvar_feed(feed):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "updated_at": datetime.utcnow().isoformat(),
        "data": feed
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def rodar_worker():
    while True:
        print("🔄 Worker iniciando execução do motor...")

        try:
            feed = gerar_feed()  # seu cérebro atual

            print(f"🧠 Feed gerado: {len(feed)} itens")

            salvar_feed(feed)

            print("✅ Feed atualizado com sucesso")

        except Exception as e:
            print(f"❌ erro no worker: {e}")

        print("😴 Dormindo por 6 horas...\n")

        time.sleep(6 * 60 * 60)  # 6 horas


if __name__ == "__main__":
    rodar_worker()