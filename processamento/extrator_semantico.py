import re
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================
# UTILIDADES
# ============================

def normalizar_texto(valor: Any) -> str:
    return re.sub(r"\s+", " ", str(valor or "")).strip()


def juntar_textos(item: Dict[str, Any]) -> str:
    partes = [
        item.get("titulo", ""),
        item.get("descricao", ""),
        item.get("conteudo", ""),
        item.get("texto", ""),
    ]
    return normalizar_texto(" ".join(partes))


# ============================
# EXTRAÇÕES
# ============================

def extrair_titulo_principal(item: Dict[str, Any]) -> str:
    texto = juntar_textos(item)

    if not texto:
        return "Sem título"

    texto = normalizar_texto(texto)

    frases = [f.strip() for f in re.split(r"[.!?]", texto) if f.strip()]
    for frase in frases:
        if 8 <= len(frase) <= 90:
            return frase

    return texto[:90].rstrip() + ("..." if len(texto) > 90 else "")


def extrair_prazo(item: Dict[str, Any]) -> Optional[str]:
    texto = juntar_textos(item)

    match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", texto)
    if match:
        d, m, y = match.groups()
        return f"{d.zfill(2)}/{m.zfill(2)}/{y}"

    return None


def extrair_instituicao(item: Dict[str, Any]) -> Optional[str]:
    texto = juntar_textos(item).lower()

    mapa = {
        "ancine": "Ancine",
        "funarte": "Funarte",
        "minc": "Ministério da Cultura",
        "sesc": "Sesc",
    }

    for chave, valor in mapa.items():
        if chave in texto:
            return valor

    return None


def extrair_geografia(item: Dict[str, Any]) -> Dict[str, Optional[str]]:
    texto = juntar_textos(item).lower()

    cidade = item.get("cidade")
    estado = item.get("estado")
    pais = item.get("pais")

    if not cidade and "são paulo" in texto:
        cidade = "São Paulo"

    if not estado and "são paulo" in texto:
        estado = "SP"

    if not pais:
        pais = "Brasil" if estado or cidade else None

    return {"cidade": cidade, "estado": estado, "pais": pais}


def extrair_condicao(item: Dict[str, Any]) -> Optional[str]:
    texto = juntar_textos(item).lower()

    if "gratuit" in texto:
        return "gratuito"

    if "pago" in texto or "taxa" in texto:
        return "pago"

    return None


def classificar_tipo_item(item: Dict[str, Any]) -> str:
    texto = juntar_textos(item).lower()

    if any(t in texto for t in ["pregão", "licitação"]):
        return "licitacao"

    if any(t in texto for t in ["edital", "chamada pública"]):
        return "edital"

    if any(t in texto for t in ["curso", "oficina", "laboratório"]):
        return "oportunidade"

    return "noticia"


def gerar_resumo(item: Dict[str, Any]) -> str:
    texto = normalizar_texto(
        item.get("descricao")
        or item.get("conteudo")
        or item.get("titulo")
    )

    if not texto:
        return "Sem resumo disponível."

    return texto[:180] + ("..." if len(texto) > 180 else "")


# ============================
# ITEM SEMÂNTICO
# ============================

def extrair_item_semantico(item: Dict[str, Any]) -> Dict[str, Any]:
    geo = extrair_geografia(item)

    return {
        "titulo_principal": extrair_titulo_principal(item),
        "tipo_item": classificar_tipo_item(item),
        "prazo": extrair_prazo(item),
        "instituicao": extrair_instituicao(item),
        "cidade": geo.get("cidade"),
        "estado": geo.get("estado"),
        "pais": geo.get("pais"),
        "condicao": extrair_condicao(item),
        "resumo": gerar_resumo(item),
        "link": item.get("link"),
        "titulo_original": item.get("titulo"),
        "descricao_original": item.get("descricao"),
    }


# ============================
# PIPELINE (EXECUÇÃO)
# ============================

def executar_extracao_semantica(caminho_entrada, caminho_saida):
    print("🧠 Rodando extração semântica...")

    caminho_entrada = Path(caminho_entrada)
    caminho_saida = Path(caminho_saida)

    if not caminho_entrada.exists():
        print(f"❌ CSV não encontrado: {caminho_entrada}")
        return []

    resultados: List[Dict[str, Any]] = []

    with open(caminho_entrada, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                item = extrair_item_semantico(row)
                resultados.append(item)
            except Exception as erro:
                print(f"⚠️ Erro ao processar item: {erro}")

    caminho_saida.parent.mkdir(parents=True, exist_ok=True)

    with open(caminho_saida, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"✅ Semântica gerada: {len(resultados)} itens")
    print(f"📁 Salvo em: {caminho_saida}")

    return resultados