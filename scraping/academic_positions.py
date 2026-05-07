import requests
from bs4 import BeautifulSoup

def get_offers():
    url = "https://academicpositions.com/jobs/physics"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    r = requests.get(url, headers=headers)

    print("Status code:", r.status_code)
    print("Taille HTML:", len(r.text))

    soup = BeautifulSoup(r.text, "html.parser")

    print("Titre page:", soup.title.text if soup.title else "Pas de titre")

    offers = []

    links = soup.find_all("a", href=True)

    for link_tag in links[:50]:
        text = link_tag.get_text(strip=True)
        href = link_tag["href"]

        if text:
            print(text, "->", href)

    return offers