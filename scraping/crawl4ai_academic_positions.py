import asyncio
import json
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup


BASE_URL = "https://academicpositions.com"
SEARCH_URL = "https://academicpositions.com/jobs/position/phd/field/physics"

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

EXCLUDED_JOB_PATHS = (
    "/jobs/position/",
    "/jobs/field/",
    "/jobs/country/",
    "/jobs/employer/",
    "/jobs/search",
)


def _clean_text(value):
    if value is None:
        return ""
    return " ".join(str(value).split())


def _clean_offer_description(text):
    text = _clean_text(text)
    noise_markers = [
        "RegionSite languageJob languages",
        "Choose your region",
        "Select the region that best fits your location or preferences.",
    ]

    for marker in noise_markers:
        if marker in text:
            text = text.split(marker, 1)[-1]

    start_patterns = [
        r"Job details\s+",
        r"About the position\s+",
        r"Project description\s+",
        r"Job description\s+",
        r"The position\s+",
    ]
    for pattern in start_patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            text = text[match.start():]
            break

    end_markers = [
        "#### Jobs from this employer",
        "Showing jobs in English",
        "Share this job",
    ]
    for marker in end_markers:
        if marker in text:
            text = text.split(marker, 1)[0]

    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[\s*\]\([^)]*\)", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = text.replace("\\(", "(").replace("\\)", ")")
    text = re.sub(r"\bApply now\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"^Job details\s+", "", text, flags=re.IGNORECASE)
    return _clean_text(text)[:5000]


def _markdown_from_result(result):
    markdown = getattr(result, "markdown", "")
    if isinstance(markdown, str):
        return markdown
    return (
        getattr(markdown, "fit_markdown", None)
        or getattr(markdown, "raw_markdown", None)
        or str(markdown or "")
    )


def _is_job_link(href):
    if not href:
        return False

    if href.startswith("mailto:") or href.startswith("tel:") or href.startswith("#"):
        return False

    path = href.split("?", 1)[0]
    if any(excluded in path for excluded in EXCLUDED_JOB_PATHS):
        return False

    return "/jobs/" in path or "/job/" in path or "/ad/" in path


def _match_keywords(text):
    text = text.lower()
    keep = [keyword for keyword in KEEP_KEYWORDS if keyword in text]
    exclude = [keyword for keyword in EXCLUDE_KEYWORDS if keyword in text]
    return keep, exclude


def _debug_candidates(label, offers):
    print(f"[DEBUG] {label}: {len(offers)} hits bruts avant filtrage")
    for index, offer in enumerate(offers[:5], start=1):
        keep, exclude = _match_keywords(f"{offer.get('title', '')} {offer.get('description', '')}")
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

        keep, exclude = _match_keywords(f"{offer.get('title', '')} {offer.get('description', '')}")
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


def _extract_field(patterns, text, default=""):
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return _clean_text(match.group(1))
    return default


def _offer_from_anchor(anchor, base_url):
    title = _clean_text(anchor.get_text(" ", strip=True))
    link = urljoin(base_url, anchor.get("href", ""))

    container = anchor.find_parent(["article", "li", "section", "div"])
    card_text = _clean_text(container.get_text(" ", strip=True) if container else title)

    laboratory = _extract_field(
        [r"(?:University|Institute|Department|Faculty|Laboratory)[:\s-]+([^|,;]+)"],
        card_text,
    )
    location = _extract_field(
        [r"Location[:\s-]+([^|;]+)", r"Country[:\s-]+([^|;]+)"],
        card_text,
    )
    deadline = _extract_field(
        [r"Deadline[:\s-]+([^|;]+)", r"Apply by[:\s-]+([^|;]+)", r"Closing date[:\s-]+([^|;]+)"],
        card_text,
    )

    return {
        "title": title,
        "link": link,
        "description": card_text,
        "laboratory": laboratory,
        "location": location,
        "deadline": deadline,
        "contact": "",
        "source": "Academic Positions / Crawl4AI",
    }


def _extract_raw_offers_from_html(html, base_url=BASE_URL):
    soup = BeautifulSoup(html or "", "html.parser")
    offers = []
    seen_links = set()

    for anchor in soup.find_all("a", href=True):
        href = anchor.get("href", "")
        if not _is_job_link(href):
            continue

        offer = _offer_from_anchor(anchor, base_url)
        if not offer["title"] or len(offer["title"]) < 8:
            continue

        if offer["link"] in seen_links:
            continue

        seen_links.add(offer["link"])
        offers.append(offer)

    return offers


def _extract_raw_offers_from_markdown(markdown):
    offers = []
    seen_links = set()
    raw_links = re.findall(r"\[([^\]]{8,180})\]\(([^)]+)\)", markdown or "")
    print(f"[DEBUG] Academic Positions markdown links bruts: {len(raw_links)}")

    for index, (title, href) in enumerate(raw_links[:5], start=1):
        print(f"[DEBUG] markdown link #{index}: {_clean_text(title)} | href={href}")

    for title, href in raw_links:
        title = _clean_text(title)
        link = urljoin(BASE_URL, href)

        looks_like_offer = _is_job_link(href) or any(keyword in title.lower() for keyword in KEEP_KEYWORDS)
        if not looks_like_offer:
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
            "source": "Academic Positions / Crawl4AI",
        })

    return offers


def _merge_offer_details(offer, markdown):
    text = _clean_offer_description(markdown)
    if text:
        offer["description"] = text
        print(
            f"[DEBUG] description nettoyee Academic Positions: "
            f"{len(offer.get('description', ''))} chars | {offer.get('title')}"
        )

    email_match = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, flags=re.IGNORECASE)
    if email_match:
        offer["contact"] = email_match.group(0)

    if not offer.get("deadline"):
        offer["deadline"] = _extract_field(
            [r"Deadline[:\s-]+([^.|;]+)", r"Apply by[:\s-]+([^.|;]+)", r"Closing date[:\s-]+([^.|;]+)"],
            text,
        )

    return offer


async def get_offers_async(search_url=SEARCH_URL, max_offers=5, enrich_details=True):
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig
    except ImportError as exc:
        raise RuntimeError(
            "Crawl4AI n est pas installe. Ajoute crawl4ai aux dependances puis lance: "
            "pip install crawl4ai && crawl4ai-setup"
        ) from exc

    browser_config = BrowserConfig(headless=True)
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=45000,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=search_url, config=run_config)

        if not getattr(result, "success", False):
            error = getattr(result, "error_message", "Erreur inconnue")
            raise RuntimeError(f"Crawl Academic Positions echoue: {error}")

        html = getattr(result, "html", "")
        markdown = _markdown_from_result(result)
        raw_offers = _extract_raw_offers_from_html(html, search_url)

        if not raw_offers:
            print(f"[DEBUG] Academic Positions HTML length: {len(html)}")
            print(f"[DEBUG] Academic Positions markdown length: {len(markdown)}")
            raw_offers = _extract_raw_offers_from_markdown(markdown)

        _debug_candidates("Academic Positions", raw_offers)
        offers = _relaxed_filter(raw_offers, max_offers)

        if enrich_details:
            enriched = []
            for offer in offers:
                detail = await crawler.arun(url=offer["link"], config=run_config)
                if getattr(detail, "success", False):
                    offer = _merge_offer_details(offer, _markdown_from_result(detail))
                enriched.append(offer)
            offers = enriched

    return offers


def get_offers(max_offers=5, enrich_details=True):
    return asyncio.run(get_offers_async(max_offers=max_offers, enrich_details=enrich_details))


if __name__ == "__main__":
    offers = get_offers()
    print(json.dumps(offers, ensure_ascii=False, indent=2))
