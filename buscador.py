import requests
from bs4 import BeautifulSoup

# URL de exemplo: Minc (editais culturais federais)
url = "https://www.gov.br/cultura/pt-br/assuntos/editais"

# Faz o download da página
response = requests.get(url)
html = response.text

# Interpreta o HTML
soup = BeautifulSoup(html, "html.parser")

# Procura títulos de editais
titulos = soup.find_all("a")

print("EDITAIS ENCONTRADOS:\n")

for t in titulos:
    texto = t.get_text(strip=True)
    if "Edital" in texto or "Concurso" in texto or "Seleção" in texto:
        print("-", texto)
