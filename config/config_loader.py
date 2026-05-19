from pathlib import Path
import json

def carregar_fontes(path=None):
    if path is None:
        base_dir = Path(__file__).resolve().parent.parent
        path = base_dir / "config" / "fontes.json"

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)