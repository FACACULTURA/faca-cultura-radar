from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path
import json
import math

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
FEED_PATH = BASE_DIR / "output" / "feed.json"

def limpar_nan(obj):

    if isinstance(obj, dict):
        return {
            k: limpar_nan(v)
            for k, v in obj.items()
        }

    elif isinstance(obj, list):
        return [
            limpar_nan(v)
            for v in obj
        ]

    elif isinstance(obj, float):

        if math.isnan(obj):
            return None

        if math.isinf(obj):
            return None

        return obj

    return obj

def carregar_feed():

    if not FEED_PATH.exists():
        return {
            "meta": {},
            "items": [],
            "agrupado": {
                "editais": [],
                "oportunidades": [],
                "noticias": [],
                "licitacoes": []
            }
        }

    try:

        with open(FEED_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        with open(FEED_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        data = limpar_nan(data)

        if isinstance(data, dict):
                    return data 

        if isinstance(data, list):

            agrupado = {
                "editais": [],
                "oportunidades": [],
                "noticias": [],
                "licitacoes": []
            }

            for item in data:

                categoria = (
                    item.get("categoria_feed")
                    or item.get("classe")
                    or item.get("tipo")
                    or "oportunidades"
                )

                categoria = categoria.lower()

                if categoria not in agrupado:
                    categoria = "oportunidades"

                agrupado[categoria].append(item)

            return {
                "meta": {
                    "total": len(data)
                },
                "items": data,
                "agrupado": agrupado
            }

    except Exception as e:

        return {
            "erro": str(e),
            "items": [],
            "agrupado": {}
        }


@app.get("/")
def home():
    return {
        "status": "online",
        "api": "fcult",
        "feed": str(FEED_PATH)
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "feed_exists": FEED_PATH.exists(),
        "feed_path": str(FEED_PATH)
    }


@app.get("/feed")
def feed():
    return carregar_feed()


@app.get("/feed_app")
def feed_app():
    return carregar_feed()