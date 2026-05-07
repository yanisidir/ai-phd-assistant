import asyncio
import html
import json
import re
from datetime import date, datetime
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://inspirehep.net"
WEB_SEARCH_URL = "https://inspirehep.net/jobs?q={query}"
API_SEARCH_URL = "https://inspirehep.net/api/jobs?q={query}&size={size}&sort=mostrecent&status=open"

KEEP_KEYWORDS = [
    "phd",
    "doctoral",
    "doctorate",
    "predoctoral",
    "pre-doctoral",
]

EXCLUDE_KEYWORDS = [
    "postdoc",
    "postdoctoral",
    "post doctoral",
    "professor",
    "faculty",
    "group leader",
]


def _clean_text(value):
    if value is None:
        return ""
    return " ".join(html.unescape(str(value)).split())


def _clean_html_text(value):
    if value is None:
        return ""
    text = BeautifulSoup(str(value), "html.parser").get_text(" ")
    return _clean_text(text)


def _markdown_from_result(result):
    markdown = getattr(result, "markdown", "")
    if isinstance(markdown, str):
        return markdown
    return (
        getattr(markdown, "fit_markdown", None)
        or getattr(markdown, "raw_markdown", None)
        or str(markdown or "")
    )


def _html_from_result(result):
    return getattr(result, "html", "") or ""


def _match_keywords(title, description=""):
    text = f"{title} {description}".lower()
    keep = [keyword for keyword in KEEP_KEYWORDS if keyword in text]
    exclude = [keyword for keyword in EXCLUDE_KEYWORDS if keyword in text]
    return keep, exclude


def _debug_candidates(label, offers):
    print(f"[DEBUG] {label}: {len(offers)} hits bruts avant filtrage")
    for index, offer in enumerate(offers[:5], start=1):
        keep, exclude = _match_keywords(offer.get("title", ""), offer.get("description", ""))
        print(
            f"[DEBUG] brut #{index}: {offer.get('title', 'No title')} | "
            f"keep={keep or '-'} | exclude={exclude or '-'} | "
            f"link={offer.get('link', '')}"
        )


def _relaxed_filter(offers, max_offers):
    accepted = []
    fallback = []
    seen_links = set()

    for offer in offers:
        link = offer.get("link") or offer.get("title")
        if not link or link in seen_links:
            print(f"[DEBUG] rejet: {offer.get('title', 'No title')} | raison=doublon ou lien vide")
            continue
        seen_links.add(link)

        if _is_deadline_expired(offer):
            print(
                f"[DEBUG] rejet deadline expiree: {offer.get('title')} | "
                f"deadline={offer.get('deadline', '')}"
            )
            continue

        if not offer.get("deadline") and _seems_closed_without_deadline(offer):
            print(f"[DEBUG] rejet sans deadline: {offer.get('title')} | raison=semble fermee")
            continue

        keep, exclude = _match_keywords(offer.get("title", ""), offer.get("description", ""))
        if exclude:
            print(f"[DEBUG] rejet filtre: {offer.get('title')} | raison=exclude {exclude}")
            continue

        if keep:
            print(f"[DEBUG] garde: {offer.get('title')} | raison=keep {keep}")
            accepted.append(offer)
        else:
            print(f"[DEBUG] rejet filtre: {offer.get('title')} | raison=pas PhD/doctoral/predoctoral")
            fallback.append(offer)

    if len(accepted) < max_offers and fallback:
        print("[DEBUG] Filtrage relache: ajout de resultats bruts pour atteindre max_offers.")

    return (accepted + fallback)[:max_offers]


def _absolute_url(value):
    return urljoin(BASE_URL, value or "")


def _first_title(metadata):
    position = _clean_text(metadata.get("position"))
    if position:
        return position

    titles = metadata.get("titles") or []
    if titles:
        return _clean_text(titles[0].get("title")) or "No title"

    return _clean_text(metadata.get("title")) or "No title"


def _first_external_link(hit, metadata):
    urls = metadata.get("urls") or []
    for item in urls:
        value = item.get("value")
        if value:
            return value

    links = hit.get("links") or {}
    if links.get("self"):
        return links["self"]
    if links.get("json"):
        return links["json"].replace("/api/", "/").replace("?format=json", "")

    control_number = metadata.get("control_number")
    if control_number:
        return f"{BASE_URL}/jobs/{control_number}"

    return ""


def _extract_deadline(metadata, description):
    deadline = metadata.get("deadline_date") or metadata.get("deadline")
    if deadline:
        return _clean_text(deadline)

    match = re.search(
        r"(?:deadline|closing date|apply by)[:\s-]+([^.;\n]+)",
        description,
        flags=re.IGNORECASE,
    )
    return _clean_text(match.group(1)) if match else ""


def _parse_deadline_date(deadline):
    value = _clean_text(deadline)
    if not value:
        return None

    value = re.sub(r"(st|nd|rd|th)\b", "", value, flags=re.IGNORECASE)
    value = value.replace(",", " ")
    value = re.sub(r"\s+", " ", value).strip()

    candidates = [value]
    iso_match = re.search(r"\b\d{4}-\d{2}-\d{2}\b", value)
    if iso_match:
        candidates.append(iso_match.group(0))

    numeric_match = re.search(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b", value)
    if numeric_match:
        candidates.append(numeric_match.group(0))

    text_match = re.search(r"\b\d{1,2} [A-Za-z]+ \d{4}\b", value)
    if text_match:
        candidates.append(text_match.group(0))

    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d/%m/%y",
        "%d.%m.%Y",
        "%d.%m.%y",
        "%d-%m-%Y",
        "%d %B %Y",
        "%d %b %Y",
        "%B %d %Y",
        "%b %d %Y",
    ]

    for candidate in candidates:
        for fmt in formats:
            try:
                return datetime.strptime(candidate, fmt).date()
            except ValueError:
                pass

    return None


def _seems_closed_without_deadline(offer):
    status = offer.get("status", "").lower()
    text = f"{offer.get('title', '')} {offer.get('description', '')}".lower()
    closed_markers = ["closed", "expired", "deadline passed", "applications closed"]
    return status in {"closed", "expired", "deleted"} or any(marker in text for marker in closed_markers)


def _is_deadline_expired(offer):
    deadline = offer.get("deadline", "")
    parsed_deadline = _parse_deadline_date(deadline)
    if parsed_deadline is None:
        return False
    return parsed_deadline < date.today()


def _extract_location(metadata):
    for key in ("locations", "location", "addresses"):
        value = metadata.get(key)
        if isinstance(value, list) and value:
            parts = []
            for item in value:
                if isinstance(item, dict):
                    parts.extend(str(v) for v in item.values() if v)
                else:
                    parts.append(str(item))
            return _clean_text(", ".join(parts))
        if isinstance(value, str):
            return _clean_text(value)
    return ""


def _extract_laboratory(metadata):
    for key in ("institutions", "institution", "experiments"):
        value = metadata.get(key)
        if isinstance(value, list) and value:
            names = []
            for item in value:
                if isinstance(item, dict):
                    names.append(item.get("value") or item.get("name") or item.get("curated_relation"))
                else:
                    names.append(str(item))
            return _clean_text(", ".join(name for name in names if name))
        if isinstance(value, str):
            return _clean_text(value)
    return ""


def _offer_from_api_hit(hit):
    metadata = hit.get("metadata", {})
    title = _first_title(metadata)
    description = _clean_html_text(metadata.get("description"))
    link = _first_external_link(hit, metadata)

    return {
        "title": title,
        "link": link,
        "description": description,
        "laboratory": _extract_laboratory(metadata),
        "location": _extract_location(metadata),
        "deadline": _extract_deadline(metadata, description),
        "contact": _clean_text(metadata.get("contact_email") or metadata.get("contact")),
        "source": "InspireHEP / Crawl4AI",
        "status": _clean_text(metadata.get("status")),
    }


def _extract_json_payload(text):
    text = html.unescape(text or "").strip()

    if text.startswith("{"):
        return json.loads(text)

    match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
    if match:
        return json.loads(match.group(1))

    raise ValueError("Aucun JSON InspireHEP exploitable trouve dans la page crawlee.")


def _extract_raw_offers_from_api_payload(payload):
    hits = payload.get("hits", {}).get("hits", [])
    print(f"[DEBUG] InspireHEP API requests: {len(hits)} hits API")
    return [_offer_from_api_hit(hit) for hit in hits]


def _fetch_api_offers(query, max_offers):
    encoded_query = quote_plus(query)
    api_url = API_SEARCH_URL.format(query=encoded_query, size=max(max_offers * 8, 40))
    print(f"[DEBUG] InspireHEP API requests URL: {api_url}")

    response = requests.get(api_url, timeout=20)
    response.raise_for_status()
    payload = response.json()

    raw_offers = _extract_raw_offers_from_api_payload(payload)
    for offer in raw_offers:
        print(f"[DEBUG] description nettoyee InspireHEP: {len(offer.get('description', ''))} chars | {offer.get('title')}")
    _debug_candidates("InspireHEP API requests", raw_offers)
    return _relaxed_filter(raw_offers, max_offers)


def _extract_raw_offers_from_markdown(markdown):
    offers = []
    seen_links = set()

    for title, href in re.findall(r"\[([^\]]{8,180})\]\(([^)]+)\)", markdown or ""):
        title = _clean_text(title)
        link = _absolute_url(href)

        if "/jobs/" not in link and "/record/" not in link:
            continue
        if link in seen_links:
            continue

        seen_links.add(link)
        offers.append({
            "title": title,
            "link": link,
            "description": title,
            "laboratory": "",
            "location": "",
            "deadline": "",
            "contact": "",
            "source": "InspireHEP / Crawl4AI",
        })

    return offers


async def get_offers_async(query="phd", max_offers=5):
    try:
        offers = _fetch_api_offers(query, max_offers)
        if offers:
            return offers
        print("[DEBUG] InspireHEP API requests retourne 0 offre, fallback Crawl4AI web.")
    except requests.RequestException as exc:
        print(f"[DEBUG] InspireHEP API requests echoue: {exc}")
    except ValueError as exc:
        print(f"[DEBUG] InspireHEP API JSON requests non exploitable: {exc}")

    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
    except ImportError as exc:
        raise RuntimeError(
            "Crawl4AI n est pas installe. Lance: pip install crawl4ai && crawl4ai-setup"
        ) from exc

    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=45000,
    )

    encoded_query = quote_plus(query)
    web_url = WEB_SEARCH_URL.format(query=encoded_query)

    async with AsyncWebCrawler(config=browser_config) as crawler:
        web_result = await crawler.arun(url=web_url, config=run_config)
        if not getattr(web_result, "success", False):
            error = getattr(web_result, "error_message", "Erreur inconnue")
            raise RuntimeError(f"Crawl InspireHEP echoue: {error}")

        raw_offers = _extract_raw_offers_from_markdown(_markdown_from_result(web_result))
        _debug_candidates("InspireHEP web Crawl4AI", raw_offers)
        return _relaxed_filter(raw_offers, max_offers)


def get_offers(max_offers=5, query="phd"):
    return asyncio.run(get_offers_async(query=query, max_offers=max_offers))


if __name__ == "__main__":
    offers = get_offers()
    print(json.dumps(offers, ensure_ascii=False, indent=2))
