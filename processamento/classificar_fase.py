def classificar_fase_produto(titulo, link=""):
    base = f"{titulo} {link}".lower()

    if any(t in base for t in [
        "development", "roteiro", "screenplay", "project development"
    ]):
        return "desenvolvimento"

    if any(t in base for t in [
        "production", "film fund", "shooting"
    ]):
        return "producao"

    if any(t in base for t in [
        "post-production", "editing", "finalization"
    ]):
        return "pos_producao"

    if any(t in base for t in [
        "distribution", "exhibition", "festival strategy"
    ]):
        return "distribuicao"

    if any(t in base for t in [
        "festival", "screening", "mostra"
    ]):
        return "exibicao"

    if any(t in base for t in [
        "market", "pitch", "industry", "coproduction"
    ]):
        return "mercado"

    return "não identificado"