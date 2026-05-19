import json
from pathlib import Path
from urllib.parse import urlparse


def carregar_json(caminho, chave_esperada):
    path = Path(caminho)

    if not path.exists():
        print(f"[AVISO] Arquivo não encontrado: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        return data.get(chave_esperada, [])

    return []


def detectar_origem_tipo(item):
    tipo = (item.get("tipo") or "").lower()
    url = (item.get("url") or "").lower()
    nome = (item.get("nome") or "").lower()

    if any(t in tipo for t in ["organizacao_publica", "agencia", "film_commission"]):
        if ".gov.br" in url or "gov.br" in url or "secretaria" in nome or "ministerio" in nome:
            return "publica"
        return "institucional"

    if tipo in ["fundo", "festival", "mercado", "lab"]:
        return "programa"

    return "fonte"


def detectar_pais_regiao(item):
    regiao = item.get("regiao", "") or ""
    url = item.get("url", "") or ""

    dominio = urlparse(url).netloc.lower()

    if "gov.br" in dominio or dominio.endswith(".br"):
        return "Brasil"

    if regiao:
        return regiao

    if dominio.endswith(".pt"):
        return "Portugal"
    if dominio.endswith(".fr"):
        return "França"
    if dominio.endswith(".es"):
        return "Espanha"
    if dominio.endswith(".it"):
        return "Itália"
    if dominio.endswith(".de"):
        return "Alemanha"
    if dominio.endswith(".uk") or dominio.endswith(".co.uk"):
        return "Reino Unido"
    if dominio.endswith(".eu"):
        return "União Europeia"

    return "Internacional"


def score_base(item):
    score = int(item.get("score", 0) or 0)
    score_fonte_mae = int(item.get("score_fonte_mae", 0) or 0)

    grupo = (item.get("grupo") or "").lower()
    tipo = (item.get("tipo") or "").lower()

    bonus = 0

    if grupo == "programas":
        bonus += 20
    if grupo == "fontes_mae":
        bonus += 15

    if tipo in ["fundo", "festival", "mercado", "lab"]:
        bonus += 10

    return score + score_fonte_mae + bonus


def normalizar_item(item, grupo_origem):
    nome = item.get("nome") or item.get("nome_original") or "Fonte sem nome"
    url = (item.get("url") or "").strip()

    if not url:
        return None

    novo = {
        "nome": nome,
        "url": url,
        "ativo": True,
        "origem_tipo": detectar_origem_tipo(item),
        "pais": detectar_pais_regiao(item),
        "grupo_origem": grupo_origem,
        "tipo_descoberto": item.get("tipo", ""),
        "regiao": item.get("regiao", ""),
        "score_base": score_base(item),
        "origem_seed": item.get("origem_seed", ""),
        "peso_exploracao": 1
    }

    if grupo_origem == "programas":
        novo["peso_exploracao"] = 3

    elif grupo_origem == "fontes_mae":
        novo["peso_exploracao"] = 2

    elif item.get("tipo") in ["mercado", "lab", "festival"]:
        novo["peso_exploracao"] = 3

    return novo


def deduplicar_por_url(fontes):
    vistas = set()
    finais = []

    fontes_ordenadas = sorted(
        fontes,
        key=lambda x: x.get("score_base", 0),
        reverse=True
    )

    for item in fontes_ordenadas:
        url = item["url"].rstrip("/").lower()
        if url in vistas:
            continue
        vistas.add(url)
        finais.append(item)

    return finais


def salvar_fontes_json(fontes, caminho_saida):
    path = Path(caminho_saida)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "fontes": fontes
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Arquivo gerado em: {path}")
    print(f"Total de fontes ativas: {len(fontes)}")


def executar():
    base_dir = Path(__file__).resolve().parent
    backend_dir = base_dir.parent

    caminho_fontes_mae = backend_dir / "saida" / "fontes_mae.json"
    caminho_programas = backend_dir / "saida" / "programas.json"
    caminho_saida = base_dir / "config_fontes" / "fontes.json"

    fontes_mae = carregar_json(caminho_fontes_mae, "fontes_mae")
    programas = carregar_json(caminho_programas, "programas")

    print(f"Fontes-mãe carregadas: {len(fontes_mae)}")
    print(f"Programas carregados: {len(programas)}")

    normalizadas = []

    for item in fontes_mae:
        convertido = normalizar_item(item, "fontes_mae")
        if convertido:
            normalizadas.append(convertido)

    for item in programas:
        convertido = normalizar_item(item, "programas")
        if convertido:
            normalizadas.append(convertido)

    finais = deduplicar_por_url(normalizadas)

    salvar_fontes_json(finais, caminho_saida)


if __name__ == "__main__":
    executar()