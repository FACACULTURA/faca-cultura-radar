from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent

OUTPUT_DIR = BASE_DIR / "output"

FEED_PATH = OUTPUT_DIR / "feed.json"
REVISAO_PATH = OUTPUT_DIR / "revisao.json"
DESCARTADOS_PATH = OUTPUT_DIR / "descartados.json"


def salvar_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def salvar_resultado(resultado):
    salvar_json(FEED_PATH, resultado["feed"])

    salvar_json(
        REVISAO_PATH,
        resultado["revisao"]
    )

    salvar_json(
        DESCARTADOS_PATH,
        resultado["descartados"]
    )

    print("💾 Persistência concluída")