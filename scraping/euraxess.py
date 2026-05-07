import requests
from bs4 import BeautifulSoup
import time
import re

BASE_URL = "https://euraxess.ec.europa.eu"

SEARCH_KEYWORDS = [
    "particle physics",
    "high energy physics",
    "neutrino",
    "astrophysics",
    "cosmology",
    "theoretical physics"
]

FILTER_KEYWORDS = [
    "particle physics",
    "high energy",
    "neutrino",
    "lhc",
    "atlas",
    "cms",
    "cern",
    "cosmology",
    "astrophysics",
    "theoretical physics",
    "phenomenology",
    "machine learning"
]

headers = {
    "User-Agent": "Mozilla/5.0"
}


# 🔹 requête robuste avec retry
def safe_request(url, params=None):
    for i in range(3):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=20)
            return r
        except requests.exceptions.RequestException as e:
            print(f"Retry {i+1} erreur:", e)
            time.sleep(2)
    return None


# 🔹 récupération description
def get_description(url):
    r = safe_request(url)

    if r is None:
        return ""

    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text("\n", strip=True)

    return text[:5000]


# 🔹 filtrage intelligent
def is_relevant(title, description):
    full_text = (title + " " + description).lower()
    return any(keyword in full_text for keyword in FILTER_KEYWORDS)


# 🔹 fonction principale
def get_offers():
    offers = []
    seen_links = set()

    for keyword in SEARCH_KEYWORDS:
        print("\nRecherche:", keyword)

        url = f"{BASE_URL}/jobs/search"
        params = {"keywords": keyword}

        r = safe_request(url, params=params)

        if r is None:
            print("Échec requête Euraxess")
            continue

        print("Status code:", r.status_code)
        print("URL finale:", r.url)

        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.find_all("a", href=True)

        for link_tag in links:
            title = link_tag.get_text(" ", strip=True)
            href = link_tag["href"]

            # ✅ garder uniquement les vraies offres (/jobs/123456)
            if not re.match(r"^/jobs/\d+$", href):
                continue

            link = BASE_URL + href

            if link in seen_links:
                continue

            seen_links.add(link)

            print("Offre trouvée:", title)

            description = get_description(link)

            if is_relevant(title, description):
                print("  -> retenue")

                offers.append({
                    "title": title,
                    "link": link,
                    "description": description
                })

            else:
                print("  -> ignorée")

            time.sleep(1)

            if len(offers) >= 5:
                print("Nombre d'offres retenues:", len(offers))
                return offers

    print("Nombre d'offres retenues:", len(offers))
    return offers