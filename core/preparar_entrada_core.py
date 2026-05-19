import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

CAMINHOS = [
    BASE / "data/bruto/urls_candidatas.json",
    BASE / "data/pistas_curadores.json",
]

SAIDA = BASE / "data/bruto/entrada_core.json"

def carregar(caminho):
    if not caminho.exists():
        return []
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []
    
    """
    Agora lê:
    - entrada_core.json (prioritário)
    - fallback: urls_candidatas.json
    """

    caminho_core = Path("data/bruto/entrada_core.json")
    caminho_urls = URLS_CANDIDATAS_PATH

    if caminho_core.exists():
        print("\n🔥 Usando entrada_core (explorador + curadores + tudo)")
        caminho = caminho_core
    else:
        print("\n⚠️ Usando apenas urls_candidatas")
        caminho = caminho_urls

    if not caminho.exists():
        print("\n⚠️ Nenhum arquivo encontrado.")
        print(f"Esperado em: {caminho}")
        return []

    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)

        urls = []

        if not isinstance(dados, list):
            print("⚠️ Arquivo existe, mas não é lista.")
            return []

        for item in dados:
            if isinstance(item, str):
                url = item
                nome = "Explorador"

            elif isinstance(item, dict):
                url = item.get("url") or item.get("link")
                nome = item.get("fonte_origem") or item.get("fonte") or item.get("nome") or "Core"

            else:
                continue

            if not url:
                continue

            urls.append({
                "nome": nome,
                "url": url,
                "origem_explorador": True,
            })

        print(f"\n🔗 URLs carregadas: {len(urls)}")
        return urls

    except Exception as e:
        print("⚠️ Erro ao carregar URLs:", e)
        return []


def normalizar(item, origem):
    return {
        "url": item.get("url"),
        "titulo": item.get("titulo") or "",
        "resumo": item.get("resumo") or "",
        "origem_tipo": origem,
        "fonte_origem": item.get("fonte") or item.get("dominio"),
        "score_origem": item.get("score") or item.get("score_candidato") or 0,
        "deve_investigar": True,
    }


def main():
    todos = []

    for caminho in CAMINHOS:
        dados = carregar(caminho)

        if not isinstance(dados, list):
            continue

        origem = caminho.name

        for item in dados:
            if not item.get("url"):
                continue
            todos.append(normalizar(item, origem))

    # deduplicar por URL
    unicos = {}
    for item in todos:
        url = item["url"]
        if url not in unicos:
            unicos[url] = item
        else:
            if item["score_origem"] > unicos[url]["score_origem"]:
                unicos[url] = item

    resultado = list(unicos.values())

    SAIDA.parent.mkdir(parents=True, exist_ok=True)

    with open(SAIDA, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"✅ entrada_core gerada: {len(resultado)} itens")


if __name__ == "__main__":
    main()