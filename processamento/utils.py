import re

def extrair_ano_de_titulo_ou_link(titulo, link=""):
    texto = f"{titulo} {link}"
    match = re.search(r"(20\d{2}|19\d{2})", texto)
    return match.group(1) if match else ""