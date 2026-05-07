import requests
from bs4 import BeautifulSoup


def clean_html(raw_html):
    soup = BeautifulSoup(raw_html, "html.parser")
    return soup.get_text(" ", strip=True)


def guess_title(description, link):
    text = clean_html(description)

    # Prend le début de la description comme titre provisoire
    if len(text) > 120:
        return text[:120] + "..."

    if text:
        return text

    return link


def get_offers():
    url = "https://inspirehep.net/api/jobs"

    params = {
        "q": "phd",
        "size": 20
    }

    r = requests.get(url, params=params, timeout=20)
    data = r.json()

    offers = []
    seen_links = set()

    for hit in data["hits"]["hits"]:
        metadata = hit.get("metadata", {})

        description_html = metadata.get("description", "")
        description = clean_html(description_html)

        link = ""
        if "urls" in metadata and len(metadata["urls"]) > 0:
            link = metadata["urls"][0].get("value", "")

        if not link:
            continue

        if link in seen_links:
            continue

        seen_links.add(link)

        title = "No title"

        if "titles" in metadata and len(metadata["titles"]) > 0:
            title = metadata["titles"][0].get("title", "No title")

        if title == "No title":
            title = guess_title(description_html, link)

        text = (title + " " + description).lower()

        if not is_phd_offer(title, description):
            continue    

        offers.append({
            "title": title,
            "link": link,
            "description": description
        })

        if len(offers) >= 5:
            break

    print("Nombre d'offres InspireHEP:", len(offers))
    return offers


def is_phd_offer(title, description):
    text = (title + " " + description).lower()

    required_words = ["phd", "doctoral", "predoctoral"]
    forbidden_words = ["postdoc", "postdoctoral", "professor", "group leader", "faculty"]

    has_required = any(word in text for word in required_words)
    has_forbidden = any(word in text for word in forbidden_words)

    return has_required and not has_forbidden