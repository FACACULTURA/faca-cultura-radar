import json
from pathlib import Path

def carregar_fontes(caminho="config/fontes.json"):
    caminho_arquivo = Path(caminho)

    if not caminho_arquivo.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        return json.load(f)