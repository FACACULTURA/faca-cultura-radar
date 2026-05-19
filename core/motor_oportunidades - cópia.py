import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from coleta.coletor import executar_coleta
from processamento.extrator_semantico import extrair_item_semantico

OUTPUT_DIR = Path("output")


def gerar_feed_json(output_dir="output"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    arquivo_tudo = output_path / "tudo.csv"
    arquivo_oportunidades = output_path / "oportunidades.csv"
    arquivo_noticias = output_path / "noticias.csv"

    if not arquivo_tudo.exists():
        raise FileNotFoundError(f"tudo.csv não encontrado em {output_path}")

    df_tudo = pd.read_csv(arquivo_tudo)
    df_oportunidades = pd.read_csv(arquivo_oportunidades) if arquivo_oportunidades.exists() else pd.DataFrame()
    df_noticias = pd.read_csv(arquivo_noticias) if arquivo_noticias.exists() else pd.DataFrame()

    oportunidades_semanticas = [
        extrair_item_semantico(item)
        for item in df_oportunidades.fillna("").to_dict(orient="records")
    ]

    noticias_semanticas = [
        extrair_item_semantico(item)
        for item in df_noticias.fillna("").to_dict(orient="records")
    ]

    feed = {
        "meta": {
            "gerado_em": datetime.now().isoformat(),    
            "total_itens": len(df_tudo),
            "total_oportunidades": len(df_oportunidades),
            "total_noticias": len(df_noticias),
            "total_fontes": len(set(df_tudo["fonte"].dropna().tolist())) if "fonte" in df_tudo.columns else 0,
        },
        "stats": {
            "por_tipo": df_tudo["tipo"].value_counts(dropna=False).to_dict() if "tipo" in df_tudo.columns else {},
            "por_classe": df_tudo["classe"].value_counts(dropna=False).to_dict() if "classe" in df_tudo.columns else {},
        },
        "oportunidades": oportunidades_semanticas,
        "noticias": noticias_semanticas,
        "fontes": sorted(list(set(df_tudo["fonte"].dropna().tolist()))) if "fonte" in df_tudo.columns else [],
    }

    with open(output_path / "feed.json", "w", encoding="utf-8") as f:
        json.dump(feed, f, ensure_ascii=False, indent=2)

    print(f"\nfeed.json salvo em: {output_path / 'feed.json'}")


def rodar_motor():
    executar_coleta()
    gerar_feed_json(OUTPUT_DIR)


if __name__ == "__main__":
    rodar_motor()