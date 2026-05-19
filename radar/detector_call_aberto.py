import re
from typing import Dict, Any, List


# ============================
# PADRÕES DE DETECÇÃO
# ============================

SINAIS_CALL_FORTE = [
    "apply", "application", "deadline", "submissions open",
    "call for projects", "call for entries",
    "inscrições abertas", "inscrição até",
    "prazo até", "regulamento", "edital",
    "formulário", "guidelines",
]

SINAIS_CALL_MEDIO = [
    "open call", "submission", "grant", "fund",
    "residency", "lab", "laboratory", "pitching",
    "market", "program", "programa",
]

SINAIS_FONTE_PROMISSORA = [
    "programs", "grants", "funds", "labs",
    "markets", "initiatives", "opportunities",
]

SINAIS_NOTICIA = [
    "news", "notícia", "article", "release",
    "entrevista", "cobertura", "festival aconteceu",
]

SINAIS_TECNICO = [
    "camera", "lens", "lente", "luz", "lighting",
    "software", "ia", "ai", "render", "produção virtual",
]


# ============================
# UTIL
# ============================

def normalizar(texto: Any) -> str:
    return str(texto or "").lower().strip()


def texto_item(item: Dict[str, Any]) -> str:
    partes = [
        item.get("titulo_principal"),
        item.get("titulo"),
        item.get("titulo_original"),
        item.get("resumo"),
        item.get("descricao"),
        item.get("descricao_original"),
        item.get("conteudo"),
        item.get("link"),
    ]

    return normalizar(" ".join([str(p) for p in partes if p]))


def detectar_sinais(texto: str, lista: List[str]) -> List[str]:
    encontrados = []
    for termo in lista:
        if termo in texto:
            encontrados.append(termo)
    return encontrados


# ============================
# CLASSIFICAÇÃO
# ============================

def classificar_sinal(item: Dict[str, Any]) -> Dict[str, Any]:
    texto = texto_item(item)

    sinais_forte = detectar_sinais(texto, SINAIS_CALL_FORTE)
    sinais_medio = detectar_sinais(texto, SINAIS_CALL_MEDIO)
    sinais_fonte = detectar_sinais(texto, SINAIS_FONTE_PROMISSORA)
    sinais_noticia = detectar_sinais(texto, SINAIS_NOTICIA)
    sinais_tecnico = detectar_sinais(texto, SINAIS_TECNICO)

    resultado = {
        **item,
        "sinal_detectado": None,
        "deve_vasculhar": False,
        "destino_sugerido": None,
        "motivos": [],
    }

    # 🔥 CALL FORTE
    if sinais_forte:
        resultado.update({
            "sinal_detectado": "call_forte",
            "deve_vasculhar": True,
            "destino_sugerido": "oportunidade",
            "motivos": sinais_forte,
        })
        return resultado

    # ⚡ CALL MÉDIO
    if sinais_medio:
        resultado.update({
            "sinal_detectado": "call_medio",
            "deve_vasculhar": True,
            "destino_sugerido": "exploracao",
            "motivos": sinais_medio,
        })
        return resultado

    # 🧭 FONTE PROMISSORA
    if sinais_fonte:
        resultado.update({
            "sinal_detectado": "fonte_promissora",
            "deve_vasculhar": True,
            "destino_sugerido": "fonte",
            "motivos": sinais_fonte,
        })
        return resultado

    # 📰 NOTÍCIA
    if sinais_noticia:
        resultado.update({
            "sinal_detectado": "noticia_setorial",
            "deve_vasculhar": False,
            "destino_sugerido": "noticia",
            "motivos": sinais_noticia,
        })
        return resultado

    # 🎥 TÉCNICO / MERCADO
    if sinais_tecnico:
        resultado.update({
            "sinal_detectado": "tecnico_mercado",
            "deve_vasculhar": False,
            "destino_sugerido": "tecnica",
            "motivos": sinais_tecnico,
        })
        return resultado

    # 🔹 DEFAULT (aqui entra sua lógica de “mesmo fraco, investigar”)
    resultado.update({
        "sinal_detectado": "fraco",
        "deve_vasculhar": True,
        "destino_sugerido": "exploracao",
        "motivos": ["sem sinal forte, mas pertence à bolha"],
    })

    return resultado


# ============================
# PROCESSAMENTO EM LOTE
# ============================

def processar_lista(itens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    resultados = []

    for item in itens:
        try:
            resultado = classificar_sinal(item)
            resultados.append(resultado)
        except Exception as e:
            print(f"Erro ao classificar item: {e}")

    return resultados


# ============================
# TESTE LOCAL
# ============================

if __name__ == "__main__":
    exemplo = {
        "titulo": "Call for Projects 2026 - Open Submissions",
        "descricao": "Apply now. Deadline: 30/06/2026",
        "link": "https://example.com"
    }

    resultado = classificar_sinal(exemplo)
    print(resultado)