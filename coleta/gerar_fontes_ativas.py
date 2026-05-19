import json
from pathlib import Path
from urllib.parse import urlparse


def carregar_json(caminho, chave_esperada=None):
    path = Path(caminho)

    if not path.exists():
        print(f"[AVISO] Arquivo não encontrado: {path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        if chave_esperada and chave_esperada in data:
            return data.get(chave_esperada, [])

        for chave in ["fontes", "fontes_mae", "fontes_descobertas", "itens", "programas"]:
            if chave in data and isinstance(data[chave], list):
                return data[chave]

    return []


def detectar_origem_tipo(item):
    tipo = (item.get("tipo") or item.get("tipo_entidade") or item.get("grupo") or "").lower()
    url = (item.get("url") or item.get("link") or "").lower()
    nome = (item.get("nome") or item.get("nome_original") or item.get("titulo") or "").lower()

    if any(t in tipo for t in ["organizacao_publica", "agencia", "film_commission", "diario_estadual", "diario_municipal"]):
        if ".gov.br" in url or "gov.br" in url or "secretaria" in nome or "ministerio" in nome or "diário" in nome or "diario" in nome:
            return "publica"
        return "institucional"

    if tipo in ["fundo", "festival", "mercado", "lab", "programa"]:
        return "programa"

    if "gov.br" in url or ".gov.br" in url:
        return "publica"

    return "fonte"


def detectar_pais_regiao(item):
    regiao = item.get("regiao") or item.get("pais") or ""
    url = item.get("url") or item.get("link") or ""

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
    campos_score = [
        "confianca",
        "score_confianca",
        "score_validacao",
        "score_fonte_mae",
        "score_descoberta",
        "score",
        "peso",
    ]

    score = 0

    for campo in campos_score:
        try:
            score += int(float(item.get(campo, 0) or 0))
        except Exception:
            pass

    grupo = (item.get("grupo") or "").lower()
    tipo = (item.get("tipo") or item.get("tipo_entidade") or "").lower()
    nome = (item.get("nome") or item.get("nome_original") or "").lower()
    url = (item.get("url") or item.get("link") or "").lower()

    bonus = 0

    if grupo == "programas":
        bonus += 20
    if grupo == "fontes_mae":
        bonus += 15

    if tipo in ["fundo", "festival", "mercado", "lab"]:
        bonus += 10

    termos_fortes = [
        "gov.br",
        "secult",
        "cultura",
        "ancine",
        "minc",
        "funarte",
        "spcine",
        "riofilme",
        "pbh",
        "prefeitura",
        "diário",
        "diario",
        "doe",
        "dom",
        "film commission",
        "audiovisual",
    ]

    for termo in termos_fortes:
        if termo in nome or termo in url or termo in tipo:
            bonus += 10

    if ".gov.br" in url:
        bonus += 30

    return score + bonus


def normalizar_item(item, grupo_origem):
    nome = (
        item.get("nome")
        or item.get("nome_pt")
        or item.get("nome_original")
        or item.get("titulo")
        or item.get("titulo_site")
        or item.get("origem_seed")
        or "Fonte sem nome"
    )

    url = (item.get("url") or item.get("link") or "").strip()

    if not url or not url.startswith("http"):
        return None

    ativo = item.get("ativo", item.get("ativa", True))
    if ativo is False:
        return None

    dominio = urlparse(url).netloc.replace("www.", "")

    novo = {
        "nome": str(nome).strip(),
        "url": url,
        "ativo": True,
        "origem_tipo": detectar_origem_tipo(item),
        "pais": detectar_pais_regiao(item),
        "grupo_origem": grupo_origem,
        "tipo_descoberto": item.get("tipo") or item.get("tipo_entidade") or "",
        "regiao": item.get("regiao") or item.get("pais") or item.get("estado") or "",
        "dominio": item.get("dominio") or dominio,
        "score_base": score_base(item),
        "origem_seed": item.get("origem_seed", ""),
        "peso_exploracao": 1,
    }

    tipo = (novo["tipo_descoberto"] or "").lower()
    nome_lower = novo["nome"].lower()
    url_lower = novo["url"].lower()

    if grupo_origem in ["fontes_curadas", "fontes_mae", "fontes_semente"]:
        novo["peso_exploracao"] = 2

    if grupo_origem == "fontes_descobertas":
        novo["peso_exploracao"] = 1

    if grupo_origem == "fontes_diarios_oficiais":
        novo["peso_exploracao"] = 3

    if tipo in ["mercado", "lab", "festival", "fundo"]:
        novo["peso_exploracao"] = 3

    if any(t in nome_lower or t in url_lower for t in ["ancine", "minc", "secult", "spcine", "riofilme", "pbh", "prefeitura"]):
        novo["peso_exploracao"] = 3

    return novo


def deduplicar_por_url(fontes):
    mapa = {}

    fontes_ordenadas = sorted(
        fontes,
        key=lambda x: x.get("score_base", 0),
        reverse=True
    )

    for item in fontes_ordenadas:
        url = item["url"].rstrip("/").lower()

        if url not in mapa:
            mapa[url] = item
            continue

        existente = mapa[url]

        if item.get("score_base", 0) > existente.get("score_base", 0):
            mapa[url] = item

    return list(mapa.values())


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

    base_fontes = backend_dir / "data" / "input" / "fontes"

    arquivos = [
        ("fontes_curadas.json", None),
        ("fontes_descobertas.json", None),
        ("fontes_mae.json", None),
        ("fontes_semente.json", None),
        ("fontes_diarios_oficiais.json", None),
    ]

    caminho_saida_viva = base_dir / "config_fontes" / "fontes.json"
    caminho_saida_compat = backend_dir / "config" / "fontes.json"

    normalizadas = []

    for nome_arquivo, chave in arquivos:
        caminho = base_fontes / nome_arquivo
        itens = carregar_json(caminho, chave)

        grupo = nome_arquivo.replace(".json", "")

        print(f"{grupo} carregadas: {len(itens)}")

        for item in itens:
            convertido = normalizar_item(item, grupo)
            if convertido:
                normalizadas.append(convertido)

    finais = deduplicar_por_url(normalizadas)

    finais = sorted(
        finais,
        key=lambda x: x.get("score_base", 0),
        reverse=True
    )

    salvar_fontes_json(finais, caminho_saida_viva)
    salvar_fontes_json(finais, caminho_saida_compat)


if __name__ == "__main__":
    executar()